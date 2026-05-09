"""
agents/red_agent.py
Patches:
  - threading.Event replaces is_running bool  → thread-safe start/stop
  - reward_history persisted to SQLite via threat_memory.save_reward()
  - red_breach_prob is now windowed (last-20-ep breach rate) not episode_count/100
"""
from __future__ import annotations

import os
import threading
from typing import Callable

from stable_baselines3 import DQN

from agents.environment import MahoragaEnv
from core.config import MODELS_DIR, RED_TRAINING_STEPS


class RedAgent:
    def __init__(self) -> None:
        self.env = MahoragaEnv()
        self.model: DQN | None = None
        self.model_path: str = f"{MODELS_DIR}/red_dqn"

        # FIX: threading.Event instead of a plain bool
        self._running = threading.Event()

        self.episode_count: int = 0
        self.total_vulns_found: int = 0
        self.unique_vulns_found: set = set()
        # Keep last 20 rewards in memory for dashboard; full history in SQLite
        self.reward_history: list[float] = []
        # Track whether each episode had a successful breach (for windowed breach_prob)
        self._breach_window: list[int] = []   # 1 = breach, 0 = no breach

        self.current_action: str = "idle"
        self.current_target: str = "none"
        self.action_frequency: dict[str, int] = {
            name: 0 for name in MahoragaEnv.ACTION_NAMES
        }
        self._broadcast_callback: Callable | None = None

    # ── is_running shim (backwards compat with routes that set it directly) ──
    @property
    def is_running(self) -> bool:
        return self._running.is_set()

    @is_running.setter
    def is_running(self, value: bool) -> None:
        if value:
            self._running.set()
        else:
            self._running.clear()

    def set_broadcast(self, callback: Callable) -> None:
        self._broadcast_callback = callback

    def train(self, steps: int = RED_TRAINING_STEPS) -> None:
        os.makedirs(MODELS_DIR, exist_ok=True)
        self.model = DQN(
            "MlpPolicy", self.env, verbose=0,
            learning_rate=1e-3, buffer_size=10000,
            learning_starts=100, batch_size=32, exploration_fraction=0.3,
        )
        self.model.learn(total_timesteps=steps)
        self.model.save(self.model_path)

    def load(self) -> bool:
        if os.path.exists(f"{self.model_path}.zip"):
            self.model = DQN.load(self.model_path, env=self.env)
            return True
        return False

    def get_windowed_breach_prob(self) -> float:
        """FIX: threat-reactive breach prob from last 20 episodes, not uptime."""
        window = self._breach_window[-20:]
        if not window:
            return 0.0
        return sum(window) / len(window)

    def run_episode(self) -> dict:
        if not self.model:
            return {}
        obs, _ = self.env.reset()
        done = False
        episode_info: dict = {"actions": [], "vulns": [], "reward": 0.0}
        episode_had_breach = False

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

            if info["success"]:
                self.unique_vulns_found.add(info["vuln_class"])
                episode_had_breach = True

            if self._broadcast_callback and info["success"]:
                self._broadcast_callback(info)

        self.episode_count += 1
        self.total_vulns_found += len(self.env.episode_vulns)

        # Update windowed breach window
        self._breach_window.append(1 if episode_had_breach else 0)
        if len(self._breach_window) > 20:
            self._breach_window = self._breach_window[-20:]

        total_reward = round(episode_info["reward"], 2)
        self.reward_history.append(total_reward)
        if len(self.reward_history) > 20:
            self.reward_history = self.reward_history[-20:]

        # FIX: persist reward to SQLite for long-term audit
        try:
            from memory.threat_store import threat_memory
            threat_memory.save_reward(self.episode_count, total_reward)
        except Exception:
            pass

        return {
            "episode": self.episode_count,
            "total_reward": total_reward,
            "vulns_found": len(self.env.episode_vulns),
            "steps": self.env.steps,
        }

    def get_status(self) -> dict:
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
            "windowed_breach_prob": round(self.get_windowed_breach_prob(), 3),
        }


red_agent = RedAgent()
