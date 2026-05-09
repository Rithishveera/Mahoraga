"""
response/snapshot.py
Patch: Each snapshot stores only the last 20 attacks and last 20 patches
       (not all records) — keeps snapshot memory O(1) regardless of session length.
"""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from agents.blue_agent import blue_agent
from core.risk_score import risk_engine
from memory.threat_store import threat_memory
from network.topology import topology


class ForensicSnapshot:
    def __init__(self) -> None:
        self.snapshots: list[dict] = []

    def take(self, trigger_event: dict, risk_score: float) -> dict:
        # FIX: cap inner lists at 20 items — not all records
        snap = {
            "id":                  str(uuid4()),
            "timestamp":           datetime.utcnow().isoformat(),
            "trigger_event":       trigger_event,
            "risk_score_at_trigger": risk_score,
            "network_state":       topology.get_state(),
            "active_patches":      blue_agent.patches_applied[-20:],
            "recent_attacks":      threat_memory.get_all_attacks()[-20:],
            "risk_history":        risk_engine.get_history(),
        }
        self.snapshots.append(snap)
        return snap

    def get_all(self) -> list[dict]:
        return self.snapshots[-20:]


snapshotter = ForensicSnapshot()
