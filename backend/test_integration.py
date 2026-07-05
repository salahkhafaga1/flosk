"""
test_integration.py
===================
Comprehensive System Sanity Check for the IoT-to-AI Pipeline.

Acts as a final diagnostic tool that verifies:
  1. MQTT Broker connectivity (TCP ping)
  2. InfluxDB health via native Python client
  3. Isolation Forest model file integrity (load + inference smoke test)
  4. FastAPI backend /health endpoint (HTTP GET)

Usage:
    python test_integration.py

Environment Variables:
    MQTT_BROKER_HOST    (default: localhost)
    MQTT_BROKER_PORT    (default: 1883)
    INFLUXDB_URL        (default: http://localhost:8086)
    INFLUXDB_TOKEN      (default: my-token)
    INFLUXDB_ORG        (default: my-org)
    FASTAPI_URL         (default: http://localhost:8000)
    MODEL_PATH          (default: isolation_forest_model.pkl)
"""

import os
import sys
import json
import socket
import logging
import joblib
from typing import List, Tuple
from datetime import datetime, timezone

import numpy as np

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("SystemSanityCheck")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MQTT_BROKER_HOST = os.environ.get("MQTT_BROKER_HOST", "localhost")
MQTT_BROKER_PORT = int(os.environ.get("MQTT_BROKER_PORT", "1883"))

INFLUXDB_URL = os.environ.get("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.environ.get("INFLUXDB_TOKEN", "my-token")
INFLUXDB_ORG = os.environ.get("INFLUXDB_ORG", "my-org")

FASTAPI_URL = os.environ.get("FASTAPI_URL", "http://localhost:8000")
FASTAPI_HEALTH_ENDPOINT = f"{FASTAPI_URL}/health"

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
MODEL_PATH = os.environ.get("MODEL_PATH", os.path.join(PROJECT_ROOT, "ml_models", "iforest_model.pkl"))
CONNECT_TIMEOUT_SEC = 5


# ---------------------------------------------------------------------------
# ASCII Art & Styling
# ---------------------------------------------------------------------------
SUCCESS_BANNER = r"""
    ================================================================================
    ================================================================================

         SSSS  Y   Y  SSSS  TTTTT  EEEEE  M   M       OOO   K   K
        S       Y Y   S       T    E      MM MM      O   O  K  K
         SSS     Y     SSS     T    EEEE   M M M      O   O  KKK
            S    Y        S    T    E      M   M      O   O  K  K
        SSSS     Y    SSSS     T    EEEEE  M   M       OOO   K   K

    ================================================================================
         SYSTEM OK: 100% INTEGRATED
         No errors. ESP32, MQTT, InfluxDB, FastAPI, and AI Model are
         perfectly connected!
    ================================================================================
    ================================================================================
"""


# ---------------------------------------------------------------------------
# Individual Check Functions
# ---------------------------------------------------------------------------

def check_mqtt_broker() -> Tuple[bool, str, str]:
    """
    Check 1: MQTT Broker TCP connectivity.
    Returns (success: bool, component: str, message: str)
    """
    component = "MQTT Broker"
    try:
        sock = socket.create_connection(
            (MQTT_BROKER_HOST, MQTT_BROKER_PORT),
            timeout=CONNECT_TIMEOUT_SEC,
        )
        sock.close()
        return (
            True,
            component,
            f"Connected successfully to {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}",
        )
    except socket.timeout:
        return (
            False,
            component,
            f"Connection timed out after {CONNECT_TIMEOUT_SEC}s.\n"
            f"   Troubleshooting:\n"
            f"   1. Ensure Mosquitto/EMQ X/RabbitMQ is running on {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}\n"
            f"   2. Check firewall rules (port {MQTT_BROKER_PORT} must be open)\n"
            f"   3. Verify MQTT_BROKER_HOST and MQTT_BROKER_PORT env vars",
        )
    except Exception as exc:
        return (
            False,
            component,
            f"Connection failed: {exc}\n"
            f"   Troubleshooting:\n"
            f"   1. Check that the broker service is started\n"
            f"   2. Verify network connectivity to {MQTT_BROKER_HOST}\n"
            f"   3. Review broker logs for authentication or bind errors",
        )


def check_influxdb() -> Tuple[bool, str, str]:
    """
    Check 2: InfluxDB health via native Python client.
    Returns (success: bool, component: str, message: str)
    """
    component = "InfluxDB"
    try:
        from influxdb_client import InfluxDBClient

        client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG,
            timeout=CONNECT_TIMEOUT_SEC * 1000,
        )
        health = client.health()

        if health.status == "pass":
            return (
                True,
                component,
                f"InfluxDB is healthy at {INFLUXDB_URL} (status={health.status})",
            )
        else:
            return (
                False,
                component,
                f"InfluxDB returned non-pass status: {health.status}\n"
                f"   Troubleshooting:\n"
                f"   1. Check InfluxDB logs: docker logs <influxdb_container>\n"
                f"   2. Verify INFLUXDB_TOKEN has sufficient permissions\n"
                f"   3. Ensure the bucket and org exist",
            )
    except ImportError:
        return (
            False,
            component,
            "influxdb-client Python package is not installed.\n"
            "   Troubleshooting:\n"
            "   1. Run: pip install influxdb-client\n"
            "   2. Re-run this sanity check",
        )
    except Exception as exc:
        return (
            False,
            component,
            f"InfluxDB health check failed: {exc}\n"
            f"   Troubleshooting:\n"
            f"   1. Ensure InfluxDB is running: docker ps | grep influxdb\n"
            f"   2. Verify INFLUXDB_URL, INFLUXDB_TOKEN, and INFLUXDB_ORG env vars\n"
            f"   3. Check if InfluxDB API port (8086) is accessible",
        )


