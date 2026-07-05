"""
system_health_watchdog.py
=========================
Lightweight "System Watchdog" that continuously pings the critical infrastructure
components of the IoT-to-AI pipeline and reports their health status.

Components Monitored:
  1. MQTT Broker      -> TCP socket connection test
  2. InfluxDB         -> HTTP ping to /ping or /health endpoint
  3. ML API Service   -> HTTP GET to the inference health endpoint

Features:
  - Non-blocking async checks using threading.
  - Configurable check intervals per component.
  - JSON / console output suitable for external monitoring (e.g., Prometheus, Grafana).
  - Exit code 1 if any critical component is down (useful for Docker HEALTHCHECK).

Usage:
    python system_health_watchdog.py

Environment Variables:
    MQTT_BROKER_HOST    (default: localhost)
    MQTT_BROKER_PORT    (default: 1883)
    INFLUXDB_URL        (default: http://localhost:8086)
    ML_API_URL          (default: http://localhost:5000)
    CHECK_INTERVAL_SEC  (default: 30)
"""

import os
import sys
import time
import json
import socket
import logging
import threading
from typing import Dict, Any
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("SystemWatchdog")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MQTT_BROKER_HOST = os.environ.get("MQTT_BROKER_HOST", "localhost")
MQTT_BROKER_PORT = int(os.environ.get("MQTT_BROKER_PORT", "1883"))

