"""
response/incident_reporter.py
Patches:
  - All LLM prompt fields sanitised (alphanumeric + _ - only, max 32 chars)
    → blocks prompt injection via sim node response body
  - Ollama wrapped in ThreadPoolExecutor with 8-second timeout
    → never blocks the Red Agent daemon thread
  - LLM failure logs a WARNING (previously silent)
"""
from __future__ import annotations

import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from datetime import datetime
from uuid import uuid4

from core.config import OLLAMA_MODEL, USE_LLM_REPORTS

log = logging.getLogger("mahoraga.reporter")

_incident_reports: list[dict] = []
_llm_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="ollama")
_LLM_TIMEOUT = 8.0   # seconds


def _sanitise(value: object) -> str:
    """FIX: Strip everything except alphanumeric, underscore, hyphen. Cap at 32 chars."""
    return re.sub(r"[^a-zA-Z0-9_\-]", "", str(value))[:32]


def _llm_full_report(attack: dict, patch_result: dict, risk_before: float, risk_after: float) -> dict:
    # FIX: sanitise all interpolated fields before building prompt
    node    = _sanitise(attack.get("target_node", "unknown"))
    action  = _sanitise(attack.get("action",      "unknown"))
    vuln    = _sanitise(attack.get("vuln_class",  "unknown"))
    p_act   = _sanitise(patch_result.get("action", "restrict_access"))
    p_app   = str(bool(patch_result.get("patch_applied", False)))
    g_block = str(bool(patch_result.get("governor_blocked", False)))

    prompt = f"""You are Mahoraga, an adaptive cyber-immune AI security system.
Generate a structured incident report in JSON format only. No markdown, no extra text, pure JSON.

Return exactly this structure:
{{
  "threat_summary": "2-3 sentence description",
  "attack_technique": "Name of attack technique",
  "attack_detail": "2-3 sentences on how it works",
  "affected_component": "What was targeted and why it was vulnerable",
  "patch_summary": "2-3 sentences on the fix",
  "patch_technique": "Defensive technique name",
  "prevention": "1-2 sentences on prevention",
  "severity": "CRITICAL|HIGH|MEDIUM|LOW",
  "confidence": "0-100"
}}

Incident data:
- Node: {node}
- Action: {action}
- Vulnerability: {vuln}
- Risk before: {risk_before:.0f}/100
- Risk after: {risk_after:.0f}/100
- Patch action: {p_act}
- Patch applied: {p_app}
- Governor blocked: {g_block}"""

    def _call() -> dict:
        import ollama
        response = ollama.chat(model=OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}])
        content = response["message"]["content"].strip()
        if content.startswith("```"):
            content = "\n".join(l for l in content.split("\n") if not l.startswith("```")).strip()
        return json.loads(content)

    # FIX: run in executor with hard timeout — never blocks calling thread
    try:
        future = _llm_executor.submit(_call)
        return future.result(timeout=_LLM_TIMEOUT)
    except FuturesTimeout:
        log.warning("Ollama timed out after %.0fs — using template fallback", _LLM_TIMEOUT)
    except Exception as exc:
        log.warning("Ollama error: %s — using template fallback", exc)

    return _template_full_report(attack, patch_result, risk_before, risk_after)


