"""
ml_inference_service.py
=======================
Robust ML inference wrapper with fallback mechanisms and graceful degradation.

Responsibilities:
  1. Load the Isolation Forest model safely with try-except.
  2. Validate input dimensionality before inference (detect data drift).
  3. If inference fails, log CRITICAL but continue database ingestion.
  4. Provide a clean API for the MQTT subscriber to call.

Architecture:
    MQTT Subscriber -> Schema Validator -> ML Inference Service -> InfluxDB
                              |                    |
                              v                    v (on failure)
                         Reject msg          Log CRITICAL, skip ML tag
                                              but still write to DB
"""

import os
import logging
import joblib
from typing import Optional, Dict, Any, List
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

# Resolve model path relative to project root
_SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SERVICE_DIR)

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("MLInferenceService")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MODEL_PATH = os.environ.get(
    "IFOREST_MODEL_PATH",
    os.path.join(_PROJECT_ROOT, "ml_models", "iforest_model.pkl"),
)
FEATURE_COLS = [
    "voltage", "current", "active_power", "power_factor",
    "apparent_power", "reactive_power",
    "delta_P", "delta_Q",
    "current_rolling_var_60s",
]
EXPECTED_N_FEATURES = len(FEATURE_COLS)


# ---------------------------------------------------------------------------
# ML Inference Service Class
# ---------------------------------------------------------------------------
class MLInferenceService:
    """
    Singleton-style wrapper around the Isolation Forest model.

    Guarantees:
      - If the model fails to load, the service enters "degraded mode".
      - In degraded mode, all inference requests return None but ingestion continues.
      - Dimensionality mismatches (data drift) are caught and logged without crashing.
    """

    _instance: Optional["MLInferenceService"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_path: str = MODEL_PATH):
        if self._initialized:
            return

        self.model_path = model_path
        self.model: Optional[IsolationForest] = None
        self.degraded_mode = False
        self.degraded_reason: Optional[str] = None
        self.inference_count = 0
        self.error_count = 0

        self._load_model()
        self._initialized = True

    # ------------------------------------------------------------------
    # Model Loading
    # ------------------------------------------------------------------
    def _load_model(self) -> None:
        """Attempt to load the Isolation Forest model from disk."""
        try:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model file not found: {self.model_path}")

            self.model = joblib.load(self.model_path)

            # Sanity check: ensure it's the right type
            if not isinstance(self.model, IsolationForest):
                raise TypeError(
                    f"Loaded model is {type(self.model).__name__}, expected IsolationForest"
                )

            logger.info(
                f"[ML] Model loaded successfully from {self.model_path}. "
                f"Estimators={self.model.n_estimators}, Features={EXPECTED_N_FEATURES}"
            )

        except Exception as exc:
            self._enter_degraded_mode(f"Model load failed: {exc}")

    def _enter_degraded_mode(self, reason: str) -> None:
        """Switch to degraded mode where inference is skipped but ingestion continues."""
        self.degraded_mode = True
        self.degraded_reason = reason
        self.model = None
        logger.critical(f"[ML] DEGRADED MODE: {reason}")
        logger.critical(
            "[ML] The system will continue ingesting data to the database, "
            "but anomaly detection is OFFLINE until the model is restored."
        )

    # ------------------------------------------------------------------
    # Public Inference API
    # ------------------------------------------------------------------
    def predict(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Run anomaly inference on a single validated telemetry record.

        Parameters
        ----------
        record : dict
            Must contain the 9 feature keys defined in FEATURE_COLS.

        Returns
        -------
        dict | None
            Enriched record with 'anomaly_score' and 'is_anomaly' keys,
            or None if inference could not be performed.
        """
        self.inference_count += 1

        # ---- Degraded mode short-circuit ----
        if self.degraded_mode:
            logger.debug("[ML] Skipping inference (degraded mode).")
            return None

        # ---- Dimensionality / schema guard ----
        try:
            feature_vector = self._extract_features(record)
        except (KeyError, ValueError, TypeError) as exc:
            self.error_count += 1
            logger.error(f"[ML] Feature extraction error (possible data drift): {exc}")
            return None

        # ---- Inference with broad exception catch ----
        try:
            # IsolationForest expects 2D array
            X = feature_vector.reshape(1, -1)

            # Check dimensionality against training
            if X.shape[1] != EXPECTED_N_FEATURES:
                raise ValueError(
                    f"Dimensionality mismatch: input has {X.shape[1]} features, "
                    f"model expects {EXPECTED_N_FEATURES}. This indicates DATA DRIFT."
                )

            # sklearn IsolationForest: decision_function gives anomaly score
            # (negative = more anomalous). We normalize to [0, 1] for consistency.
            raw_score = self.model.decision_function(X)[0]
            # Normalize: decision_function is roughly [-0.5, 0.5] in practice
            # Map to [0, 1] where 1 = highly anomalous
            anomaly_score = 0.5 - raw_score  # heuristic normalization
            anomaly_score = float(np.clip(anomaly_score, 0.0, 1.0))

            # Predict label: -1 = anomaly, 1 = normal
            label = int(self.model.predict(X)[0])
            is_anomaly = (label == -1)

            result = dict(record)
            result["anomaly_score"] = round(anomaly_score, 6)
            result["is_anomaly"] = is_anomaly
            result["ml_status"] = "ok"

            logger.debug(
                f"[ML] Inference OK -> score={anomaly_score:.4f}, anomaly={is_anomaly}"
            )
            return result

        except ValueError as exc:
            # Dimensionality errors are treated as data drift -> critical log
            self.error_count += 1
            logger.critical(f"[ML] DATA DRIFT / Dimensionality error: {exc}")
            return None

        except Exception as exc:
            # Any other unexpected error -> enter degraded mode
            self.error_count += 1
            logger.critical(f"[ML] Unexpected inference error: {exc}")
            self._enter_degraded_mode(f"Inference runtime error: {exc}")
            return None

    def predict_batch(self, records: List[Dict[str, Any]]) -> List[Optional[Dict[str, Any]]]:
        """Batch inference for efficiency. Returns list aligned with input."""
        return [self.predict(r) for r in records]

    # ------------------------------------------------------------------
    # Feature Extraction
    # ------------------------------------------------------------------
    def _extract_features(self, record: Dict[str, Any]) -> np.ndarray:
        """
        Build a NumPy feature vector from a validated record.

        If the record only contains raw telemetry (V, I, P, PF), we compute
        the derived features on-the-fly to match the training schema.
        """
        # If all engineered features are present, use them directly
        if all(col in record for col in FEATURE_COLS):
            return np.array([record[col] for col in FEATURE_COLS], dtype=np.float32)

        # Otherwise, compute derived features from base telemetry
        V = float(record["V"])
        I = float(record["I"])
        P = float(record["P"])
        PF = float(record["PF"])

        S = P / PF if PF > 0.001 else 0.0
        diff_sq = S * S - P * P
        Q = np.sqrt(max(diff_sq, 0.0))

        # For delta features in a single-record context, we default to 0
        # (the model will see this as "no change" which is acceptable for edge inference)
        dP = record.get("delta_P", 0.0)
        dQ = record.get("delta_Q", 0.0)
        var60 = record.get("current_rolling_var_60s", 0.0)

        return np.array([V, I, P, PF, S, Q, dP, dQ, var60], dtype=np.float32)

    # ------------------------------------------------------------------
    # Health / Metrics
    # ------------------------------------------------------------------
    def health(self) -> Dict[str, Any]:
        """Return current service health status."""
        return {
            "status": "degraded" if self.degraded_mode else "healthy",
            "degraded_reason": self.degraded_reason,
            "inference_count": self.inference_count,
            "error_count": self.error_count,
            "model_loaded": self.model is not None,
            "expected_features": EXPECTED_N_FEATURES,
        }


# ---------------------------------------------------------------------------
# Convenience module-level functions
# ---------------------------------------------------------------------------
_service: Optional[MLInferenceService] = None


def get_service(model_path: str = MODEL_PATH) -> MLInferenceService:
    """Lazy initializer for the singleton service."""
    global _service
    if _service is None:
        _service = MLInferenceService(model_path=model_path)
    return _service


def predict(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """One-shot inference using the singleton service."""
    return get_service().predict(record)


def health() -> Dict[str, Any]:
    """One-shot health check using the singleton service."""
    return get_service().health()


# ---------------------------------------------------------------------------
# CLI / Standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 70)
    print("ML INFERENCE SERVICE - SELF TEST")
    print("=" * 70)

    # Test 1: Service initialization (will likely enter degraded mode without a model file)
    svc = get_service()
    print(f"\nHealth: {svc.health()}")

    # Test 2: Simulate a validated record
    test_record = {
        "device_id": "esp32-energy-01",
        "timestamp": 12345678,
        "V": 230.5,
        "I": 2.150,
        "P": 425.30,
        "PF": 0.850,
        "Q": 245.1,
    }

    print(f"\nInput record: {test_record}")
    result = svc.predict(test_record)

    if result:
        print(f"Inference result: {result}")
    else:
        print("Inference skipped (degraded mode or error).")

    # Test 3: Simulate dimensionality drift
    print("\n--- Testing dimensionality drift handling ---")
    drift_record = {
        "device_id": "esp32-energy-01",
        "timestamp": 12345678,
        "V": 230.5,
        "I": 2.150,
        # Missing P and PF -> feature extraction will fail gracefully
    }
    drift_result = svc.predict(drift_record)
    print(f"Drift result: {drift_result}")

    print("\n" + "=" * 70)
    print("Self-test complete.")

