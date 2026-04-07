from datetime import datetime
from uuid import uuid4

from memory.threat_store import threat_memory


class PatchLog:
    def __init__(self) -> None:
        self.entries: list[dict] = []

    def add(self, patch_id: str, vuln_class: str, target_node: str) -> None:
        self.entries.append(
            {
                "id": patch_id,
                "vuln_class": vuln_class,
                "target_node": target_node,
                "timestamp": datetime.utcnow().isoformat(),
                "effectiveness": 1.0,
                "bypassed": False,
            }
        )

    def check_effectiveness(self, patch_id: str, was_bypassed: bool) -> None:
        for entry in self.entries:
            if entry["id"] == patch_id:
                entry["bypassed"] = was_bypassed
                entry["effectiveness"] = 0.0 if was_bypassed else 1.0
                threat_memory.update_effectiveness(patch_id, not was_bypassed)
                return

    def get_recent(self, n: int = 20) -> list[dict]:
        return self.entries[-n:]

    def get_effectiveness_by_class(self) -> dict[str, float]:
        by_class: dict[str, list[float]] = {}
        for entry in self.entries:
            cls = entry["vuln_class"]
            if cls not in by_class:
                by_class[cls] = []
            by_class[cls].append(entry["effectiveness"])
        return {
            cls: round(sum(vals) / len(vals), 3)
            for cls, vals in by_class.items()
        }


patch_log = PatchLog()
