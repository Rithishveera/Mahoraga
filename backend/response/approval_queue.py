from agents.blue_agent import blue_agent
from core.risk_score import risk_engine
from memory.threat_store import threat_memory


class ApprovalQueue:
    def __init__(self) -> None:
        self.queue: list[dict] = []
        self.history: list[dict] = []

    def add(self, report: dict) -> None:
        self.queue.append(report)

    def approve(self, report_id: str) -> dict:
        from response.incident_reporter import create_incident_report

        report = self._find(report_id)
        if not report:
            return {"error": "not found"}

        risk_before = report.get("risk_score", risk_engine.get())
        report["status"] = "approved"

        result = blue_agent.respond(
            report["vuln_class"], report["affected_node"]
        )
        threat_memory.record_patch(
            report["vuln_class"],
            report["recommended_action"],
            report["affected_node"],
        )

        risk_after = max(0.0, risk_before - report.get("estimated_risk_reduction", 10.0))

        # Generate full incident report
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

        self.queue = [r for r in self.queue if r["id"] != report_id]
        self.history.append(report)
        return {"approved": True, "patch_result": result}

    def override(self, report_id: str, reason: str = "") -> dict:
        report = self._find(report_id)
        if not report:
            return {"error": "not found"}
        report["status"] = "overridden"
        report["override_reason"] = reason
        self.queue = [r for r in self.queue if r["id"] != report_id]
        self.history.append(report)
        return {"overridden": True}

    def get_pending(self) -> list[dict]:
        return self.queue

    def get_history(self) -> list[dict]:
        return self.history

    def _find(self, report_id: str) -> dict | None:
        return next((r for r in self.queue if r["id"] == report_id), None)


approval_queue = ApprovalQueue()
