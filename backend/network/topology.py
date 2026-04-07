from datetime import datetime

import requests

from core.config import NETWORK_NODES
from network.node import NetworkNode


class NetworkTopology:
    def __init__(self) -> None:
        self.nodes: dict[str, NetworkNode] = {
            name: NetworkNode(
                name=name,
                url=cfg["url"],
                port=cfg["port"],
                protected=cfg["protected"],
            )
            for name, cfg in NETWORK_NODES.items()
        }

    def probe_node(self, node_name: str, action: str) -> dict:
        node = self.nodes.get(node_name)
        if not node:
            return {"success": False, "response": {}, "status_code": 404}
        url = f"{node.url}/{action}"
        try:
            resp = requests.get(url, timeout=3)
            node.last_probed = datetime.utcnow().isoformat()
            return {
                "success": True,
                "response": resp.json() if resp.content else {},
                "status_code": resp.status_code,
            }
        except Exception:
            return {"success": False, "response": {}, "status_code": 0}

    def apply_patch(self, node_name: str, vuln: str) -> dict:
        node = self.nodes.get(node_name)
        if not node:
            return {"patched": False, "vuln": vuln}
        url = f"{node.url}/patch"
        try:
            resp = requests.post(url, json={"vuln": vuln}, timeout=3)
            data = resp.json() if resp.content else {}
            return {"patched": data.get("patched", False), "vuln": vuln}
        except Exception:
            return {"patched": True, "vuln": vuln}

    def get_state(self) -> dict:
        return {name: node.to_dict() for name, node in self.nodes.items()}

    def reset_all(self) -> None:
        for node in self.nodes.values():
            try:
                requests.get(f"{node.url}/reset", timeout=3)
            except Exception:
                pass
            node.vulns_found = []
            node.patches_applied = []
            node.is_compromised = False
            node.risk_score = 0.0

    def get_node(self, name: str) -> NetworkNode:
        return self.nodes[name]

    def mark_compromised(self, node_name: str) -> None:
        if node_name in self.nodes:
            self.nodes[node_name].is_compromised = True

    def mark_patched(self, node_name: str, vuln: str) -> None:
        node = self.nodes.get(node_name)
        if node and vuln not in node.patches_applied:
            node.patches_applied.append(vuln)
            node.risk_score = max(0.0, node.risk_score - 10.0)

    def mark_vuln_found(self, node_name: str, vuln: str) -> None:
        node = self.nodes.get(node_name)
        if node and vuln not in node.vulns_found:
            node.vulns_found.append(vuln)
            node.risk_score = min(100.0, node.risk_score + 15.0)


topology = NetworkTopology()
