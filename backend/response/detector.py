"""
response/detector.py
Patch: triggered_keys persisted to SQLite via threat_memory.
       On startup, historical keys are loaded so deduplication survives restarts.
"""
from __future__ import annotations

from core.config import RISK_THRESHOLD


class ResponseTrigger:
    def __init__(self) -> None:
        self.threshold = RISK_THRESHOLD
        self.triggered_count = 0
        self._triggered_keys: set[str] = set()

    def load_from_db(self) -> None:
        """Call once on startup — restores all historical triggered keys."""
        from memory.threat_store import threat_memory
        self._triggered_keys = threat_memory.load_triggered_keys()

    def should_trigger(
        self,
        risk_score: float,
        anomaly_score: float,
        red_breach: bool,
        vuln_class: str = "",
        target_node: str = "",
    ) -> bool:
        if not red_breach:
            return False
        key = f"{target_node}:{vuln_class}"
        if key in self._triggered_keys:
            return False
        # FIX: persist before adding to memory so restarts don't re-trigger
        from memory.threat_store import threat_memory
        threat_memory.save_triggered_key(key)
        self._triggered_keys.add(key)
        self.triggered_count += 1
        return True

    def reset(self) -> None:
        """In-memory reset only (used for dev resets, not production restarts)."""
        self._triggered_keys.clear()


trigger = ResponseTrigger()
