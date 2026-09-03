"""Risk Threshold Engine – classifies a risk_score into risk levels.

Thresholds are configurable and clearly labeled as prototype values.
"""

from typing import Dict
from app.schemas import RiskLevelEnum

# Prototype configurable thresholds (NOT scientifically validated)
DEFAULT_THRESHOLDS = {
    "LOW_MAX": 0.29,
    "MODERATE_MAX": 0.59,
    "HIGH_MAX": 0.79,
    # >= 0.80 → CRITICAL
}


class RiskThresholdEngine:
    """Classifies numeric risk scores into categorical risk levels."""

    def __init__(self, thresholds: Dict[str, float] = None):
        self.thresholds = thresholds or DEFAULT_THRESHOLDS.copy()

    def classify(self, risk_score: float) -> RiskLevelEnum:
        if not 0 <= risk_score <= 1:
            raise ValueError(f"risk_score must be in [0,1], got {risk_score}")

        if risk_score <= self.thresholds["LOW_MAX"]:
            return RiskLevelEnum.LOW
        elif risk_score <= self.thresholds["MODERATE_MAX"]:
            return RiskLevelEnum.MODERATE
        elif risk_score <= self.thresholds["HIGH_MAX"]:
            return RiskLevelEnum.HIGH
        else:
            return RiskLevelEnum.CRITICAL

    def classify_environmental_factor(self, name: str, value: float) -> str:
        """Classify an individual environmental factor as LOW/MODERATE/HIGH."""
        factor_thresholds = {
            "rainfall_1h":   (10, 25),
            "rainfall_6h":   (30, 60),
            "rainfall_24h":  (50, 150),
            "rainfall_72h":  (100, 300),
            "slope":         (15, 30),
            "elevation":     (500, 1500),
            "soil_moisture": (0.4, 0.7),
            "historical_landslide_density": (0.3, 0.6),
        }
        low_t, high_t = factor_thresholds.get(name, (0.33, 0.66))
        if value <= low_t:
            return "LOW"
        elif value <= high_t:
            return "MODERATE"
        else:
            return "HIGH"

    def get_thresholds(self) -> Dict:
        return {
            "LOW":      f"0.00 – {self.thresholds['LOW_MAX']:.2f}",
            "MODERATE": f"{self.thresholds['LOW_MAX']+0.01:.2f} – {self.thresholds['MODERATE_MAX']:.2f}",
            "HIGH":     f"{self.thresholds['MODERATE_MAX']+0.01:.2f} – {self.thresholds['HIGH_MAX']:.2f}",
            "CRITICAL": f"{self.thresholds['HIGH_MAX']+0.01:.2f} – 1.00",
            "note": "Prototype configurable thresholds – not scientifically validated",
        }


# Singleton
risk_engine = RiskThresholdEngine()
