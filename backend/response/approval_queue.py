"""
response/approval_queue.py
Patches:
  - Plain list replaced by collections.deque(maxlen=50) — bounded, O(1) appends
  - threading.Lock around all queue reads/writes — eliminates concurrent-modification race
  - queue.clear() is now lock-protected
"""
from __future__ import annotations

import threading
from collections import deque

from agents.blue_agent import blue_agent
from core.risk_score import risk_engine
from memory.threat_store import threat_memory


class ApprovalQueue:
    def __init__(self) -> None:
        self._queue: deque[dict] = deque(maxlen=50)  # FIX: bounded deque
        self._lock  = threading.Lock()               # FIX: thread-safe access
        self.history: list[dict] = []

    # kept for backwards compat (main.py does approval_queue.queue.clear())
    class _QueueProxy:
        """Thin proxy that routes .clear() through the lock."""
        def __init__(self, owner: "ApprovalQueue") -> None:
            self._owner = owner
        def clear(self) -> None:
            with self._owner._lock:
                self._owner._queue.clear()

    @property
    def queue(self) -> "_QueueProxy":
        return self._QueueProxy(self)

    def add(self, report: dict) -> None:
        with self._lock:
            self._queue.append(report)

    def get_pending(self) -> list[dict]:
        with self._lock:
            return list(self._queue)

    def approve(self, report_id: str) -> dict:
        from response.incident_reporter import create_incident_report

        with self._lock:
            report = next((r for r in self._queue if r["id"] == report_id), None)
            if not report:
                return {"error": "not found"}
            report["status"] = "approved"

        risk_before = report.get("risk_score", risk_engine.get())
        result = blue_agent.respond(report["vuln_class"], report["affected_node"])
        threat_memory.record_patch(
            report["vuln_class"],
            report["recommended_action"],
            report["affected_node"],
        )
        risk_after = max(0.0, risk_before - report.get("estimated_risk_reduction", 10.0))

        create_incident_report(
            attack={
                "target_node": report["affected_node"],
                "action": report.get("title", "unknown"),
                "vuln_class": report["vuln_class"],
            },
            patch_result=result,
            risk_before=risk_before,
            risk_after=risk_after,
        )

        with self._lock:
            self._queue = deque(
                (r for r in self._queue if r["id"] != report_id), maxlen=50
            )
        self.history.append(report)
        return {"approved": True, "patch_result": result}

    def override(self, report_id: str, reason: str = "") -> dict:
        with self._lock:
            report = next((r for r in self._queue if r["id"] == report_id), None)
            if not report:
                return {"error": "not found"}
            report["status"] = "overridden"
            report["override_reason"] = reason
            self._queue = deque(
                (r for r in self._queue if r["id"] != report_id), maxlen=50
            )
        self.history.append(report)
        return {"overridden": True}

    def get_history(self) -> list[dict]:
        return self.history

    def _find(self, report_id: str) -> dict | None:
        with self._lock:
            return next((r for r in self._queue if r["id"] == report_id), None)


approval_queue = ApprovalQueue()
