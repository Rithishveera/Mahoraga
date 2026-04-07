from datetime import datetime
from uuid import uuid4

from core.config import OLLAMA_MODEL, USE_LLM_REPORTS


class ReportGenerator:
    def generate(
        self,
        event: dict,
        risk_score: float,
        recommended_patch: str,
    ) -> dict:
        if USE_LLM_REPORTS:
            summary = self._llm_summary(event, risk_score, recommended_patch)
        else:
            summary = self._template_summary(event, risk_score, recommended_patch)

        return {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "title": f"Threat detected on {event.get('target_node', 'unknown')}",
            "summary": summary,
            "affected_node": event.get("target_node", "unknown"),
            "vuln_class": event.get("vuln_class", "unknown"),
            "risk_score": round(risk_score, 1),
            "recommended_action": recommended_patch,
            "estimated_risk_reduction": round(risk_score * 0.4, 1),
            "requires_approval": True,
            "status": "pending",
        }

    def _llm_summary(
        self, event: dict, risk_score: float, patch: str
    ) -> str:
        try:
            import ollama

            prompt = (
                f"You are Mahoraga, an adaptive cyber-immune AI system.\n"
                f"Write a 2-sentence plain-language incident report.\n"
                f"Sentence 1: what attack was detected and on which node.\n"
                f"Sentence 2: what you recommend doing and why.\n"
                f"Keep it under 60 words total. No headers. No bullet points. Plain text only.\n\n"
                f"Data:\n"
                f"- Node: {event.get('target_node')}\n"
                f"- Attack: {event.get('action')}\n"
                f"- Vulnerability: {event.get('vuln_class')}\n"
                f"- Risk score: {risk_score:.0f}/100\n"
                f"- Recommended action: {patch}"
            )
            response = ollama.chat(
                model=OLLAMA_MODEL,
                messages=[{"role": "user", "content": prompt}],
            )
            return response["message"]["content"].strip()
        except Exception:
            return self._template_summary(event, risk_score, patch)

    def _template_summary(
        self, event: dict, risk_score: float, patch: str
    ) -> str:
        return (
            f"Red agent executed {event.get('action', 'unknown attack')} on "
            f"{event.get('target_node', 'unknown')} exploiting "
            f"{event.get('vuln_class', 'unknown vulnerability')} "
            f"(risk score: {risk_score:.0f}/100). "
            f"Recommended action: {patch} — approve to harden this vulnerability class."
        )


reporter = ReportGenerator()
