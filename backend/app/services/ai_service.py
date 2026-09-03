"""XGBoost-based landslide risk prediction service.

Trains a simple XGBoost model on synthetic NER-representative data
and persists it to disk. Loads the trained model for inference.
"""

import os
import numpy as np
import xgboost as xgb
import joblib
from typing import Dict, Optional
from datetime import datetime

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ai", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "xgboost_landslide_v1.joblib")

FEATURE_NAMES = [
    "rainfall_1h", "rainfall_6h", "rainfall_24h", "rainfall_72h",
    "slope", "elevation", "soil_moisture", "land_cover",
    "historical_landslide_density",
]

MODEL_VERSION = "xgboost-v1"


class AIService:
    """Manages loading / training / predicting with the XGBoost model."""

    def __init__(self):
        self.model: Optional[xgb.XGBClassifier] = None
        self._ensure_model()

    # ── bootstrap ────────────────────────────────────────────────────────
    def _ensure_model(self):
        os.makedirs(MODEL_DIR, exist_ok=True)
        if os.path.exists(MODEL_PATH):
            self.model = joblib.load(MODEL_PATH)
        else:
            self._train_demo_model()

    # ── synthetic training data representative of NE India ───────────────
    def _train_demo_model(self):
        """Train on synthetic data that captures landslide risk patterns."""
        rng = np.random.RandomState(42)
        n = 2000

        # Features
        rainfall_1h = rng.exponential(10, n)
        rainfall_6h = rainfall_1h * rng.uniform(2, 5, n)
        rainfall_24h = rainfall_6h * rng.uniform(2, 4, n)
        rainfall_72h = rainfall_24h * rng.uniform(1.5, 3, n)
        slope = rng.uniform(0, 60, n)
        elevation = rng.uniform(100, 2500, n)
        soil_moisture = rng.uniform(0.1, 1.0, n)
        land_cover = rng.randint(0, 8, n)
        historical = rng.uniform(0, 1, n)

        X = np.column_stack([
            rainfall_1h, rainfall_6h, rainfall_24h, rainfall_72h,
            slope, elevation, soil_moisture, land_cover, historical,
        ])

        # Risk label driven by domain heuristics
        risk = (
            0.25 * (rainfall_24h / 300).clip(0, 1)
            + 0.15 * (rainfall_72h / 500).clip(0, 1)
            + 0.20 * (slope / 60).clip(0, 1)
            + 0.15 * soil_moisture
            + 0.10 * historical
            + 0.05 * (1 - elevation / 2500).clip(0, 1)
            + 0.10 * (rainfall_1h / 50).clip(0, 1)
        )
        noise = rng.normal(0, 0.05, n)
        risk = np.clip(risk + noise, 0, 1)
        labels = (risk >= 0.5).astype(int)

        self.model = xgb.XGBClassifier(
            n_estimators=150,
            max_depth=5,
            learning_rate=0.1,
            use_label_encoder=False,
            eval_metric="logloss",
            random_state=42,
        )
        self.model.fit(X, labels)
        joblib.dump(self.model, MODEL_PATH)

    # ── inference ────────────────────────────────────────────────────────
    def predict(self, features: Dict[str, float]) -> Dict:
        if self.model is None:
            raise RuntimeError("AI model is not loaded")

        ordered = [features.get(f, 0) for f in FEATURE_NAMES]
        arr = np.array([ordered])
        proba = self.model.predict_proba(arr)[0]
        risk_score = float(round(proba[1], 4))  # probability of class 1
        risk_score = max(0.0, min(1.0, risk_score))

        return {
            "risk_score": risk_score,
            "model_version": MODEL_VERSION,
            "timestamp": datetime.utcnow().isoformat(),
            "feature_importances": self._feature_importances(),
        }

    def _feature_importances(self) -> Dict[str, float]:
        if self.model is None:
            return {}
        importances = self.model.feature_importances_
        return {name: float(round(imp, 4)) for name, imp in zip(FEATURE_NAMES, importances)}

    def get_status(self) -> Dict:
        return {
            "name": "XGBoost Landslide Risk Model",
            "version": MODEL_VERSION,
            "is_loaded": self.model is not None,
            "model_path": MODEL_PATH,
            "features": FEATURE_NAMES,
        }


# Singleton
ai_service = AIService()
