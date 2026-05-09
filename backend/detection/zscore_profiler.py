"""
detection/zscore_profiler.py
Patches:
  - Minimum 10-sample window before scoring (not 5) — reduces volatile early scores
  - Winsorized std floor: max(std, mean*0.1 + 0.01) — prevents division-by-near-zero saturation
  - Cap individual Z-scores at 3σ before normalising — one event can't saturate to 1.0
"""
from __future__ import annotations

import numpy as np
import pandas as pd

PROFILE_FEATURES: list[str] = [
    "api_calls_per_minute",
    "data_volume_mb",
    "endpoints_accessed",
    "failed_auth_count",
]

_MIN_SAMPLES = 10   # FIX: was 5
_MAX_SIGMA   = 3.0  # FIX: cap Z at 3σ before normalising


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
        if entity_id not in self.windows or len(self.windows[entity_id]) < _MIN_SAMPLES:
            return 0.0

        window = pd.DataFrame(self.windows[entity_id])
        z_scores: list[float] = []

        for feat in PROFILE_FEATURES:
            if feat not in window.columns:
                continue
            vals = window[feat].dropna().astype(float)
            mean = float(vals.mean())
            raw_std = float(vals.std())
            # FIX: Winsorized std floor — prevents (val/0.0001)*10000 = saturation
            std = max(raw_std, abs(mean) * 0.1 + 0.01)
            val = float(event.get(feat, 0))
            z = abs(val - mean) / std
            # FIX: cap at 3σ — one outlier event can't max the entire component
            z_scores.append(min(z, _MAX_SIGMA))

        if not z_scores:
            return 0.0
        max_z = max(z_scores)
        return float(min(1.0, max_z / _MAX_SIGMA))


profiler = BehaviouralProfiler()
