import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import numpy as np


logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).resolve().parents[2] / "model"
MODEL_PATH = MODEL_DIR / "sla_model.pkl"
ENCODER_PATH = MODEL_DIR / "encoders.pkl"

DEFAULT_FEATURE_ORDER = [
    "lens_type",
    "current_stage",
    "order_age_hours",
    "sla_hours",
    "inventory_available",
    "qc_failures",
    "store_location",
    "rework_count",
    "delay_reason",
]


class PredictionError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def load_artifacts() -> tuple[Any, dict[str, Any]]:
    try:
        model = joblib.load(MODEL_PATH)
        encoders = joblib.load(ENCODER_PATH)
    except FileNotFoundError as exc:
        logger.exception("SLA model artifact missing")
        raise PredictionError("SLA model artifacts are missing") from exc
    except Exception as exc:
        logger.exception("Failed to load SLA model artifacts")
        raise PredictionError("Unable to load SLA model artifacts") from exc
    return model, encoders


def _risk_level(probability: float) -> str:
    if probability >= 0.7:
        return "High"
    if probability >= 0.3:
        return "Medium"
    return "Low"


def _encode_value(feature: str, value: Any, encoders: dict[str, Any]) -> Any:
    encoder = encoders.get(feature)
    if encoder is None:
        return value

    normalized = "None" if value in (None, "") else str(value)
    if normalized not in set(encoder.classes_):
        logger.warning("Unknown category '%s' for feature '%s'; using first known class", normalized, feature)
        normalized = str(encoder.classes_[0])
    return int(encoder.transform([normalized])[0])


def predict_breach(order_data: dict[str, Any]) -> dict[str, float | str]:
    try:
        model, encoders = load_artifacts()
        feature_order = list(getattr(model, "feature_names_in_", DEFAULT_FEATURE_ORDER)) or DEFAULT_FEATURE_ORDER
        encoded_features = [
            _encode_value(feature, order_data.get(feature), encoders)
            for feature in feature_order
        ]

        # Use predict_proba as per instructions and clip to [0.0, 1.0]
        val = model.predict_proba([encoded_features])[:, 1][0]
        probability = float(np.clip(val, 0.0, 1.0))

        return {
            "breach_probability": probability,
            "risk_level": _risk_level(probability),
        }
    except PredictionError:
        raise
    except Exception as exc:
        logger.exception("SLA breach prediction failed for payload: %s", order_data)
        raise PredictionError("SLA breach prediction failed") from exc
