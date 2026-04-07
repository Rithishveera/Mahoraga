import asyncio
import os
import threading
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import pandas as pd
import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agents.blue_agent import VULN_TO_PATCH, blue_agent
from agents.red_agent import red_agent
from api.routes import router
from api.websocket import emit_agent_status, emit_network_state, emit_risk_score, sio
from core.config import BASELINE_CSV, RED_TRAINING_STEPS
from core.events import Event, init_db, save_event
from core.risk_score import risk_engine
from detection.baseline_generator import generate_baseline
from detection.composite_scorer import scorer
from detection.isolation_forest import anomaly_detector
from memory.threat_store import threat_memory
from network.topology import topology
from response.approval_queue import approval_queue
from response.detector import trigger
from response.report_generator import reporter
from response.snapshot import snapshotter

_loop: asyncio.AbstractEventLoop | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    global _loop
    _loop = asyncio.get_event_loop()

    init_db()
    threat_memory.init_db()
    os.makedirs("data/models", exist_ok=True)

    # Clear any stale queue from previous runs
    approval_queue.queue.clear()
    trigger.reset()

    if not os.path.exists(BASELINE_CSV):
        df = generate_baseline(days=30)
    else:
        df = pd.read_csv(BASELINE_CSV)

    if not anomaly_detector.load():
        anomaly_detector.train(df)

    if not red_agent.load():
        red_agent.train(steps=RED_TRAINING_STEPS)

    def broadcast_sync(info: dict) -> None:
        event = Event(
            source="red_agent",
            target_node=info["node"],
            action=info["action_name"],
            outcome="success" if info["success"] else "failed",
            severity="high" if info["success"] else "low",
            risk_delta=5.0 if info["success"] else 0.0,
            details=info,
        )
        save_event(event)
        threat_memory.record_attack(
            info["action_name"],
            info["node"],
            info["vuln_class"],
            info["success"],
        )

        if trigger.should_trigger(
            risk_engine.get(),
            scorer.current_if_score,
            info["success"],
            vuln_class=info["vuln_class"],
            target_node=info["node"],
        ):
            report = reporter.generate(
                {
                    "target_node": info["node"],
                    "action": info["action_name"],
                    "vuln_class": info["vuln_class"],
                },
                risk_engine.get(),
                VULN_TO_PATCH.get(info["vuln_class"], "restrict_access"),
            )
            approval_queue.add(report)
            snapshotter.take(info, risk_engine.get())

            if _loop and _loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    sio.emit("approval_required", report),
                    _loop,
                )

    red_agent.set_broadcast(broadcast_sync)

    def red_loop() -> None:
        while red_agent.is_running:
            red_agent.run_episode()
            fake_event = {
                "entity_id": "user_001",
                "login_hour": 10,
                "login_ip": "known",
                "api_calls_per_minute": 12,
                "data_volume_mb": 5,
                "endpoints_accessed": 3,
                "failed_auth_count": 0,
                "session_duration_min": 45,
            }
            red_breach_prob = min(red_agent.episode_count / 100, 1.0)
            scorer.score(fake_event, red_breach_prob)
            time.sleep(3)

    red_agent.is_running = True
    thread = threading.Thread(target=red_loop, daemon=True)
    thread.start()

    async def periodic_broadcast() -> None:
        tick = 0
        while True:
            await asyncio.sleep(2)
            await emit_risk_score()
            await emit_agent_status()
            if tick % 3 == 0:
                await emit_network_state(topology.get_state())
            # Push pending approvals (max 5 shown)
            pending = approval_queue.get_pending()
            if pending:
                for item in pending[:5]:
                    await sio.emit("approval_required", item)
            tick += 1

    asyncio.create_task(periodic_broadcast())
    yield
    red_agent.is_running = False


app = FastAPI(title="Mahoraga", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
sio_app = socketio.ASGIApp(sio, app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:sio_app", host="0.0.0.0", port=8000, reload=False)
