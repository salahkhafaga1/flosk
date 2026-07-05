"""
mqtt_schema_validator.py
========================
Pydantic-based schema validation layer that sits between the MQTT subscriber
and the ML model / time-series database.

Responsibilities:
  1. Validate that incoming telemetry matches the exact expected data types.
  2. Handle missing / corrupted JSON payloads without crashing the pipeline.
  3. Enforce reasonable physical bounds on electrical quantities (V, I, P, PF).
  4. Log validation errors for observability.

Usage:
    from mqtt_schema_validator import validate_payload, ValidationResult
    result = validate_payload(raw_json_string)
    if result.is_valid:
        influx_db.write(result.record)
    else:
        logger.warning(result.error_msg)
"""

import json
import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator, ValidationError

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("SchemaValidator")


# ---------------------------------------------------------------------------
# Pydantic Model
# ---------------------------------------------------------------------------
class EnergyTelemetry(BaseModel):
    """
    Strict schema for an incoming energy telemetry payload.

    Fields
    ------
    device_id : str
        Unique identifier for the sensor node (e.g. IP Address 192.168.1.4, MAC, or custom ID).
    timestamp : int
        Epoch milliseconds or uptime ms from the ESP32.
    V : float
        Voltage in Volts (RMS). Expected range: 100-300 V.
    I : float
        Current in Amperes. Expected range: 0-100 A.
    P : float
        Active Power in Watts. Expected range: 0-30_000 W.
    PF : float
        Power Factor (dimensionless). Expected range: 0.0-1.0.
    Q : float | None
        Reactive Power in VAR (optional, but validated if present).
    alert : bool | None
        Anomaly flag from edge device (optional).
    score : float | None
        Anomaly score from edge device (optional).
    buffered : bool | None
        True if this reading was back-filled from the ESP32 async buffer.
    """

    device_id: str = Field(..., min_length=1, max_length=64)
    timestamp: int = Field(..., ge=0)
    V: float = Field(..., ge=100.0, le=300.0, description="Voltage (V)")
    I: float = Field(..., ge=0.0, le=100.0, description="Current (A)")
    P: float = Field(..., ge=0.0, le=30000.0, description="Active Power (W)")
    PF: float = Field(..., ge=0.0, le=1.0, description="Power Factor")
    Q: Optional[float] = Field(None, ge=0.0, le=30000.0, description="Reactive Power (VAR)")
    alert: Optional[bool] = Field(None)
    score: Optional[float] = Field(None, ge=0.0, le=1.0)
    buffered: Optional[bool] = Field(None)

    @validator("V")
    def validate_voltage(cls, v: float) -> float:
        if v < 180.0 or v > 260.0:
            logger.warning(f"[VALIDATION] Voltage {v}V is outside typical mains range (180-260V).")
        return v

    @validator("I")
    def validate_current_non_negative(cls, i: float) -> float:
        if i < 0:
            raise ValueError("Current cannot be negative.")
        return i

    @validator("PF")
    def validate_pf_range(cls, pf: float) -> float:
        if not (0.0 <= pf <= 1.0):
            raise ValueError("Power Factor must be between 0.0 and 1.0.")
        return pf


# ---------------------------------------------------------------------------
# Validation Result Wrapper
# ---------------------------------------------------------------------------
class ValidationResult:
    """Lightweight result object to avoid exceptions in hot path."""

    def __init__(
        self,
        is_valid: bool,
        record: Optional[Dict[str, Any]] = None,
        error_msg: Optional[str] = None,
    ):
        self.is_valid = is_valid
        self.record = record
        self.error_msg = error_msg

    def __repr__(self) -> str:
        if self.is_valid:
            return f"ValidationResult(valid=True, device={self.record.get('device_id')})"
        return f"ValidationResult(valid=False, error='{self.error_msg}')"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def validate_payload(raw_payload: str) -> ValidationResult:
    """
    Validate a raw JSON string against the EnergyTelemetry schema.

    Parameters
    ----------
    raw_payload : str
        The raw JSON payload received from the MQTT broker.

    Returns
    -------
    ValidationResult
        is_valid=True  -> record contains the parsed dict.
        is_valid=False -> error_msg contains a human-readable reason.
    """
    # ---- 1. JSON parse step ----
    try:
        parsed = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        logger.error(f"[VALIDATION] Malformed JSON: {exc}")
        return ValidationResult(
            is_valid=False,
            error_msg=f"Malformed JSON: {exc}",
        )
    except Exception as exc:
        logger.error(f"[VALIDATION] Unexpected error during JSON parsing: {exc}")
        return ValidationResult(
            is_valid=False,
            error_msg=f"Unexpected JSON parse error: {exc}",
        )

    # ---- 2. Schema validation step ----
    try:
        telemetry = EnergyTelemetry(**parsed)
    except ValidationError as exc:
        # Pydantic gives us detailed error messages
        errors = exc.errors()
        # Build a concise error string
        error_parts = []
        for err in errors:
            loc = ".".join(str(x) for x in err["loc"])
            error_parts.append(f"{loc}: {err['msg']}")
        error_str = "; ".join(error_parts)
        logger.warning(f"[VALIDATION] Schema violation: {error_str} | raw={raw_payload[:200]}")
        return ValidationResult(
            is_valid=False,
            error_msg=f"Schema violation: {error_str}",
        )
    except Exception as exc:
        logger.error(f"[VALIDATION] Unexpected Pydantic error: {exc}")
        return ValidationResult(
            is_valid=False,
            error_msg=f"Unexpected validation error: {exc}",
        )

    # ---- 3. Success ----
    logger.debug(f"[VALIDATION] OK -> {telemetry.device_id} @ {telemetry.timestamp}")
    return ValidationResult(
        is_valid=True,
        record=telemetry.model_dump(),
    )


# ---------------------------------------------------------------------------
# CLI / Standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Valid payload
    valid_json = json.dumps({
        "device_id": "esp32-energy-01",
        "timestamp": 12345678,
        "V": 230.5,
        "I": 2.150,
        "P": 425.30,
        "PF": 0.850,
        "Q": 245.1,
        "alert": True,
        "score": 0.6234,
    })

    # Corrupted payload (missing required field V)
    corrupted_json = json.dumps({
        "device_id": "esp32-energy-01",
        "timestamp": 12345678,
        "I": 2.150,
        "P": 425.30,
        "PF": 0.850,
    })

    # Out-of-bounds payload
    oob_json = json.dumps({
        "device_id": "esp32-energy-01",
        "timestamp": 12345678,
        "V": 500.0,   # out of bounds
        "I": 2.150,
        "P": 425.30,
        "PF": 1.5,    # out of bounds
    })

    # Completely invalid JSON
    garbage = "{this is not json}"

    test_cases = [
        ("VALID", valid_json),
        ("CORRUPTED (missing V)", corrupted_json),
        ("OUT_OF_BOUNDS", oob_json),
        ("GARBAGE", garbage),
    ]

    print("=" * 70)
    print("MQTT SCHEMA VALIDATOR - SELF TEST")
    print("=" * 70)

    for name, payload in test_cases:
        print(f"\n--- Test: {name} ---")
        result = validate_payload(payload)
        print(f"Result: {result}")
        if result.is_valid:
            print(f"Parsed record: {result.record}")
        else:
            print(f"Rejection reason: {result.error_msg}")

    print("\n" + "=" * 70)
    print("Self-test complete.")