def _template_full_report(attack: dict, patch_result: dict, risk_before: float, risk_after: float) -> dict:
    vuln   = _sanitise(attack.get("vuln_class",  "unknown"))
    node   = _sanitise(attack.get("target_node", "unknown"))
    action = _sanitise(attack.get("action",      "unknown"))
    patch  = _sanitise(patch_result.get("action","restrict_access"))

    templates: dict[str, dict] = {
        "xss":            {"attack_technique": "Cross-Site Scripting (XSS)",
                           "attack_detail": "XSS allows attackers to inject malicious scripts into web pages. Scripts execute in the victim's browser enabling session hijacking and credential theft.",
                           "patch_technique": "Input Sanitisation & Output Encoding",
                           "patch_summary": f"User-supplied input on {node} has been sanitised. Output is HTML-encoded.",
                           "prevention": "Validate and encode all user input. Implement a Content Security Policy header."},
        "sql_injection":  {"attack_technique": "SQL Injection",
                           "attack_detail": "SQL injection manipulates database queries via malicious input, exposing or deleting data.",
                           "patch_technique": "Parameterised Queries",
                           "patch_summary": f"The {node} query endpoint now uses parameterised queries exclusively.",
                           "prevention": "Never concatenate user input into SQL. Use an ORM or prepared statements."},
        "default_creds":  {"attack_technique": "Default Credential Exploitation",
                           "attack_detail": "Default credentials are tried against admin interfaces, granting full access on success.",
                           "patch_technique": "Forced Password Rotation",
                           "patch_summary": f"All default credentials on {node} have been invalidated. MFA enforced.",
                           "prevention": "Disable default accounts. Enforce MFA on all admin interfaces."},
        "priv_escalation":{"attack_technique": "Privilege Escalation",
                           "attack_detail": "A misconfigured endpoint allowed low-privilege users to gain root access.",
                           "patch_technique": "Permission Revocation & Least Privilege",
                           "patch_summary": f"Escalation endpoint on {node} disabled. RBAC now enforced.",
                           "prevention": "Apply least privilege. Audit all role assignment endpoints regularly."},
        "unprotected":    {"attack_technique": "Unauthenticated Internal Endpoint Exposure",
                           "attack_detail": "Internal endpoints were accessible without authentication, exposing configuration and credentials.",
                           "patch_technique": "Access Control Enforcement",
                           "patch_summary": f"The internal endpoint on {node} now requires a valid auth token.",
                           "prevention": "Never expose internal endpoints publicly. Apply zero-trust segmentation."},
    }

    t = templates.get(vuln, {
        "attack_technique": vuln.replace("_", " ").title(),
        "attack_detail": f"The {vuln} vulnerability on {node} allowed unauthorised access.",
        "patch_technique": patch.replace("_", " ").title(),
        "patch_summary": f"The {vuln} on {node} remediated via {patch}.",
        "prevention": "Regularly audit and patch all service endpoints.",
    })

    severity = ("CRITICAL" if risk_before > 80 else "HIGH" if risk_before > 60 else
                "MEDIUM" if risk_before > 40 else "LOW")
    return {
        "threat_summary": f"Red Agent executed {t['attack_technique']} on {node} via {action}, risk {risk_before:.0f}/100.",
        **t,
        "affected_component": f"{node} — {vuln} on the {action} endpoint",
        "severity": severity,
        "confidence": min(99, int(risk_before + 10)),
    }


def create_incident_report(attack: dict, patch_result: dict, risk_before: float, risk_after: float) -> dict:
    if USE_LLM_REPORTS:
        details = _llm_full_report(attack, patch_result, risk_before, risk_after)
    else:
        details = _template_full_report(attack, patch_result, risk_before, risk_after)

    report = {
        "id":              str(uuid4()),
        "timestamp":       datetime.utcnow().isoformat(),
        "status":          "PATCHED" if patch_result.get("patch_applied") else "PENDING",
        "node":            _sanitise(attack.get("target_node", "unknown")),
        "vuln_class":      _sanitise(attack.get("vuln_class",  "unknown")),
        "action":          _sanitise(attack.get("action",      "unknown")),
        "risk_before":     round(risk_before, 1),
        "risk_after":      round(risk_after, 1),
        "risk_reduction":  round(risk_before - risk_after, 1),
        "patch_action":    patch_result.get("action", "unknown"),
        "patch_applied":   patch_result.get("patch_applied", False),
        "governor_blocked":patch_result.get("governor_blocked", False),
        **details,
    }
    _incident_reports.insert(0, report)
    if len(_incident_reports) > 100:
        _incident_reports.pop()
    return report


def get_all_reports() -> list[dict]:
    return _incident_reports
