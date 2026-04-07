from datetime import datetime

import socketio

from core.risk_score import risk_engine
from agents.red_agent import red_agent
from agents.blue_agent import blue_agent

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
)


async def emit_event(event_dict: dict) -> None:
    await sio.emit("event", event_dict)


async def emit_risk_score() -> None:
    await sio.emit(
        "risk_score",
        {
            "score": risk_engine.get(),
            "timestamp": datetime.utcnow().isoformat(),
            "history": risk_engine.get_history(),
        },
    )


async def emit_agent_status() -> None:
    await sio.emit(
        "agent_status",
        {
            "red": red_agent.get_status(),
            "blue": blue_agent.get_status(),
        },
    )


async def emit_network_state(topology_state: dict) -> None:
    await sio.emit(
        "network_state",
        {
            "nodes": topology_state,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


async def emit_approval(report: dict) -> None:
    await sio.emit("approval_required", report)


@sio.event
async def connect(sid: str, environ: dict) -> None:
    print(f"[Mahoraga] Client connected: {sid}")


@sio.event
async def disconnect(sid: str) -> None:
    print(f"[Mahoraga] Client disconnected: {sid}")