INFLUXDB_URL = os.environ.get("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_HEALTH_ENDPOINT = f"{INFLUXDB_URL}/health"

ML_API_URL = os.environ.get("ML_API_URL", "http://localhost:5000")
ML_API_HEALTH_ENDPOINT = f"{ML_API_URL}/health"

CHECK_INTERVAL_SEC = int(os.environ.get("CHECK_INTERVAL_SEC", "30"))
CONNECT_TIMEOUT_SEC = 5

# ---------------------------------------------------------------------------
# Health Check Functions
# ---------------------------------------------------------------------------

def check_mqtt_broker(host: str, port: int) -> Dict[str, Any]:
    """
    Check MQTT broker connectivity by attempting a TCP socket connection.
    Returns a status dict compatible with the unified health format.
    """
    start = time.time()
    try:
        sock = socket.create_connection((host, port), timeout=CONNECT_TIMEOUT_SEC)
        sock.close()
        latency_ms = (time.time() - start) * 1000
        return {
            "component": "mqtt_broker",
            "status": "UP",
            "latency_ms": round(latency_ms, 2),
            "host": host,
            "port": port,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
    except socket.timeout:
        return {
            "component": "mqtt_broker",
            "status": "DOWN",
            "error": "Connection timeout",
            "host": host,
            "port": port,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
    except Exception as exc:
        return {
            "component": "mqtt_broker",
            "status": "DOWN",
            "error": str(exc),
            "host": host,
            "port": port,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }


def check_influxdb(url: str) -> Dict[str, Any]:
    """
    Check InfluxDB health via its HTTP health endpoint.
    """
    start = time.time()
    try:
        req = Request(url, method="GET")
        req.add_header("Accept", "application/json")
        with urlopen(req, timeout=CONNECT_TIMEOUT_SEC) as resp:
            latency_ms = (time.time() - start) * 1000
            body = resp.read().decode("utf-8", errors="ignore")
            # InfluxDB /health returns JSON like {"status":"pass"}
            try:
                payload = json.loads(body)
                db_status = payload.get("status", "unknown")
            except json.JSONDecodeError:
                db_status = "unknown"

            return {
                "component": "influxdb",
                "status": "UP" if db_status == "pass" else "DEGRADED",
                "latency_ms": round(latency_ms, 2),
                "db_status": db_status,
                "url": url,
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }
    except HTTPError as exc:
        return {
            "component": "influxdb",
            "status": "DOWN",
            "error": f"HTTP {exc.code}",
            "url": url,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
    except URLError as exc:
        return {
            "component": "influxdb",
            "status": "DOWN",
            "error": str(exc.reason),
            "url": url,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
    except Exception as exc:
        return {
            "component": "influxdb",
            "status": "DOWN",
            "error": str(exc),
            "url": url,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }


def check_ml_api(url: str) -> Dict[str, Any]:
    """
    Check ML API health via its HTTP health endpoint.
    """
    start = time.time()
    try:
        req = Request(url, method="GET")
        req.add_header("Accept", "application/json")
        with urlopen(req, timeout=CONNECT_TIMEOUT_SEC) as resp:
            latency_ms = (time.time() - start) * 1000
            body = resp.read().decode("utf-8", errors="ignore")
            try:
                payload = json.loads(body)
                ml_status = payload.get("status", "unknown")
            except json.JSONDecodeError:
                ml_status = "unknown"

            return {
                "component": "ml_api",
                "status": "UP" if ml_status == "healthy" else "DEGRADED",
                "latency_ms": round(latency_ms, 2),
                "ml_status": ml_status,
                "url": url,
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }
    except HTTPError as exc:
        return {
            "component": "ml_api",
            "status": "DOWN",
            "error": f"HTTP {exc.code}",
            "url": url,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
    except URLError as exc:
        return {
            "component": "ml_api",
            "status": "DOWN",
            "error": str(exc.reason),
            "url": url,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
    except Exception as exc:
        return {
            "component": "ml_api",
            "status": "DOWN",
            "error": str(exc),
            "url": url,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }


# ---------------------------------------------------------------------------
# Watchdog Orchestrator
# ---------------------------------------------------------------------------

class SystemWatchdog:
    """
    Continuous health monitor that runs checks in parallel threads.
    """

    def __init__(
        self,
        mqtt_host: str = MQTT_BROKER_HOST,
        mqtt_port: int = MQTT_BROKER_PORT,
        influx_url: str = INFLUXDB_HEALTH_ENDPOINT,
        ml_url: str = ML_API_HEALTH_ENDPOINT,
        interval_sec: int = CHECK_INTERVAL_SEC,
    ):
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.influx_url = influx_url
        self.ml_url = ml_url
        self.interval_sec = interval_sec
        self.running = False
        self.latest_results: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def _run_checks(self) -> None:
        """Execute all health checks concurrently."""
        results = {}

        # Threaded execution for non-blocking behaviour
        threads = []

        def _check_and_store(check_fn, key, *args, **kwargs):
            results[key] = check_fn(*args, **kwargs)

        t1 = threading.Thread(
            target=_check_and_store,
            args=(check_mqtt_broker, "mqtt_broker", self.mqtt_host, self.mqtt_port),
        )
        t2 = threading.Thread(
            target=_check_and_store,
            args=(check_influxdb, "influxdb", self.influx_url),
        )
        t3 = threading.Thread(
            target=_check_and_store,
            args=(check_ml_api, "ml_api", self.ml_url),
        )

        threads.extend([t1, t2, t3])
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=CONNECT_TIMEOUT_SEC + 2)

        with self._lock:
            self.latest_results = results

    def _report(self) -> None:
        """Log the latest health results in a structured format."""
        with self._lock:
            snapshot = dict(self.latest_results)

        overall_up = all(
            r.get("status") == "UP" for r in snapshot.values()
        )

        report = {
            "watchdog_timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "overall_status": "HEALTHY" if overall_up else "DEGRADED",
            "checks": snapshot,
        }

        # Pretty-print JSON to stdout for log aggregation
        print(json.dumps(report, indent=2))

        if overall_up:
            logger.info("[WATCHDOG] All systems operational.")
        else:
            down_components = [
                name for name, r in snapshot.items() if r.get("status") != "UP"
            ]
            logger.warning(
                f"[WATCHDOG] DEGRADED: {', '.join(down_components)} are not healthy."
            )

    def run_once(self) -> Dict[str, Dict[str, Any]]:
        """Run a single health check cycle and return results."""
        self._run_checks()
        self._report()
        return self.latest_results

    def run_continuous(self) -> None:
        """Run health checks in an infinite loop until interrupted."""
        self.running = True
        logger.info(
            f"[WATCHDOG] Starting continuous monitoring every {self.interval_sec}s..."
        )
        logger.info(
            f"[WATCHDOG] Targets: MQTT={self.mqtt_host}:{self.mqtt_port}, "
            f"InfluxDB={self.influx_url}, ML_API={self.ml_url}"
        )

        try:
            while self.running:
                self.run_once()
                time.sleep(self.interval_sec)
        except KeyboardInterrupt:
            logger.info("[WATCHDOG] Interrupted by user. Shutting down.")
            self.running = False

    def stop(self) -> None:
        """Signal the continuous loop to stop."""
        self.running = False


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main() -> int:
    """
    Main entry point. Returns 0 if all checks pass, 1 otherwise.
    """
    watchdog = SystemWatchdog()
    results = watchdog.run_once()

    any_down = any(
        r.get("status") != "UP" for r in results.values()
    )

    return 1 if any_down else 0


if __name__ == "__main__":
    # If RUN_ONCE is set, do a single check and exit with appropriate code.
    # Otherwise, run continuously.
    if os.environ.get("RUN_ONCE", "false").lower() == "true":
        sys.exit(main())
    else:
        watchdog = SystemWatchdog()
        watchdog.run_continuous()

