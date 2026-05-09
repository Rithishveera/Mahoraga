"""
response/report_generator.py
Patches:
  - _sanitise() applied to all event fields before building LLM prompt
  - Ollama call wrapped in ThreadPoolExecutor with 8s timeout
"""
from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from datetime import datetime
from uuid import uuid4

from core.config import OLLAMA_MODEL, USE_LLM_REPORTS

log = logging.getLogger("mahoraga.report_gen")
_exec = ThreadPoolExecutor(max_workers=2, thread_name_prefix="rptgen")
_TIMEOUT = 8.0


def _sanitise(v: object) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-]", "", str(v))[:32]


class ReportGenerator:
    def generate(self, event: dict, risk_score: float, recommended_patch: str) -> dict:
        if USE_LLM_REPORTS:
            summary = self._llm_summary(event, risk_score, recommended_patch)
        else:
            summary = self._template_summary(event, risk_score, recommended_patch)

        return {
            "id":                   str(uuid4()),
            "timestamp":            datetime.utcnow().isoformat(),
            "title":                f"Threat detected on {_sanitise(event.get('target_node', 'unknown'))}",
            "summary":              summary,
            "affected_node":        _sanitise(event.get("target_node", "unknown")),
            "vuln_class":           _sanitise(event.get("vuln_class",  "unknown")),
            "risk_score":           round(risk_score, 1),
            "recommended_action":   recommended_patch,
            "estimated_risk_reduction": round(risk_score * 0.4, 1),
            "requires_approval":    True,
            "status":               "pending",
        }

    def _llm_summary(self, event: dict, risk_score: float, patch: str) -> str:
        node   = _sanitise(event.get("target_node", "unknown"))
        action = _sanitise(event.get("action",      "unknown"))
        vuln   = _sanitise(event.get("vuln_class",  "unknown"))

        prompt = (
            f"You are Mahoraga, an adaptive cyber-immune AI system.\n"
            f"Write a 2-sentence plain-language incident report. Under 60 words. No headers.\n"
            f"Sentence 1: attack detected + node. Sentence 2: recommended action + why.\n\n"
            f"Data:\n- Node: {node}\n- Attack: {action}\n- Vuln: {vuln}\n"
            f"- Risk: {risk_score:.0f}/100\n- Recommended: {patch}"
        )

        def _call() -> str:
            import ollama
            response = ollama.chat(model=OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}])
            return response["message"]["content"].strip()

        try:
            future = _exec.submit(_call)
            return future.result(timeout=_TIMEOUT)
        except (FuturesTimeout, Exception) as exc:
            log.warning("LLM summary failed (%s) — using template", exc)
            return self._template_summary(event, risk_score, patch)

    def _template_summary(self, event: dict, risk_score: float, patch: str) -> str:
        return (
            f"Red agent executed {_sanitise(event.get('action', 'unknown attack'))} on "
            f"{_sanitise(event.get('target_node', 'unknown'))} exploiting "
            f"{_sanitise(event.get('vuln_class', 'unknown vulnerability'))} "
            f"(risk: {risk_score:.0f}/100). "
            f"Recommended: {patch} — approve to harden this vulnerability class."
        )


reporter = ReportGenerator()
