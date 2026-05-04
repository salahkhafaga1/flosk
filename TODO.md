# TODO.md - Running Project_H Smart Home Energy Monitor

## Progress Tracker
### 1. Install Python Dependencies ✅ (already satisfied)
### 2. Train & Export ML Model ✅ (iforest_model.pkl exists)
### 3. Start Backend Server (uvicorn) ⏳ [Launcher fixed, retrying python -m uvicorn]
### 4. Verify Dashboard at http://localhost:8000 ⏳
### 5. Test Login/Claim/Simulator ⏳

## Notes
- uvicorn launcher broken (pip reinstall if needed: python -m pip install --force-reinstall uvicorn)
- Server serves frontend + API + WS + MQTT
