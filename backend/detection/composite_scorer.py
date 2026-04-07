from core.risk_score import risk_engine
from detection.isolation_forest import anomaly_detector
from detection.zscore_profiler import profiler


class CompositeScorer:
    def __init__(self) -> None:
        self.detector = anomaly_detector
        self.profiler = profiler
        self.engine = risk_engine
        self.current_if_score: float = 0.0
        self.current_zscore: float = 0.0

    def score(self, event: dict, red_breach_prob: float = 0.0) -> float:
        entity_id = event.get("entity_id", "unknown")
        self.profiler.update(entity_id, event)
        if_score = self.detector.score(event)
        zscore = self.profiler.get_zscore(entity_id, event)
        self.current_if_score = if_score
        self.current_zscore = zscore
        return self.engine.update(if_score, zscore, red_breach_prob)

    def get_current(self) -> dict:
        return {
            "composite_score": self.engine.get(),
            "if_score": round(self.current_if_score, 3),
            "zscore_delta": round(self.current_zscore, 3),
            "history": self.engine.get_history(),
        }


scorer = CompositeScorer()
