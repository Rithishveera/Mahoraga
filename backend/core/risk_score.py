from datetime import datetime
from threading import Lock


class RiskScoreEngine:
    def __init__(self) -> None:
        self._score: float = 0.0
        self._history: list[dict] = []
        self._lock = Lock()

    def update(
        self,
        if_score: float,
        zscore_delta: float,
        red_breach_prob: float,
    ) -> float:
        raw = (if_score * 40.0) + (zscore_delta * 30.0) + (red_breach_prob * 30.0)
        score = max(0.0, min(100.0, raw))
        with self._lock:
            self._score = score
            self._history.append(
                {"score": round(score, 2), "timestamp": datetime.utcnow().isoformat()}
            )
            if len(self._history) > 100:
                self._history = self._history[-100:]
        return score

    def get(self) -> float:
        return round(self._score, 2)

    def get_history(self) -> list[dict]:
        return self._history[-20:]

    def manual_adjust(self, delta: float) -> None:
        with self._lock:
            self._score = max(0.0, min(100.0, self._score + delta))

    def reset(self) -> None:
        with self._lock:
            self._score = 0.0


risk_engine = RiskScoreEngine()
