"""
mqtt_simulator.py
=================
Simulates an ESP32 + PZEM-004T energy sensor publishing telemetry over MQTT.

Use this when your physical ESP32 is not connected, to verify that the
FastAPI backend and dashboard are receiving and displaying data correctly.

What it does:
  - Connects to the local MQTT broker (default: localhost:1883)
  - Publishes a realistic telemetry payload every 1 second
  - Generates slight random fluctuations around typical mains values
  - Occasionally injects an anomaly (voltage spike) to test alerting

Run:
    python mqtt_simulator.py

The simulator publishes to the same topic the backend subscribes to:
    home/energy/alerts

Payload keys (must match mqtt_schema_validator.py exactly):
    device_id, timestamp, V, I, P, PF, Q, alert, score
"""

import os
import json
import time
import random
import logging

# Optional dependency: paho-mqtt
try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("[ERROR] paho-mqtt is not installed.")
    print("[FIX]   Run: pip install paho-mqtt")
    raise SystemExit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "home/energy/alerts"
# Any unique string works (MAC, IP Address like 192.168.1.4, or custom slug)
DEVICE_ID = os.environ.get("DEVICE_ID", "192.168.1.4")
PUBLISH_INTERVAL = 1.0  # seconds

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("MQTTSimulator")

# ---------------------------------------------------------------------------
# Simulation State
# ---------------------------------------------------------------------------
base_voltage = 230.0       # V
base_current = 2.5         # A
base_pf = 0.85             # Power factor
anomaly_counter = 0


def generate_telemetry() -> dict:
    """
    Generate a realistic energy telemetry payload.

    Normal operating ranges:
        Voltage : 220-240 V (±10V fluctuation)
        Current : 1.0-5.0 A (±1.5A fluctuation)
        PF      : 0.80-0.95

    Anomaly injection:
        Every ~30 seconds, inject a voltage spike to trigger the anomaly alert.
    """
    global anomaly_counter
    anomaly_counter += 1

    # Decide if this reading should be an anomaly
    inject_anomaly = (anomaly_counter % 35 == 0)  # every 35th reading (~35s)

    if inject_anomaly:
        # Voltage spike anomaly
        voltage = round(random.uniform(260.0, 280.0), 1)
        current = round(random.uniform(8.0, 12.0), 3)
        pf = round(random.uniform(0.50, 0.65), 3)
        alert = True
        score = round(random.uniform(0.55, 0.85), 4)
        logger.warning("[SIM] INJECTING ANOMALY — Voltage spike!")
    else:
        # Normal fluctuation
        voltage = round(base_voltage + random.uniform(-3.0, 3.0), 1)
        current = round(base_current + random.uniform(-0.5, 0.5), 3)
        pf = round(base_pf + random.uniform(-0.03, 0.03), 3)
        # Clamp PF to valid range
        pf = max(0.0, min(1.0, pf))
        alert = False
        score = round(random.uniform(0.10, 0.35), 4)

    # Derived quantities
    apparent_power = round(voltage * current, 1)          # S = V * I
    active_power = round(apparent_power * pf, 1)          # P = S * PF
    reactive_power = round(
        (apparent_power ** 2 - active_power ** 2) ** 0.5, 1
    ) if apparent_power > active_power else 0.0

    # Pydantic validator expects P in range 0-30000, so ensure it fits
    active_power = max(0.0, min(30000.0, active_power))

    payload = {
        "device_id": DEVICE_ID,
        "timestamp": int(time.time() * 1000),  # epoch ms
        "V": voltage,
        "I": current,
        "P": active_power,
        "PF": pf,
        "Q": reactive_power,
        "alert": alert,
        "score": score,
    }

    return payload


# ---------------------------------------------------------------------------
# MQTT Callbacks
# ---------------------------------------------------------------------------
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info(f"[MQTT] Connected to broker at {MQTT_BROKER}:{MQTT_PORT}")
    else:
        logger.error(f"[MQTT] Connection failed, code={rc}")


def on_disconnect(client, userdata, rc):
    logger.info(f"[MQTT] Disconnected (rc={rc}). Will auto-reconnect...")


# ---------------------------------------------------------------------------
# Main Loop
# ---------------------------------------------------------------------------
def main():
    client = mqtt.Client(client_id=DEVICE_ID)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    logger.info("[SIM] Starting MQTT Simulator...")
    logger.info(f"[SIM] Target topic : {MQTT_TOPIC}")
    logger.info(f"[SIM] Broker       : {MQTT_BROKER}:{MQTT_PORT}")
    logger.info(f"[SIM] Publish rate : {PUBLISH_INTERVAL}s")

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
    except Exception as exc:
        logger.error(f"[MQTT] Could not connect to broker: {exc}")
        logger.error("[HINT] Is Mosquitto running?  Start it with: mosquitto -v")
        raise SystemExit(1)

    try:
        while True:
            payload = generate_telemetry()
            json_payload = json.dumps(payload)

            result = client.publish(MQTT_TOPIC, json_payload, qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(
                    f"[SIM] Published -> V={payload['V']}V I={payload['I']}A "
                    f"P={payload['P']}W PF={payload['PF']} "
                    f"Alert={'YES' if payload['alert'] else 'no'}"
                )
            else:
                logger.warning(f"[SIM] Publish failed, rc={result.rc}")

            time.sleep(PUBLISH_INTERVAL)

    except KeyboardInterrupt:
        logger.info("[SIM] Shutdown requested by user.")
    finally:
        client.loop_stop()
        client.disconnect()
        logger.info("[SIM] Disconnected. Goodbye!")


if __name__ == "__main__":
    main()

