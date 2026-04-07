import threading
import time
from datetime import datetime

from fastapi import APIRouter

from agents.blue_agent import blue_agent
from agents.red_agent import red_agent
from api.schemas import (
    AgentStatusResponse,
    ApproveRequest,
    HealthResponse,
    OverrideRequest,
)
from core.config import APP_NAME, APP_VERSION
from core.events import get_recent_events
from core.risk_score import risk_engine
from detection.composite_scorer import scorer
from memory.export import exporter
from memory.threat_store import threat_memory
from network.governor import governor
from network.topology import topology
from response.approval_queue import approval_queue
from response.snapshot import snapshotter

router = APIRouter()


@router.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        app=APP_NAME,
        version=APP_VERSION,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/api/network/state")
async def network_state() -> dict:
    return {
        "nodes": topology.get_state(),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/api/network/reset")
async def network_reset() -> dict:
    topology.reset_all()
    risk_engine.reset()
    return {"reset": True, "timestamp": datetime.utcnow().isoformat()}


@router.get("/api/risk/current")
async def risk_current() -> dict:
    return scorer.get_current()


@router.get("/api/events/recent")
async def events_recent(n: int = 50) -> list:
    return get_recent_events(n)


@router.get("/api/agents/status", response_model=AgentStatusResponse)
async def agents_status() -> AgentStatusResponse:
    return AgentStatusResponse(
        red=red_agent.get_status(),
        blue=blue_agent.get_status(),
        governor={
            "override_count": governor.override_count,
            "overrides": governor.get_overrides(),
        },
    )


@router.post("/api/agents/red/start")
async def red_start() -> dict:
    red_agent.is_running = True
    return {"started": True}


@router.post("/api/agents/red/stop")
async def red_stop() -> dict:
    red_agent.is_running = False
    return {"stopped": True}


@router.get("/api/memory/attacks")
async def memory_attacks() -> list:
    return threat_memory.get_all_attacks()


@router.get("/api/memory/patches")
async def memory_patches() -> list:
    return threat_memory.get_all_patches()


@router.get("/api/memory/stats")
async def memory_stats() -> dict:
    return threat_memory.get_stats()


@router.get("/api/memory/export")
async def memory_export() -> dict:
    return exporter.export()


@router.get("/api/approval/pending")
async def approval_pending() -> list:
    return approval_queue.get_pending()


@router.post("/api/approval/{report_id}/approve")
async def approve(report_id: str, body: ApproveRequest) -> dict:
    return approval_queue.approve(report_id)


@router.post("/api/approval/{report_id}/override")
async def override(report_id: str, body: OverrideRequest) -> dict:
    return approval_queue.override(report_id, body.reason)


@router.get("/api/anomaly/score")
async def anomaly_score() -> dict:
    return scorer.get_current()


@router.get("/api/snapshots")
async def snapshots() -> list:
    return snapshotter.get_all()


@router.get("/api/reports")
async def get_reports() -> list:
    from response.incident_reporter import get_all_reports
    return get_all_reports()
