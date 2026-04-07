import pandas as pd

PROFILE_FEATURES: list[str] = [
    "api_calls_per_minute",
    "data_volume_mb",
    "endpoints_accessed",
    "failed_auth_count",
]


class BehaviouralProfiler:
    def __init__(self) -> None:
        self.windows: dict[str, list[dict]] = {}
        self.window_size: int = 50

    def update(self, entity_id: str, event: dict) -> None:
        if entity_id not in self.windows:
            self.windows[entity_id] = []
        self.windows[entity_id].append(event)
        if len(self.windows[entity_id]) > self.window_size:
            self.windows[entity_id] = self.windows[entity_id][-self.window_size:]

    def get_zscore(self, entity_id: str, event: dict) -> float:
        if entity_id not in self.windows or len(self.windows[entity_id]) < 5:
            return 0.0
        window = pd.DataFrame(self.windows[entity_id])
        z_scores: list[float] = []
        for feat in PROFILE_FEATURES:
            if feat not in window.columns:
                continue
            mean = float(window[feat].mean())
            std = float(window[feat].std()) + 0.0001
            val = float(event.get(feat, 0))
            z_scores.append(abs(val - mean) / std)
        if not z_scores:
            return 0.0
        max_z = max(z_scores)
        return float(min(1.0, max_z / 5.0))


profiler = BehaviouralProfiler()
