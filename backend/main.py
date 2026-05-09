"""
backend/main.py — Mahoraga entry point (patched)

Summary of all wired fixes:
  1. CORS: reads ALLOWED_ORIGINS from env — no hardcoded "*"
  2. Red loop: real action-feature profiles passed to CompositeScorer (not a static dict)
  3. Red breach prob: windowed (last-20-ep rate) via red_agent.get_windowed_breach_prob()
  4. Topology restore: node patch state loaded from SQLite before Red Agent starts
  5. Triggered keys: loaded from SQLite on startup (restart-safe deduplication)
  6. threading.Event used for is_running (handled inside RedAgent itself)
  7. DB WAL + migrations run via run_migrations() on startup
"""
from __future__ import annotations

import asyncio
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
from core.config import ALLOWED_ORIGINS, BASELINE_CSV, RED_TRAINING_STEPS
from core.db import run_migrations
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

import os

_loop: asyncio.AbstractEventLoop | None = None

# ── Per-action feature profiles (FIX: anomaly engine now sees real signals) ──
_ACTION_FEATURE_MAP: dict[str, dict] = {
    "port_scan_web_server": {
        "entity_id": "red_agent", "login_hour": 2,
        "api_calls_per_minute": 60.0, "data_volume_mb": 0.5,
        "endpoints_accessed": 8, "failed_auth_count": 0, "session_duration_min": 2.0,
    },
    "port_scan_api_service": {
        "entity_id": "red_agent", "login_hour": 3,
        "api_calls_per_minute": 55.0, "data_volume_mb": 0.5,
        "endpoints_accessed": 7, "failed_auth_count": 0, "session_duration_min": 2.0,
    },
    "try_default_creds_admin": {
        "entity_id": "red_agent", "login_hour": 1,
        "api_calls_per_minute": 10.0, "data_volume_mb": 0.1,
        "endpoints_accessed": 1, "failed_auth_count": 8, "session_duration_min": 1.0,
    },
    "inject_payload_web": {
        "entity_id": "red_agent", "login_hour": 2,
        "api_calls_per_minute": 90.0, "data_volume_mb": 2.0,
        "endpoints_accessed": 5, "failed_auth_count": 2, "session_duration_min": 3.0,
    },
    "probe_database": {
        "entity_id": "red_agent", "login_hour": 3,
        "api_calls_per_minute": 40.0, "data_volume_mb": 45.0,
        "endpoints_accessed": 2, "failed_auth_count": 1, "session_duration_min": 5.0,
    },
    "exploit_unprotected_endpoint": {
        "entity_id": "red_agent", "login_hour": 22,
        "api_calls_per_minute": 75.0, "data_volume_mb": 10.0,
        "endpoints_accessed": 9, "failed_auth_count": 0, "session_duration_min": 4.0,
    },
    "attempt_privilege_escalation": {
        "entity_id": "red_agent", "login_hour": 0,
        "api_calls_per_minute": 20.0, "data_volume_mb": 0.3,
        "endpoints_accessed": 3, "failed_auth_count": 5, "session_duration_min": 2.0,
    },
    "lateral_move_to_internal": {
        "entity_id": "red_agent", "login_hour": 3,
        "api_calls_per_minute": 35.0, "data_volume_mb": 38.0,
        "endpoints_accessed": 6, "failed_auth_count": 1, "session_duration_min": 8.0,
    },
}

_DEFAULT_FEATURE = {
    "entity_id": "red_agent", "login_hour": 10,
    "api_calls_per_minute": 12.0, "data_volume_mb": 5.0,
    "endpoints_accessed": 3, "failed_auth_count": 0, "session_duration_min": 45.0,
}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    global _loop
    _loop = asyncio.get_event_loop()

    # FIX: WAL + migrations (replaces raw CREATE TABLE IF NOT EXISTS)
    run_migrations()
    init_db()
    threat_memory.init_db()
    os.makedirs("data/models", exist_ok=True)

    # FIX: restore triggered keys from DB before Red Agent can fire
    trigger.load_from_db()

    # FIX: restore node patch state from DB so reward signal is coherent post-restart
    saved_patches = threat_memory.load_node_patches()
    for node_name, vuln_list in saved_patches.items():
        for vuln in vuln_list:
            topology.mark_patched(node_name, vuln)

    # FIX: clear queue via lock-safe proxy (not direct list.clear())
    approval_queue.queue.clear()

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
            info["action_name"], info["node"], info["vuln_class"], info["success"]
        )

        if trigger.should_trigger(
            risk_engine.get(), scorer.current_if_score, info["success"],
            vuln_class=info["vuln_class"], target_node=info["node"],
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
                    sio.emit("approval_required", report), _loop
                )

    red_agent.set_broadcast(broadcast_sync)

    def red_loop() -> None:
        # FIX: uses threading.Event.is_set() via the is_running property shim
        while red_agent.is_running:
            info = red_agent.run_episode()
            if not info:
                time.sleep(3)
                continue

            # FIX: real per-action feature profile (not a static dict)
            action_name = red_agent.current_action
            feature_event = _ACTION_FEATURE_MAP.get(action_name, _DEFAULT_FEATURE).copy()
            feature_event["entity_id"] = "red_agent"

            # FIX: windowed breach prob (last-20-ep rate), not episode_count/100
            red_breach_prob = red_agent.get_windowed_breach_prob()
            scorer.score(feature_event, red_breach_prob)
            time.sleep(3)

    red_agent.is_running = True   # sets threading.Event via property shim
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
            pending = approval_queue.get_pending()
            if pending:
                for item in pending[:5]:
                    await sio.emit("approval_required", item)
            tick += 1

    asyncio.create_task(periodic_broadcast())
    yield
    red_agent.is_running = False  # clears threading.Event via property shim


app = FastAPI(title="Mahoraga", version="1.1.0", lifespan=lifespan)

# FIX: ALLOWED_ORIGINS from env config — never hardcoded "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
sio_app = socketio.ASGIApp(sio, app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:sio_app", host="0.0.0.0", port=8000, reload=False)
