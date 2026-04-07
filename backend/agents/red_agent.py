import os
from typing import Callable

from stable_baselines3 import DQN

from agents.environment import MahoragaEnv
from core.config import MODELS_DIR, RED_TRAINING_STEPS


class RedAgent:
    def __init__(self) -> None:
        self.env = MahoragaEnv()
        self.model: DQN | None = None
        self.model_path: str = f"{MODELS_DIR}/red_dqn"
        self.is_running: bool = False
        self.episode_count: int = 0
        self.total_vulns_found: int = 0
        self.unique_vulns_found: set = set()
        self.reward_history: list[float] = []
        self.current_action: str = "idle"
        self.current_target: str = "none"
        self.action_frequency: dict[str, int] = {
            name: 0 for name in MahoragaEnv.ACTION_NAMES
        }
        self._broadcast_callback: Callable | None = None

    def set_broadcast(self, callback: Callable) -> None:
        self._broadcast_callback = callback

    def train(self, steps: int = RED_TRAINING_STEPS) -> None:
        os.makedirs(MODELS_DIR, exist_ok=True)
        self.model = DQN(
            "MlpPolicy",
            self.env,
            verbose=0,
            learning_rate=1e-3,
            buffer_size=10000,
            learning_starts=100,
            batch_size=32,
            exploration_fraction=0.3,
        )
        self.model.learn(total_timesteps=steps)
        self.model.save(self.model_path)

    def load(self) -> bool:
        if os.path.exists(f"{self.model_path}.zip"):
            self.model = DQN.load(self.model_path, env=self.env)
            return True
        return False

    def run_episode(self) -> dict:
        if not self.model:
            return {}
        obs, _ = self.env.reset()
        done = False
        episode_info: dict = {"actions": [], "vulns": [], "reward": 0.0}

        while not done:
            action, _ = self.model.predict(obs, deterministic=False)
            obs, reward, terminated, truncated, info = self.env.step(int(action))
            done = terminated or truncated

            self.current_action = info["action_name"]
            self.current_target = info["node"]
            self.action_frequency[info["action_name"]] = (
                self.action_frequency.get(info["action_name"], 0) + 1
            )
            episode_info["actions"].append(info["action_name"])
            episode_info["reward"] += reward

            # Track unique vulns globally
            if info["success"]:
                self.unique_vulns_found.add(info["vuln_class"])

            if self._broadcast_callback and info["success"]:
                self._broadcast_callback(info)

        self.episode_count += 1
        self.total_vulns_found += len(self.env.episode_vulns)
        self.reward_history.append(episode_info["reward"])
        if len(self.reward_history) > 20:
            self.reward_history = self.reward_history[-20:]

        return {
            "episode": self.episode_count,
            "total_reward": round(episode_info["reward"], 2),
            "vulns_found": len(self.env.episode_vulns),
            "steps": self.env.steps,
        }

    def get_status(self) -> dict:
        # Coverage based on unique vuln classes found out of 12 total
        coverage = round(len(self.unique_vulns_found) / 12 * 100, 1)
        return {
            "is_running": self.is_running,
            "episode_count": self.episode_count,
            "total_vulns_found": self.total_vulns_found,
            "current_action": self.current_action,
            "current_target": self.current_target,
            "reward_history": self.reward_history,
            "action_frequency": self.action_frequency,
            "attack_surface_coverage": min(coverage, 100.0),
        }


red_agent = RedAgent()
