"""
core/events.py — Event persistence.
Patch: uses core.db for WAL + retry instead of raw sqlite3.connect().
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from uuid import uuid4

from core.db import execute, run_migrations


@dataclass
class Event:
    source: str
    target_node: str
    action: str
    outcome: str
    severity: str
    risk_delta: float = 0.0
    details: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


def init_db() -> None:
    run_migrations()


def save_event(event: Event) -> None:
    execute(
        "INSERT OR REPLACE INTO events VALUES (?,?,?,?,?,?,?,?,?)",
        (
            event.id, event.timestamp, event.source, event.target_node,
            event.action, event.outcome, event.severity,
            event.risk_delta, json.dumps(event.details),
        ),
    )


def get_recent_events(n: int = 50) -> list[dict]:
    rows = execute(
        "SELECT * FROM events ORDER BY timestamp DESC LIMIT ?", (n,)
    )
    return [
        {
            "id": r[0], "timestamp": r[1], "source": r[2],
            "target_node": r[3], "action": r[4], "outcome": r[5],
            "severity": r[6], "risk_delta": r[7],
            "details": json.loads(r[8]),
        }
        for r in rows
    ]
