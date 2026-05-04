"""
rest_simulator.py
=================
Alternative simulator that uses the REST API (/api/ingest) instead of MQTT.
Use this when an MQTT broker is not available.

Usage:
    python rest_simulator.py
"""

import json
import time
import random
import requests
import os

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
API_URL = "http://localhost/api/ingest"
DEVICE_ID = os.environ.get("DEVICE_ID", "192.168.1.4")
PUBLISH_INTERVAL = 1.0  # seconds

# ---------------------------------------------------------------------------
# Simulation State
# ---------------------------------------------------------------------------
base_voltage = 230.0       # V
base_current = 2.5         # A
base_pf = 0.85             # Power factor
anomaly_counter = 0

def generate_telemetry() -> dict:
    global anomaly_counter
    anomaly_counter += 1
    inject_anomaly = (anomaly_counter % 35 == 0)

    if inject_anomaly:
        voltage = round(random.uniform(260.0, 280.0), 1)
        current = round(random.uniform(8.0, 12.0), 3)
        pf = round(random.uniform(0.50, 0.65), 3)
        alert = True
        score = round(random.uniform(0.55, 0.85), 4)
    else:
        voltage = round(base_voltage + random.uniform(-3.0, 3.0), 1)
        current = round(base_current + random.uniform(-0.5, 0.5), 3)
        pf = round(base_pf + random.uniform(-0.03, 0.03), 3)
        pf = max(0.0, min(1.0, pf))
        alert = False
        score = round(random.uniform(0.10, 0.35), 4)

    apparent_power = round(voltage * current, 1)
    active_power = round(apparent_power * pf, 1)
    reactive_power = round((apparent_power ** 2 - active_power ** 2) ** 0.5, 1) if apparent_power > active_power else 0.0
    active_power = max(0.0, min(30000.0, active_power))

    return {
        "device_id": DEVICE_ID,
        "timestamp": int(time.time() * 1000),
        "V": voltage,
        "I": current,
        "P": active_power,
        "PF": pf,
        "Q": reactive_power,
        "alert": alert,
        "score": score,
    }

def main():
    print(f"[REST-SIM] Starting simulator for {DEVICE_ID}...")
    print(f"[REST-SIM] Target API: {API_URL}")
    
    try:
        while True:
            payload = generate_telemetry()
            try:
                res = requests.post(API_URL, json=payload, timeout=2)
                if res.ok:
                    print(f"[REST-SIM] Sent -> V={payload['V']}V I={payload['I']}A P={payload['P']}W")
                else:
                    print(f"[REST-SIM] Failed -> {res.status_code} {res.text}")
            except Exception as e:
                print(f"[REST-SIM] Connection error: {e}")
            
            time.sleep(PUBLISH_INTERVAL)
    except KeyboardInterrupt:
        print("[REST-SIM] Stopped.")

if __name__ == "__main__":
    main()
