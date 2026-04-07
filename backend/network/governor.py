from datetime import datetime

from core.config import PROTECTED_SERVICES, CRITICAL_ACTIONS


class AutoimmuneGovernor:
    def __init__(self) -> None:
        self.protected: list[str] = PROTECTED_SERVICES
        self.critical: list[str] = CRITICAL_ACTIONS
        self.overrides: list[dict] = []
        self.override_count: int = 0

    def check(self, target_node: str, action: str) -> bool:
        """Returns True if action is ALLOWED, False if BLOCKED."""
        if target_node in self.protected and action in self.critical:
            record = {
                "timestamp": datetime.utcnow().isoformat(),
                "target": target_node,
                "action": action,
                "decision": "BLOCKED",
            }
            self.overrides.append(record)
            self.override_count += 1
            return False
        return True

    def get_overrides(self) -> list[dict]:
        return self.overrides[-20:]


governor = AutoimmuneGovernor()
