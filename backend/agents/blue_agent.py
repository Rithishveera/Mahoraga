"""
agents/blue_agent.py
Patches:
  - LabelEncoder replaces hash(vuln) % 1000  → no hash collisions
  - _samples_since_retrain counter replaces modulo trigger → never misses
  - respond() persists patch to node_patch_state via threat_memory
"""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

from core.config import BLUE_RETRAIN_INTERVAL
from network.governor import governor
from network.topology import topology

VULN_TO_PATCH: dict[str, str] = {
    "xss":            "patch_endpoint",
    "admin_exposure": "restrict_access",
    "info_disclosure":"remove_endpoint",
    "injection":      "patch_endpoint",
    "weak_creds":     "rotate_credentials",
    "unprotected":    "restrict_access",
    "sql_injection":  "patch_endpoint",
    "data_dump":      "restrict_access",
    "unauth_access":  "restrict_access",
    "default_creds":  "force_password_change",
    "user_enum":      "restrict_access",
    "priv_escalation":"revoke_permissions",
}

VULN_ENDPOINT_MAP: dict[str, str] = {k: k for k in VULN_TO_PATCH}

# Deterministic collision-free encoder fitted over known vocab
_label_enc = LabelEncoder()
_label_enc.fit(sorted(VULN_TO_PATCH.keys()))


class BlueAgent:
    def __init__(self) -> None:
        self.model = RandomForestClassifier(n_estimators=50, random_state=42)
        self.governor = governor
        self.topology = topology
        self.training_data: list[tuple] = []
        self.patches_applied: list[dict] = []
        self.is_trained: bool = False
        self.patch_count: int = 0
        self.governor_blocks: int = 0
        # FIX: counter replaces modulo — never skips a retrain boundary
        self._samples_since_retrain: int = 0

    def respond(self, vuln_class: str, target_node: str) -> dict:
        # Validate vuln_class is known (injection-safety)
        if vuln_class not in VULN_TO_PATCH:
            vuln_class = "unprotected"

        patch_action = VULN_TO_PATCH[vuln_class]
        allowed = self.governor.check(target_node, patch_action)

        if not allowed:
            self.governor_blocks += 1
            return {
                "action": patch_action, "target": target_node,
                "allowed": False, "governor_blocked": True, "patch_applied": False,
            }

        result = self.topology.apply_patch(target_node, VULN_ENDPOINT_MAP[vuln_class])
        self.topology.mark_patched(target_node, vuln_class)

        # Persist patch state so restarts don't lose it
        from memory.threat_store import threat_memory
        threat_memory.save_node_patch(target_node, vuln_class)

        record: dict = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "vuln_class": vuln_class,
            "patch_action": patch_action,
            "target_node": target_node,
            "effectiveness": 1.0,
            "held": True,
        }
        self.patches_applied.append(record)
        self.patch_count += 1

        self.training_data.append((vuln_class, patch_action))
        self._samples_since_retrain += 1
        if self._samples_since_retrain >= BLUE_RETRAIN_INTERVAL:
            self.retrain()
            self._samples_since_retrain = 0

        return {
            "action": patch_action, "target": target_node,
            "allowed": True, "governor_blocked": False,
            "patch_applied": result.get("patched", False),
            "record_id": record["id"],
        }

    def retrain(self) -> None:
        if len(self.training_data) < 5:
            return
        # FIX: LabelEncoder — deterministic, collision-free integer per class
        known = set(_label_enc.classes_)
        filtered = [(v, p) for v, p in self.training_data if v in known]
        if not filtered:
            return
        X = [[int(_label_enc.transform([v])[0])] for v, _ in filtered]
        y = [p for _, p in filtered]
        self.model.fit(X, y)
        self.is_trained = True

    def get_status(self) -> dict:
        return {
            "patch_count": self.patch_count,
            "governor_blocks": self.governor_blocks,
            "is_trained": self.is_trained,
            "patches_applied": self.patches_applied[-10:],
            "training_samples": len(self.training_data),
        }


blue_agent = BlueAgent()
