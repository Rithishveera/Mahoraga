"""
detection/baseline_generator.py
Patch: inject 5% synthetic anomalous rows so IsolationForest has a real
decision boundary to train against (contamination=0.05 now matches data).
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
from faker import Faker

from core.config import BASELINE_CSV

fake = Faker()
_rng = np.random.default_rng(42)
_ENTITY_IDS: list[str] = [f"user_{i:03d}" for i in range(20)]


def generate_baseline(days: int = 30, records_per_day: int = 500) -> pd.DataFrame:
    total = days * records_per_day
    anomaly_count = int(total * 0.05)   # FIX: 5% anomalous rows
    normal_count  = total - anomaly_count

    records: list[dict] = []

    # Normal traffic
    for _ in range(normal_count):
        hour = int(np.clip(_rng.normal(10, 3), 0, 23))
        records.append({
            "timestamp":            fake.date_time_this_year().isoformat(),
            "entity_id":            _rng.choice(_ENTITY_IDS),
            "login_hour":           hour,
            "login_ip":             "known" if _rng.random() < 0.9 else "unknown",
            "api_calls_per_minute": float(np.clip(_rng.normal(12, 4), 0, 100)),
            "data_volume_mb":       float(np.clip(_rng.normal(5, 2), 0, 50)),
            "endpoints_accessed":   int(np.clip(_rng.normal(3, 1), 1, 10)),
            "failed_auth_count":    int(np.clip(_rng.poisson(0.2), 0, 10)),
            "session_duration_min": float(np.clip(_rng.normal(45, 15), 1, 480)),
            "is_anomalous":         0,
        })

    # Anomalous traffic (attack-like patterns)
    for _ in range(anomaly_count):
        hour = int(_rng.choice([0, 1, 2, 3, 22, 23]))          # off-hours
        records.append({
            "timestamp":            fake.date_time_this_year().isoformat(),
            "entity_id":            _rng.choice(_ENTITY_IDS),
            "login_hour":           hour,
            "login_ip":             "unknown",
            "api_calls_per_minute": float(np.clip(_rng.normal(80, 10), 40, 200)),  # high
            "data_volume_mb":       float(np.clip(_rng.normal(40, 5), 20, 100)),   # high
            "endpoints_accessed":   int(np.clip(_rng.normal(9, 1), 5, 20)),        # high
            "failed_auth_count":    int(np.clip(_rng.poisson(5), 3, 20)),          # high
            "session_duration_min": float(np.clip(_rng.normal(5, 2), 1, 15)),      # short
            "is_anomalous":         1,
        })

    df = pd.DataFrame(records).sample(frac=1, random_state=42).reset_index(drop=True)
    os.makedirs(os.path.dirname(BASELINE_CSV), exist_ok=True)
    df.to_csv(BASELINE_CSV, index=False)
    return df
