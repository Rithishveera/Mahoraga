from datetime import datetime
from uuid import uuid4

from sklearn.ensemble import RandomForestClassifier

from core.config import BLUE_RETRAIN_INTERVAL
from network.governor import governor
from network.topology import topology

VULN_TO_PATCH: dict[str, str] = {
    "xss": "patch_endpoint",
    "admin_exposure": "restrict_access",
    "info_disclosure": "remove_endpoint",
    "injection": "patch_endpoint",
    "weak_creds": "rotate_credentials",
    "unprotected": "restrict_access",
    "sql_injection": "patch_endpoint",
    "data_dump": "restrict_access",
    "unauth_access": "restrict_access",
    "default_creds": "force_password_change",
    "user_enum": "restrict_access",
    "priv_escalation": "revoke_permissions",
}

VULN_ENDPOINT_MAP: dict[str, str] = {
    "xss": "xss",
    "admin_exposure": "admin_exposure",
    "info_disclosure": "info_disclosure",
    "injection": "injection",
    "weak_creds": "weak_creds",
    "unprotected": "unprotected",
    "sql_injection": "sql_injection",
    "data_dump": "data_dump",
    "unauth_access": "unauth_access",
    "default_creds": "default_creds",
    "user_enum": "user_enum",
    "priv_escalation": "priv_escalation",
}


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

    def respond(self, vuln_class: str, target_node: str) -> dict:
        patch_action = VULN_TO_PATCH.get(vuln_class, "restrict_access")
        allowed = self.governor.check(target_node, patch_action)

        if not allowed:
            self.governor_blocks += 1
            return {
                "action": patch_action,
                "target": target_node,
                "allowed": False,
                "governor_blocked": True,
                "patch_applied": False,
            }

        endpoint_vuln = VULN_ENDPOINT_MAP.get(vuln_class, vuln_class)
        result = self.topology.apply_patch(target_node, endpoint_vuln)
        self.topology.mark_patched(target_node, vuln_class)

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
        if len(self.training_data) % BLUE_RETRAIN_INTERVAL == 0:
            self.retrain()

        return {
            "action": patch_action,
            "target": target_node,
            "allowed": True,
            "governor_blocked": False,
            "patch_applied": result.get("patched", False),
            "record_id": record["id"],
        }

    def retrain(self) -> None:
        if len(self.training_data) < 5:
            return
        X = [[hash(vuln) % 1000] for vuln, _ in self.training_data]
        y = [patch for _, patch in self.training_data]
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
