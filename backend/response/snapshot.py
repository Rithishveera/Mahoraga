from datetime import datetime
from uuid import uuid4

from agents.blue_agent import blue_agent
from core.risk_score import risk_engine
from memory.threat_store import threat_memory
from network.topology import topology


class ForensicSnapshot:
    def __init__(self) -> None:
        self.snapshots: list[dict] = []

    def take(self, trigger_event: dict, risk_score: float) -> dict:
        snap = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "trigger_event": trigger_event,
            "risk_score_at_trigger": risk_score,
            "network_state": topology.get_state(),
            "active_patches": blue_agent.patches_applied[-10:],
            "recent_attacks": threat_memory.get_all_attacks()[-10:],
            "risk_history": risk_engine.get_history(),
        }
        self.snapshots.append(snap)
        return snap

    def get_all(self) -> list[dict]:
        return self.snapshots[-20:]


snapshotter = ForensicSnapshot()