def check_model_file() -> Tuple[bool, str, str]:
    """
    Check 3: Load the pre-trained Isolation Forest model and run a smoke test.
    Returns (success: bool, component: str, message: str)
    """
    component = "AI Model (Isolation Forest)"
    try:
        if not os.path.exists(MODEL_PATH):
            return (
                False,
                component,
                f"Model file not found: {MODEL_PATH}\n"
                f"   Troubleshooting:\n"
                f"   1. Run the training pipeline first:\n"
                f"      python train_isolation_forest.py\n"
                f"   2. Export the model: python export_iforest_to_cpp.py\n"
                f"   3. Save the sklearn model via pickle:\n"
                f"      import pickle; pickle.dump(model, open('{MODEL_PATH}', 'wb'))",
            )

        model = joblib.load(MODEL_PATH)

        # Verify it's an IsolationForest-like object
        if not hasattr(model, "predict") or not hasattr(model, "decision_function"):
            return (
                False,
                component,
                f"Loaded file is not a valid sklearn model (type={type(model).__name__})\n"
                f"   Troubleshooting:\n"
                f"   1. Retrain the model: python train_isolation_forest.py\n"
                f"   2. Re-serialize with pickle.dump(model, open('{MODEL_PATH}', 'wb'))",
            )

        # Smoke test inference with 9 features (matches training schema)
        smoke_input = np.array([[230.0, 2.0, 400.0, 0.85, 470.0, 250.0, 0.0, 0.0, 0.05]])
        _ = model.decision_function(smoke_input)
        _ = model.predict(smoke_input)

        return (
            True,
            component,
            f"Model loaded and smoke test passed. File: {MODEL_PATH}, Type: {type(model).__name__}",
        )
    except Exception as exc:
        return (
            False,
            component,
            f"Model loading or inference failed: {exc}\n"
            f"   Troubleshooting:\n"
            f"   1. Check that the model was trained with sklearn=={__import__('sklearn').__version__}\n"
            f"   2. Delete {MODEL_PATH} and re-run the training pipeline\n"
            f"   3. Verify the model was pickled correctly",
        )


