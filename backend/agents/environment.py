import numpy as np
import gymnasium

from agents.reward import red_reward
from core.risk_score import risk_engine
from network.topology import topology


class MahoragaEnv(gymnasium.Env):
    metadata: dict = {"render_modes": []}

    ACTION_NAMES: list[str] = [
        "port_scan_web_server",
        "port_scan_api_service",
        "try_default_creds_admin",
        "inject_payload_web",
        "probe_database",
        "exploit_unprotected_endpoint",
        "attempt_privilege_escalation",
        "lateral_move_to_internal",
    ]

    ACTION_MAP: dict[int, tuple[str, str, str]] = {
        0: ("web_server", "info", "info_disclosure"),
        1: ("api_service", "internal", "unprotected"),
        2: ("admin_panel", "login", "default_creds"),
        3: ("web_server", "search", "xss"),
        4: ("database_node", "query", "sql_injection"),
        5: ("api_service", "internal", "unprotected"),
        6: ("admin_panel", "escalate", "priv_escalation"),
        7: ("database_node", "dump", "data_dump"),
    }

    action_space = gymnasium.spaces.Discrete(8)
    observation_space = gymnasium.spaces.Box(
        low=0, high=1, shape=(20,), dtype=np.float32
    )

    def __init__(self) -> None:
        super().__init__()
        self.topology = topology
        self.steps: int = 0
        self.max_steps: int = 200
        self.episode_vulns: list[str] = []
        self.episode_breaches: int = 0
        self.actions_taken: list[str] = []
        self.total_reward: float = 0.0

    def reset(
        self, seed: int | None = None, options: dict | None = None
    ) -> tuple[np.ndarray, dict]:
        super().reset(seed=seed)
        self.steps = 0
        self.episode_vulns = []
        self.episode_breaches = 0
        self.actions_taken = []
        self.total_reward = 0.0
        return self._get_obs(), {}

    def step(self, action: int) -> tuple[np.ndarray, float, bool, bool, dict]:
        self.steps += 1
        node_name, endpoint, vuln_class = self.ACTION_MAP[action]
        action_name = self.ACTION_NAMES[action]

        result = self.topology.probe_node(node_name, endpoint)
        success = result["success"] and result.get("status_code", 500) == 200

        reward, event_type = self._calculate_reward(action, node_name, vuln_class, success)
        self.total_reward += reward

        if success and vuln_class not in self.episode_vulns:
            self.episode_vulns.append(vuln_class)
            self.topology.mark_vuln_found(node_name, vuln_class)

        self.actions_taken.append(action_name)
        terminated = self.steps >= self.max_steps
        obs = self._get_obs()
        info = {
            "action_name": action_name,
            "node": node_name,
            "vuln_class": vuln_class,
            "success": success,
            "event_type": event_type,
            "reward": reward,
        }
        return obs, reward, terminated, False, info

    def _get_obs(self) -> np.ndarray:
        nodes = list(self.topology.nodes.values())
        obs: list[float] = []
        for node in nodes:
            obs.append(1.0 if len(node.vulns_found) > 0 else 0.0)
        for node in nodes:
            obs.append(1.0 if len(node.patches_applied) > 0 else 0.0)
        for node in nodes:
            obs.append(1.0 if node.is_compromised else 0.0)
        for node in nodes:
            obs.append(node.risk_score / 100.0)
        obs.append(self.steps / self.max_steps)
        obs.append(len(self.episode_vulns) / 8.0)
        obs.append(self.episode_breaches / 10.0)
        obs.append(risk_engine.get() / 100.0)
        obs.append(
            1.0
            if self.steps > 0 and self.actions_taken[-1] in self.actions_taken[:-1]
            else 0.0
        )
        obs.append(sum(len(n.patches_applied) for n in nodes) / 8.0)
        obs.append(0.0)
        obs.append(0.0)
        return np.array(obs[:20], dtype=np.float32)

    def _calculate_reward(
        self, action: int, node_name: str, vuln_class: str, success: bool
    ) -> tuple[float, str]:
        node = self.topology.get_node(node_name)
        if vuln_class in node.patches_applied:
            return red_reward("patched_target"), "patched_target"
        if success and vuln_class not in self.episode_vulns:
            return red_reward("new_vuln_found"), "new_vuln_found"
        if success:
            self.episode_breaches += 1
            return red_reward("successful_breach"), "successful_breach"
        action_name = self.ACTION_NAMES[action]
        if action_name in self.actions_taken[:-1]:
            return red_reward("repeated_action"), "repeated_action"
        return red_reward("failed_action"), "failed_action"
