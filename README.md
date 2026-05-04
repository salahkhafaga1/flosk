# Smart Home Energy Monitoring System

> **Version:** 3.0 — B2C SaaS with RTL Arabic Support  
> **Tech Stack:** ESP32 (C++) → MQTT → FastAPI (Python) → SQLite → WebSocket → HTML/JS Dashboard  
> **Goal:** Real-time energy anomaly detection with ML-powered edge inference, cloud visualization, and multi-tenant device claiming

---

## 📁 Project Structure (Organized)

```
GProject/
│
├── 📁 backend/                          # FastAPI servers and services
│   ├── main.py                          # Main API + WebSocket + MQTT + Auth
│   ├── database.py                      # SQLAlchemy models (User, Device, Appliance)
│   ├── mqtt_schema_validator.py         # Validate JSON payloads from ESP32
│   ├── ml_inference_service.py          # Isolation Forest ML wrapper
│   ├── system_health_watchdog.py        # Monitor MQTT, InfluxDB, FastAPI health
│   ├── test_integration.py              # End-to-end system test
│   └── mqtt_simulator.py                # Simulate MQTT messages for testing
│
├── 📁 frontend/                         # Frontend UI (HTML/JS/CSS)
│   ├── static/
│   │   ├── index.html                   # Dashboard: metric cards, Chart.js, telemetry log
│   │   ├── landing.html                 # Premium RTL Arabic landing page
│   │   ├── login.html                   # JWT auth page (login/register)
│   │   ├── claim.html                   # Device claiming flow (MAC input + guide)
│   │   ├── onboarding.html              # Interactive onboarding guide
│   │   ├── app.js                       # WebSocket client + auth guard + device filtering
│   │   ├── dashboard.js                 # Dashboard logic and rendering
│   │   └── style.css                    # Dark theme + RTL support
│   └── execute_command.js               # Command execution script
│
├── 📁 firmware/                         # ESP32 firmware (C++)
│   ├── ESP32_EnergyAnomalyDetector.ino  # Basic firmware (single-core)
│   ├── ESP32_EnergyAnomalyDetector_v2.ino # Production firmware (dual-core + WDT + buffer)
│   ├── IsolationForestModel.h           # C++ Isolation Forest model (auto-generated)
│   ├── RobustScalerParams.h             # C++ scaler parameters (auto-generated)
│   └── platformio.ini                   # PlatformIO build configuration
│
├── 📁 ml_models/                        # Training & export scripts
│   ├── train_isolation_forest.py        # Train Isolation Forest model
│   ├── feature_engineering.py           # Feature extraction (deltas, rolling variance)
│   ├── preprocess_energy.py             # Data cleaning & normalization
│   ├── inject_anomalies.py              # Synthetic anomaly injection
│   ├── export_iforest_to_cpp.py         # Export model to C++ header
│   └── export_scaler_to_cpp.py          # Export scaler params to C++ header
│
├── 📁 data/                             # Data files
│   └── sample_energy_data.csv           # Example dataset for training
│
├── 📁 config/                           # Configuration files
│   └── requirements.txt                 # Python dependencies (pip install -r)
│
├── 📁 docs/                             # Documentation
│   ├── PROJECT_GUIDE.md                 # Comprehensive project guide
│   ├── ENV_SETUP_GUIDE.md               # Environment setup instructions
│   └── TODO.md                          # Remaining tasks
│
├── 📁 scripts/                          # Automation & setup
│   └── setup_vscode_esp32.ps1           # Auto-fix ESP32 paths (PowerShell)
│
├── 📁 .vscode/                          # VS Code configuration
│   └── c_cpp_properties.json            # IntelliSense config for ESP32
│
├── 📄 README_AR.md                      # README in Arabic
├── 📄 README.md                         # This file (in English)
├── 📄 .gitignore                        # Exclude temp files from Git
└── 📄 energy_monitor.db                 # SQLite database file

```

---

## 📌 Directory Explanations

