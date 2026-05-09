"""
detection/isolation_forest.py
Patches:
  - contamination='auto' — model self-calibrates; no stale fixed value
  - Model manifest saved/validated on load — detects model/scaler version mismatch
  - Mismatched manifest → refuse to load, retrain from scratch (logged clearly)
"""
from __future__ import annotations

import json
import logging
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from core.config import MODELS_DIR

log = logging.getLogger("mahoraga.anomaly")

FEATURE_COLS: list[str] = [
    "login_hour", "api_calls_per_minute", "data_volume_mb",
    "endpoints_accessed", "failed_auth_count", "session_duration_min",
]


class AnomalyDetector:
    def __init__(self) -> None:
        # FIX: contamination='auto' — model learns the boundary from data
        self.model = IsolationForest(contamination="auto", random_state=42)
        self.scaler = StandardScaler()
        self.is_trained: bool = False
        self.model_path: str  = f"{MODELS_DIR}/isolation_forest.pkl"
        self.scaler_path: str = f"{MODELS_DIR}/if_scaler.pkl"
        self.manifest_path: str = f"{MODELS_DIR}/if_manifest.json"

    def _write_manifest(self) -> None:
        manifest = {
            "feature_cols": FEATURE_COLS,
            "n_features": len(FEATURE_COLS),
            "contamination": "auto",
        }
        with open(self.manifest_path, "w") as f:
            json.dump(manifest, f)

    def _validate_manifest(self) -> bool:
        """Returns True if saved manifest matches current config."""
        if not os.path.exists(self.manifest_path):
            log.warning("No IF manifest found — will retrain")
            return False
        with open(self.manifest_path) as f:
            saved = json.load(f)
        if saved.get("feature_cols") != FEATURE_COLS:
            log.warning("IF manifest feature_cols mismatch — retraining. saved=%s current=%s",
                        saved.get("feature_cols"), FEATURE_COLS)
            return False
        if saved.get("n_features") != len(FEATURE_COLS):
            log.warning("IF manifest n_features mismatch — retraining")
            return False
        return True

    def train(self, df: pd.DataFrame) -> None:
        os.makedirs(MODELS_DIR, exist_ok=True)
        X = df[FEATURE_COLS].fillna(0)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_trained = True
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
        self._write_manifest()
        log.info("IsolationForest trained and manifest saved")

    def load(self) -> bool:
        if not (os.path.exists(self.model_path) and os.path.exists(self.scaler_path)):
            return False
        # FIX: validate manifest before loading — detect mismatch
        if not self._validate_manifest():
            log.warning("Manifest validation failed — refusing to load stale model")
            return False
        self.model = joblib.load(self.model_path)
        self.scaler = joblib.load(self.scaler_path)
        self.is_trained = True
        log.info("IsolationForest loaded from disk (manifest validated)")
        return True

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
