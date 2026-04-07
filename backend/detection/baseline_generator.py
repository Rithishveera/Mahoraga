import os

import numpy as np
import pandas as pd
from faker import Faker

from core.config import BASELINE_CSV

fake = Faker()
_rng = np.random.default_rng(42)

_ENTITY_IDS: list[str] = [f"user_{i:03d}" for i in range(20)]


def generate_baseline(days: int = 30, records_per_day: int = 500) -> pd.DataFrame:
    records: list[dict] = []
    for _ in range(days * records_per_day):
        # Weight toward business hours
        hour = int(np.clip(_rng.normal(10, 3), 0, 23))
        records.append(
            {
                "timestamp": fake.date_time_this_year().isoformat(),
                "entity_id": _rng.choice(_ENTITY_IDS),
                "login_hour": hour,
                "login_ip": "known" if _rng.random() < 0.9 else "unknown",
                "api_calls_per_minute": float(
                    np.clip(_rng.normal(12, 4), 0, 100)
                ),
                "data_volume_mb": float(np.clip(_rng.normal(5, 2), 0, 50)),
                "endpoints_accessed": int(np.clip(_rng.normal(3, 1), 1, 10)),
                "failed_auth_count": int(
                    np.clip(_rng.poisson(0.2), 0, 10)
                ),
                "session_duration_min": float(
                    np.clip(_rng.normal(45, 15), 1, 480)
                ),
                "is_anomalous": 0,
            }
        )

    df = pd.DataFrame(records)
    os.makedirs(os.path.dirname(BASELINE_CSV), exist_ok=True)
    df.to_csv(BASELINE_CSV, index=False)
    return df