### 🔷 **backend/** - Backend Server & Services

**Purpose:** All Python server-side code

| File | Purpose |
|------|---------|
| `main.py` | FastAPI application server with REST API, WebSocket, MQTT client, JWT auth |
| `database.py` | SQLAlchemy ORM models for User, Device, Appliance tables |
| `mqtt_schema_validator.py` | Pydantic validators for MQTT message payloads from ESP32 |
| `ml_inference_service.py` | Loads and runs Isolation Forest model predictions with fallback logic |
| `system_health_watchdog.py` | Monitors health of MQTT broker, InfluxDB, FastAPI server |
| `test_integration.py` | End-to-end system integration tests |
| `mqtt_simulator.py` | Simulates ESP32 telemetry messages for testing |

**Commands:**
```bash
# Start the server (with auto-reload)
cd backend
uvicorn main:app --reload

# Run integration tests
python test_integration.py

# Check system health
python system_health_watchdog.py
```

---

### 🔷 **frontend/** - User Interface

**Purpose:** HTML, JavaScript, CSS files served by FastAPI

| File | Purpose |
|------|---------|
| `static/index.html` | Main dashboard with metric cards, charts, telemetry logs |
| `static/landing.html` | Premium B2C landing page with RTL Arabic support |
| `static/login.html` | JWT authentication page (login/register with glass-morphism UI) |
| `static/claim.html` | Device claiming workflow (MAC address input + setup guide) |
| `static/onboarding.html` | Interactive onboarding tutorial for new users |
| `static/app.js` | WebSocket client, auth guard, device filtering logic |
| `static/dashboard.js` | Dashboard rendering, real-time chart updates, data processing |
| `static/style.css` | Dark theme, responsive design, RTL support for Arabic |
| `execute_command.js` | Helper for executing commands from the UI |

**Access:**
```
http://localhost:8000
```

---

### 🔷 **firmware/** - ESP32 Microcontroller Code

**Purpose:** Arduino C++ code for ESP32 edge device

| File | Purpose |
|------|---------|
| `ESP32_EnergyAnomalyDetector.ino` | Basic firmware (single-core, initial version) |
| `ESP32_EnergyAnomalyDetector_v2.ino` | **[RECOMMENDED]** Production firmware with dual-core processing, watchdog timer, circular buffer |
| `IsolationForestModel.h` | Compiled C++ Isolation Forest model (auto-generated from Python) |
| `RobustScalerParams.h` | Pre-computed feature scaler parameters (auto-generated from Python) |
| `platformio.ini` | PlatformIO configuration for building/uploading |

**Features:**
- Reads energy sensors (CT clamps or shunt resistors)
- Runs ML inference locally on ESP32
- Sends telemetry via MQTT to backend
- WiFi auto-reconnect + MQTT client
- Dual-core architecture + watchdog timer (v2)
- Circular buffer for sensor data

**Build & Upload:**
```bash
cd firmware
platformio run --target upload
```

---

### 🔷 **ml_models/** - Model Training & Export

**Purpose:** Python scripts for training and exporting ML models

| File | Purpose |
|------|---------|
| `train_isolation_forest.py` | Train Isolation Forest model on energy data, save to `iforest_model.pkl` |
| `feature_engineering.py` | Extract features: power deltas, rolling averages, variance, trends |
| `preprocess_energy.py` | Clean data: remove outliers, handle missing values, normalize |
| `inject_anomalies.py` | Inject synthetic anomalies into training data to improve model robustness |
| `export_iforest_to_cpp.py` | Convert trained model to C++ header (`firmware/IsolationForestModel.h`) |
| `export_scaler_to_cpp.py` | Export RobustScaler parameters to C++ header (`firmware/RobustScalerParams.h`) |

