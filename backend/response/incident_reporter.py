import os
from datetime import datetime
from uuid import uuid4

from core.config import OLLAMA_HOST, OLLAMA_MODEL, USE_LLM_REPORTS

# In-memory store of all completed incident reports
_incident_reports: list[dict] = []


def _llm_full_report(
    attack: dict,
    patch_result: dict,
    risk_before: float,
    risk_after: float,
) -> dict:
    """Call Ollama to generate a detailed incident report."""
    try:
        import ollama

        prompt = f"""You are Mahoraga, an adaptive cyber-immune AI security system.
Generate a structured incident report in JSON format only. No markdown, no extra text, pure JSON.

Return exactly this structure:
{{
  "threat_summary": "2-3 sentence description of the attack that was detected",
  "attack_technique": "Name of the attack technique used (e.g. SQL Injection, XSS, Default Credentials)",
  "attack_detail": "2-3 sentences explaining how this attack works and why it is dangerous",
  "affected_component": "What part of the system was targeted and why it was vulnerable",
  "patch_summary": "2-3 sentences explaining exactly what was done to fix the vulnerability",
  "patch_technique": "Name of the defensive technique applied",
  "prevention": "1-2 sentences on how to prevent this class of attack in future",
  "severity": "CRITICAL|HIGH|MEDIUM|LOW",
  "confidence": "percentage 0-100"
}}

Incident data:
- Node attacked: {attack.get('target_node')}
- Attack action: {attack.get('action')}
- Vulnerability class: {attack.get('vuln_class')}
- Risk score before patch: {risk_before:.0f}/100
- Risk score after patch: {risk_after:.0f}/100
- Patch action applied: {patch_result.get('action')}
- Patch was applied: {patch_result.get('patch_applied')}
- Governor blocked: {patch_result.get('governor_blocked')}"""

        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response["message"]["content"].strip()

        # Strip markdown code fences if present
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(
                l for l in lines if not l.startswith("```")
            ).strip()

        import json
        return json.loads(content)

    except Exception as e:
        # Fallback to template if Ollama fails
        return _template_full_report(attack, patch_result, risk_before, risk_after)


def _template_full_report(
    attack: dict,
    patch_result: dict,
    risk_before: float,
    risk_after: float,
) -> dict:
    vuln = attack.get("vuln_class", "unknown")
    node = attack.get("target_node", "unknown")
    action = attack.get("action", "unknown")
    patch = patch_result.get("action", "restrict_access")

    templates = {
        "xss": {
            "attack_technique": "Cross-Site Scripting (XSS)",
            "attack_detail": "XSS allows attackers to inject malicious scripts into web pages viewed by other users. The injected code executes in the victim's browser, enabling session hijacking, credential theft, and malware delivery.",
            "patch_technique": "Input Sanitisation & Output Encoding",
            "patch_summary": f"All user-supplied input on the {node} search endpoint has been sanitised. Output is now HTML-encoded before rendering, preventing script injection.",
            "prevention": "Always validate and encode user input. Implement a Content Security Policy (CSP) header.",
        },
        "sql_injection": {
            "attack_technique": "SQL Injection",
            "attack_detail": "SQL injection allows attackers to manipulate database queries by injecting malicious SQL code. This can expose, modify, or delete all data in the database.",
            "patch_technique": "Parameterised Queries",
            "patch_summary": f"The {node} query endpoint now uses parameterised queries exclusively. Raw SQL string concatenation has been removed, eliminating the injection surface.",
            "prevention": "Never concatenate user input into SQL queries. Use an ORM or prepared statements.",
        },
        "default_creds": {
            "attack_technique": "Default Credential Exploitation",
            "attack_detail": "Default credentials (admin/admin, root/root) are tried against administrative interfaces. Successful login grants full privileged access to the system.",
            "patch_technique": "Forced Password Rotation",
            "patch_summary": f"All default credentials on {node} have been invalidated. A strong password policy is now enforced and initial credential rotation is mandatory on first login.",
            "prevention": "Disable or rename default accounts. Enforce MFA on all administrative interfaces.",
        },
        "unprotected": {
            "attack_technique": "Unauthenticated Internal Endpoint Exposure",
            "attack_detail": "Internal API endpoints were accessible without authentication, exposing database credentials, API keys, and internal configuration to any network-level attacker.",
            "patch_technique": "Access Control Enforcement",
            "patch_summary": f"The internal endpoint on {node} now requires a valid authentication token. Network-level firewall rules have been applied to restrict access to internal services only.",
            "prevention": "Never expose internal endpoints on public interfaces. Apply zero-trust network segmentation.",
        },
        "priv_escalation": {
            "attack_technique": "Privilege Escalation",
            "attack_detail": "An attacker exploited a misconfigured escalation endpoint to elevate from a low-privilege user to root. This grants complete control over the system.",
            "patch_technique": "Permission Revocation & Least Privilege",
            "patch_summary": f"The escalation endpoint on {node} has been disabled. User permissions have been audited and reduced to the minimum required. Role-based access control is now enforced.",
            "prevention": "Apply the principle of least privilege. Audit all role assignment endpoints regularly.",
        },
    }

    t = templates.get(vuln, {
        "attack_technique": vuln.replace("_", " ").title(),
        "attack_detail": f"The {vuln} vulnerability was exploited on {node}, allowing an attacker to gain unauthorised access or extract sensitive information.",
        "patch_technique": patch.replace("_", " ").title(),
        "patch_summary": f"The {vuln} vulnerability on {node} has been remediated using {patch}. The affected endpoint has been hardened against further exploitation.",
        "prevention": "Regularly audit and patch all service endpoints. Implement continuous vulnerability scanning.",
    })

    risk_reduction = risk_before - risk_after
    severity = "CRITICAL" if risk_before > 80 else "HIGH" if risk_before > 60 else "MEDIUM" if risk_before > 40 else "LOW"

    return {
        "threat_summary": f"The Red Agent executed a {t['attack_technique']} attack against {node} via the {action} vector, successfully exploiting the {vuln} vulnerability with a pre-patch risk score of {risk_before:.0f}/100.",
        "attack_technique": t["attack_technique"],
        "attack_detail": t["attack_detail"],
        "affected_component": f"{node} — {vuln} vulnerability on the {action} endpoint",
        "patch_summary": t["patch_summary"],
        "patch_technique": t["patch_technique"],
        "prevention": t["prevention"],
        "severity": severity,
        "confidence": min(99, int(risk_before + 10)),
    }


def create_incident_report(
    attack: dict,
    patch_result: dict,
    risk_before: float,
    risk_after: float,
) -> dict:
    """Create a full incident report and store it."""
    if USE_LLM_REPORTS:
        details = _llm_full_report(attack, patch_result, risk_before, risk_after)
    else:
        details = _template_full_report(attack, patch_result, risk_before, risk_after)

    report = {
        "id": str(uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "status": patch_result.get("patch_applied", False) and "PATCHED" or "PENDING",
        "node": attack.get("target_node", "unknown"),
        "vuln_class": attack.get("vuln_class", "unknown"),
        "action": attack.get("action", "unknown"),
        "risk_before": round(risk_before, 1),
        "risk_after": round(risk_after, 1),
        "risk_reduction": round(risk_before - risk_after, 1),
        "patch_action": patch_result.get("action", "unknown"),
        "patch_applied": patch_result.get("patch_applied", False),
        "governor_blocked": patch_result.get("governor_blocked", False),
        **details,
    }

    _incident_reports.insert(0, report)
    if len(_incident_reports) > 100:
        _incident_reports.pop()

    return report


def get_all_reports() -> list[dict]:
    return _incident_reports
