import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from core.config import MODELS_DIR

FEATURE_COLS: list[str] = [
    "login_hour",
    "api_calls_per_minute",
    "data_volume_mb",
    "endpoints_accessed",
    "failed_auth_count",
    "session_duration_min",
]


class AnomalyDetector:
    def __init__(self) -> None:
        self.model = IsolationForest(contamination=0.05, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained: bool = False
        self.model_path: str = f"{MODELS_DIR}/isolation_forest.pkl"
        self.scaler_path: str = f"{MODELS_DIR}/if_scaler.pkl"

    def train(self, df: pd.DataFrame) -> None:
        os.makedirs(MODELS_DIR, exist_ok=True)
        X = df[FEATURE_COLS].fillna(0)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_trained = True
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)

    def load(self) -> bool:
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
            self.is_trained = True
            return True
        return False

    def score(self, event: dict) -> float:
        if not self.is_trained:
            return 0.0
        row = pd.DataFrame([{col: event.get(col, 0) for col in FEATURE_COLS}])
        X_scaled = self.scaler.transform(row)
        raw = float(self.model.decision_function(X_scaled)[0])
        score = 1.0 - (raw - (-0.5)) / (0.5 - (-0.5))
        return float(max(0.0, min(1.0, score)))

    def is_anomalous(self, event: dict, threshold: float = 0.6) -> bool:
        return self.score(event) > threshold


anomaly_detector = AnomalyDetector()