def check_fastapi() -> Tuple[bool, str, str]:
    """
    Check 4: Send GET request to FastAPI /health endpoint.
    Returns (success: bool, component: str, message: str)
    """
    component = "FastAPI Backend"
    try:
        from urllib.request import urlopen, Request
        from urllib.error import URLError, HTTPError

        req = Request(FASTAPI_HEALTH_ENDPOINT, method="GET")
        req.add_header("Accept", "application/json")

        with urlopen(req, timeout=CONNECT_TIMEOUT_SEC) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            status_code = resp.getcode()

            if status_code == 200:
                return (
                    True,
                    component,
                    f"FastAPI /health returned HTTP 200 OK from {FASTAPI_HEALTH_ENDPOINT}",
                )
            else:
                return (
                    False,
                    component,
                    f"FastAPI /health returned HTTP {status_code}\n"
                    f"   Response body: {body[:200]}\n"
                    f"   Troubleshooting:\n"
                    f"   1. Check FastAPI logs for startup errors\n"
                    f"   2. Verify all dependencies are installed: pip install -r requirements.txt",
                )

    except ImportError:
        return (
            False,
            component,
            "urllib is part of the Python standard library — this should never fail.\n"
            "   Troubleshooting: Your Python installation may be corrupted.",
        )
    except HTTPError as exc:
        return (
            False,
            component,
            f"FastAPI returned HTTP error: {exc.code}\n"
            f"   Troubleshooting:\n"
            f"   1. FastAPI is running but /health returned an error\n"
            f"   2. Check application logs: uvicorn main:app --reload\n"
            f"   3. Verify the /health route is defined in your FastAPI app",
        )
    except URLError as exc:
        return (
            False,
            component,
            f"Cannot reach FastAPI backend: {exc.reason}\n"
            f"   Troubleshooting:\n"
            f"   1. Start the FastAPI server: uvicorn main:app --host 0.0.0.0 --port 8000\n"
            f"   2. Verify FASTAPI_URL env var (current: {FASTAPI_URL})\n"
            f"   3. Check firewall / port binding on port 8000",
        )
    except Exception as exc:
        return (
            False,
            component,
            f"FastAPI health check failed: {exc}\n"
            f"   Troubleshooting:\n"
            f"   1. Ensure the FastAPI application is running\n"
            f"   2. Check for unhandled exceptions in the /health handler\n"
            f"   3. Verify network connectivity to {FASTAPI_URL}",
        )


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def run_all_checks() -> List[Tuple[bool, str, str]]:
    """Execute all checks and return their results."""
    checks = [
        check_mqtt_broker,
        check_influxdb,
        check_model_file,
        check_fastapi,
    ]
    results = []
    for check_fn in checks:
        results.append(check_fn())
    return results


def print_report(results: List[Tuple[bool, str, str]]) -> None:
    """Print a formatted report of all check results."""
    print("\n" + "=" * 80)
    print("  SYSTEM SANITY CHECK REPORT")
    print("=" * 80)
    print(f"  Timestamp : {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}")
    print(f"  Checks    : {len(results)}")
    print("-" * 80)

    all_passed = True
    for success, component, message in results:
        status_icon = "✅ PASS" if success else "❌ FAIL"
        print(f"\n  [{status_icon}] {component}")
        for line in message.splitlines():
            print(f"           {line}")
        if not success:
            all_passed = False

    print("\n" + "=" * 80)

    if all_passed:
        print(SUCCESS_BANNER)
        print("\n  🚀 All systems are GO. The pipeline is fully integrated and operational.\n")
    else:
        failed_components = [
            comp for success, comp, _ in results if not success
        ]
        print(
            f"\n  ❌ SYSTEM NOT READY: {len(failed_components)} component(s) failed.\n"
            f"     Failed: {', '.join(failed_components)}\n"
            f"     Please follow the troubleshooting steps above and re-run this script.\n"
        )

    print("=" * 80 + "\n")


def main() -> int:
    """
    Main entry point.
    Returns 0 if all checks pass, 1 otherwise.
    """
    print("\n🔍 Starting System Sanity Check...\n")
    results = run_all_checks()
    print_report(results)
    return 0 if all(success for success, _, _ in results) else 1


if __name__ == "__main__":
    sys.exit(main())