**Workflow:**
```bash
cd ml_models

# 1. Preprocess raw data
python preprocess_energy.py

# 2. Engineer features
python feature_engineering.py

# 3. (Optional) Inject synthetic anomalies
python inject_anomalies.py

# 4. Train model
python train_isolation_forest.py

# 5. Export to C++ headers for ESP32
python export_iforest_to_cpp.py
python export_scaler_to_cpp.py

# 6. Copy headers to firmware folder
cp IsolationForestModel.h ../firmware/
cp RobustScalerParams.h ../firmware/
```

---

### 🔷 **data/** - Datasets

**Purpose:** Training and test data

| File | Purpose |
|------|---------|
| `sample_energy_data.csv` | Example energy consumption data (power in Watts, timestamps) |

**Format:**
```
timestamp,power_w,appliance_id
2024-01-01 10:00:00,250.5,1
2024-01-01 10:01:00,251.2,1
...
```

---

### 🔷 **config/** - Configuration

**Purpose:** Project dependencies and settings

| File | Purpose |
|------|---------|
| `requirements.txt` | Python package dependencies (pip install -r config/requirements.txt) |

**Packages included:**
- FastAPI, Uvicorn (web framework)
- paho-mqtt (MQTT client)
- SQLAlchemy (database ORM)
- scikit-learn (ML models)
- numpy, pandas (data processing)
- python-jose (JWT auth)

---

### 🔷 **docs/** - Documentation

**Purpose:** Project guides, setup instructions, task tracking

| File | Purpose |
|------|---------|
| `PROJECT_GUIDE.md` | Comprehensive overview of all components |
| `ENV_SETUP_GUIDE.md` | Step-by-step environment setup (Python, MQTT, Arduino) |
| `TODO.md` | Remaining features and bug fixes |

---

### 🔷 **scripts/** - Automation

**Purpose:** Setup and utility scripts

| File | Purpose |
|------|---------|
| `setup_vscode_esp32.ps1` | PowerShell script to auto-configure VS Code for ESP32 development |

**Usage:**
```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_vscode_esp32.ps1
```

---

### 🔷 **.vscode/** - VS Code Configuration

**Purpose:** Development environment setup

| File | Purpose |
|------|---------|
| `c_cpp_properties.json` | IntelliSense paths for ESP32 Arduino framework |

---

## 🚀 Quick Start Guide

### 1️⃣ Install Python Dependencies
```bash
pip install -r config/requirements.txt
```

### 2️⃣ Train ML Model
```bash
cd ml_models
python train_isolation_forest.py
python export_iforest_to_cpp.py
python export_scaler_to_cpp.py
```

### 3️⃣ Start Backend Server
```bash
cd backend
uvicorn main:app --reload
```

### 4️⃣ Access Dashboard
```
http://localhost:8000
```

### 5️⃣ Upload Firmware to ESP32
```bash
cd firmware
platformio run --target upload
```

---

## 🔗 Key Paths

| Component | Path |
|-----------|------|
| **Main Server** | `backend/main.py` |
| **Dashboard** | `frontend/static/index.html` |
| **ESP32 Firmware** | `firmware/ESP32_EnergyAnomalyDetector_v2.ino` |
| **Model Training** | `ml_models/train_isolation_forest.py` |
| **Dependencies** | `config/requirements.txt` |
| **Setup Guide** | `docs/ENV_SETUP_GUIDE.md` |
| **Project Guide** | `docs/PROJECT_GUIDE.md` |

---

## ✅ System Health Check

```bash
# Run comprehensive tests
python backend/test_integration.py

# Monitor system health
python backend/system_health_watchdog.py

# Simulate ESP32 messages
python backend/mqtt_simulator.py
```

---

## 📝 File Organization Summary

✅ **backend/** - All Python server code
✅ **frontend/** - All HTML/JS/CSS UI code  
✅ **firmware/** - All C++ Arduino code for ESP32
✅ **ml_models/** - All ML training and export scripts
✅ **data/** - Training data and datasets
✅ **config/** - Dependencies and configuration
✅ **docs/** - Documentation and guides
✅ **scripts/** - Automation scripts

**Ready for development! 🚀**
# flosk
