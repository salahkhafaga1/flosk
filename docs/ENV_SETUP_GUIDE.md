# VS Code Environment Setup Guide

This guide resolves the two most common environment issues for this IoT/AI project.

---

## ⚠️ Critical: PowerShell 5.1 Syntax Errors (`||`, `&&`, `2>nul`)

### Symptom
You see errors like:
```
The token '||' is not a valid statement separator in this version.
The token '&&' is not a valid statement separator in this version.
```

### Root Cause
Windows PowerShell 5.1 (the default shell on Windows 10/11) **does not support** the `||`, `&&`, or `2>nul` operators. The C/C++ extension sometimes tries to resolve wildcard paths using cmd/bash-style commands, which triggers these parser errors.

### Immediate Fix
1. The `.vscode/c_cpp_properties.json` has been updated with a **blank `compilerPath`** and literal username paths to prevent the error.
2. After you install the ESP32 Arduino core, run the PowerShell-safe script:
   ```powershell
   .\scripts\setup_vscode_esp32.ps1
   ```
3. **Recommended alternative:** Use [PlatformIO](#solution-c--use-platformio-recommended-for-professional-projects) instead of the Arduino IDE toolchain. PlatformIO auto-downloads everything and never triggers these shell errors.

### Why Not Just Upgrade PowerShell?
PowerShell 7 supports `||` and `&&`, but VS Code's integrated terminal often defaults to Windows PowerShell 5.1, and the C/C++ extension may still invoke 5.1 internally. The fixes above work on **any** PowerShell version.

---

## Issue 1: Python — `Import "influxdb_client" could not be resolved`

### Root Cause
Pylance (VS Code's Python language server) cannot find the `influxdb_client` package because either:
1. The package is not installed in your active Python environment, **OR**
2. VS Code is using the wrong Python interpreter (e.g., global Python instead of your virtual environment).

### Solution A — Install the Missing Library

Open a terminal **inside VS Code** (`Ctrl + `` `) or Windows Command Prompt and run:

```bash
cd d:/AI/GProject

# Option 1: Install in the global Python environment (simplest for beginners)
pip install influxdb-client

# Option 2: (RECOMMENDED) Create a virtual environment first
python -m venv venv

# On Windows CMD:
venv\Scripts\activate

# On Windows PowerShell:
venv\Scripts\Activate.ps1

# Then install all project dependencies at once
pip install influxdb-client pydantic numpy pandas scikit-learn
```

### Solution B — Select the Correct Python Interpreter in VS Code

If you installed the package but Pylance still shows red squiggles, VS Code is pointing to the wrong Python executable.

**Step-by-step:**

1. **Open the Command Palette**
   - Press `Ctrl + Shift + P`

2. **Select Interpreter**
   - Type: `Python: Select Interpreter`
   - Click on it.

3. **Choose the correct interpreter**
   - If you created a virtual environment (`venv`), select:
     ```
     Python 3.x.x ('venv': venv)  ./venv/Scripts/python.exe
     ```
   - If you installed globally, select:
     ```
     Python 3.x.x
     ```
   - **Avoid** selecting Windows Store Python or Anaconda unless you installed the packages there.

4. **Reload VS Code**
   - Press `Ctrl + Shift + P`
   - Type: `Developer: Reload Window`
   - Press `Enter`.

5. **Verify**
   - Open `test_integration.py`
   - The red squiggle under `from influxdb_client import InfluxDBClient` should disappear within 5–10 seconds.

### Quick Diagnostic Command

Run this in VS Code's terminal to confirm the package is visible to the active interpreter:

```bash
python -c "import influxdb_client; print(influxdb_client.__version__)"
```

If this prints a version number (e.g., `1.37.0`) but VS Code still complains, you definitely have the **wrong interpreter selected** — repeat Solution B.

---

## Issue 2: C/C++ — `Cannot find: C:/Users/DELL/AppData/Local/Arduino15/packages/esp32/tools/...`

### Root Cause
The `c_cpp_properties.json` file contains wildcard paths (`*`) and environment variable syntax (`${env:USERNAME}`) that the Microsoft C/C++ extension **does not always resolve correctly**, especially if:
- You have not yet installed the ESP32 board package in the Arduino IDE.
- The ESP32 core version folder name does not match the wildcard pattern.
- You are using a different installation path (e.g., portable Arduino IDE).

### Solution A — Auto-Generate Correct Paths Using the Arduino Extension (Easiest)

The **Arduino extension for VS Code** can automatically generate the correct `c_cpp_properties.json`.

**Step-by-step:**

1. **Install Extensions**
   - Open VS Code Extensions panel (`Ctrl + Shift + X`)
   - Search and install: **"Arduino"** by Microsoft
   - Search and install: **"C/C++"** by Microsoft

2. **Install ESP32 Board Support in Arduino IDE**
   - Open the **Arduino IDE** (not VS Code)
   - Go to `File → Preferences`
   - In "Additional Board Manager URLs", paste:
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Go to `Tools → Board → Board Manager`
   - Search `ESP32` and click **Install**
   - Wait for installation to finish. This creates the folders we need.

3. **Auto-Generate IntelliSense Config**
   - In VS Code, open `ESP32_EnergyAnomalyDetector_v2.ino`
   - Press `Ctrl + Shift + P`
   - Type: `Arduino: Initialize`
   - Then type: `Arduino: Verify` (or click the checkmark icon in the top-right)
   - The Arduino extension will automatically create/update `.vscode/c_cpp_properties.json` with the **exact absolute paths** for your system.

### Solution B — Auto-Generate Paths with the Provided PowerShell Script

A PowerShell 5.1–safe script is included in this repo. It detects your exact ESP32 core and GCC versions and writes `c_cpp_properties.json` automatically — no `||`, `&&`, or manual editing needed.

```powershell
# Run from the project root (d:/AI/GProject)
.\scripts\setup_vscode_esp32.ps1
```

**What it does:**
- Detects the installed ESP32 core version under `%LOCALAPPDATA%\Arduino15\packages\esp32\hardware\esp32`
- Detects the matching `xtensa-esp32-elf-gcc` toolchain version
- Generates `.vscode/c_cpp_properties.json` with absolute paths

**If you prefer to inspect paths manually**, run this PowerShell 5.1 snippet:

```powershell
$esp32Path = "C:\Users\$env:USERNAME\AppData\Local\Arduino15\packages\esp32\hardware\esp32"
if (Test-Path $esp32Path) {
    Get-ChildItem $esp32Path | Select-Object Name
} else {
    Write-Host "ERROR: ESP32 core not found. Install it via Arduino IDE Board Manager first."
}
```

Here is a **template** — paste your exact version numbers where it says `YOUR_VERSION`:

```json
{
  "configurations": [
    {
      "name": "ESP32 Arduino",
      "includePath": [
        "${workspaceFolder}/**",
        "C:/Users/DELL/AppData/Local/Arduino15/packages/esp32/hardware/esp32/YOUR_VERSION/cores/esp32/**",
        "C:/Users/DELL/AppData/Local/Arduino15/packages/esp32/hardware/esp32/YOUR_VERSION/libraries/**",
        "C:/Users/DELL/AppData/Local/Arduino15/packages/esp32/hardware/esp32/YOUR_VERSION/tools/sdk/include/**",
        "C:/Users/DELL/Documents/Arduino/libraries/**"
      ],
      "defines": [
        "ARDUINO=10800",
        "ESP32",
        "CORE_DEBUG_LEVEL=0"
      ],
      "compilerPath": "C:/Users/DELL/AppData/Local/Arduino15/packages/esp32/tools/xtensa-esp32-elf-gcc/YOUR_GCC_VERSION/bin/xtensa-esp32-elf-gcc.exe",
      "cStandard": "c11",
      "cppStandard": "c++11",
      "intelliSenseMode": "gcc-x64"
    }
  ],
  "version": 4
}
```

### Solution C — Use PlatformIO (Recommended for Professional Projects)

If you want to avoid manual path management entirely, migrate to **PlatformIO**.

**Step-by-step:**

1. Install the **PlatformIO IDE** extension in VS Code.
2. Create a file named `platformio.ini` in `d:/AI/GProject/` with this content:
   ```ini
   [env:esp32dev]
   platform = espressif32
   board = esp32dev
   framework = arduino
   monitor_speed = 115200
   lib_deps =
       mandulaj/PZEM004Tv30 @ ^1.1.2
       knolleary/PubSubClient @ ^2.8
       bblanchon/ArduinoJson @ ^6.21.0
   ```
3. Move your `.ino` code into `src/main.cpp`.
4. PlatformIO will **automatically download** the ESP32 toolchain and resolve all `#include` paths with zero manual configuration.

---

## Summary Checklist

| Issue | Fix |
|-------|-----|
| `influxdb_client` import error | `pip install influxdb-client` + `Ctrl+Shift+P → Python: Select Interpreter` |
| PowerShell `\|\|`, `&&`, `2>nul` errors | Use `.\scripts\setup_vscode_esp32.ps1` (PowerShell 5.1 safe) or switch to [PlatformIO](#solution-c--use-platformio-recommended-for-professional-projects) |
| ESP32 `#include` squiggles | Install ESP32 in Arduino IDE + run `setup_vscode_esp32.ps1`, **OR** use PlatformIO (zero manual config) |

After applying the fixes, press **`Ctrl + Shift + P → C/C++: Rescan Workspace`** or reload VS Code to refresh IntelliSense.

