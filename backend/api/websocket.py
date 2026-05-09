"""
api/websocket.py
Patches:
  - cors_allowed_origins reads from settings.ALLOWED_ORIGINS, not hardcoded "*"
  - connect handler validates an optional WS_TOKEN; disconnects unknown clients
    when WS_TOKEN env var is set (opt-in — safe default is open for local dev)
"""
from __future__ import annotations

import logging
import os
from datetime import datetime

import socketio

from core.config import ALLOWED_ORIGINS
from core.risk_score import risk_engine
from agents.red_agent import red_agent
from agents.blue_agent import blue_agent

log = logging.getLogger("mahoraga.ws")

# FIX: read allowed origins from config, not hardcoded "*"
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=ALLOWED_ORIGINS,
)

# Optional shared secret for WebSocket auth (set WS_TOKEN env var to enable)
_WS_TOKEN: str | None = os.getenv("WS_TOKEN")  # None = open (dev mode)


async def emit_event(event_dict: dict) -> None:
    await sio.emit("event", event_dict)


async def emit_risk_score() -> None:
    await sio.emit("risk_score", {
        "score":     risk_engine.get(),
        "timestamp": datetime.utcnow().isoformat(),
        "history":   risk_engine.get_history(),
    })


async def emit_agent_status() -> None:
    await sio.emit("agent_status", {
        "red":  red_agent.get_status(),
        "blue": blue_agent.get_status(),
    })


async def emit_network_state(topology_state: dict) -> None:
    await sio.emit("network_state", {
        "nodes":     topology_state,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def emit_approval(report: dict) -> None:
    await sio.emit("approval_required", report)


@sio.event
async def connect(sid: str, environ: dict, auth: dict | None = None) -> bool | None:
    # FIX: validate token when WS_TOKEN is set; silent pass-through in dev mode
    if _WS_TOKEN:
        provided = (auth or {}).get("token") or ""
        if provided != _WS_TOKEN:
            log.warning("WS auth rejected for sid=%s", sid)
            await sio.disconnect(sid)
            return False
    log.info("Client connected: %s", sid)


@sio.event
async def disconnect(sid: str) -> None:
    log.info("Client disconnected: %s", sid)
