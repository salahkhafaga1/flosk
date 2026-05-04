"""
main.py
=======
FastAPI backend for the Smart Home Energy Monitoring System.

Features:
  - REST API for telemetry ingestion and anomaly queries
  - WebSocket endpoint for real-time dashboard updates
  - MQTT subscriber that listens to ESP32 telemetry
  - JWT Authentication & User Management
  - Integration with ML inference service and InfluxDB
  - CORS enabled for local frontend development

Run with hot-reload:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

import os
import importlib
import json
import logging
import asyncio
import secrets
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import List as PyList

from database import init_db, get_db, User as UserModel, Device as DeviceModel, Appliance as ApplianceModel
from sqlalchemy.orm import Session

# ---------------------------------------------------------------------------
# Auth imports
# ---------------------------------------------------------------------------
from passlib.context import CryptContext
from jose import JWTError, jwt

# ---------------------------------------------------------------------------
# Project-local imports
# ---------------------------------------------------------------------------
from mqtt_schema_validator import validate_payload
from ml_inference_service import get_service as get_ml_service

try:
    import paho.mqtt.client as mqtt
except ImportError:
    mqtt = None

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("EnergyBackend")

# ---------------------------------------------------------------------------
# Auth Configuration
# ---------------------------------------------------------------------------
_SECRET_KEY_FILE = os.path.join(os.path.dirname(__file__), ".secret_key")

def _load_or_create_secret_key() -> str:
    """Load a persistent secret key from disk, or generate + save a new one."""
    env_key = os.environ.get("SECRET_KEY")
    if env_key:
        return env_key
    if os.path.exists(_SECRET_KEY_FILE):
        with open(_SECRET_KEY_FILE, "r") as f:
            return f.read().strip()
    new_key = secrets.token_urlsafe(64)
    with open(_SECRET_KEY_FILE, "w") as f:
        f.write(new_key)
    return new_key

SECRET_KEY = _load_or_create_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MQTT_BROKER_HOST = os.environ.get("MQTT_BROKER_HOST", "localhost")
MQTT_BROKER_PORT = int(os.environ.get("MQTT_BROKER_PORT", "1883"))
MQTT_TOPIC = os.environ.get("MQTT_TOPIC", "home/energy/alerts")

INFLUXDB_URL = os.environ.get("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.environ.get("INFLUXDB_TOKEN", "my-token")
INFLUXDB_ORG = os.environ.get("INFLUXDB_ORG", "my-org")
INFLUXDB_BUCKET = os.environ.get("INFLUXDB_BUCKET", "energy_data")

MODEL_PATH = os.environ.get("MODEL_PATH", "isolation_forest_model.pkl")

# ---------------------------------------------------------------------------
# In-memory stores (for demo / local dev without InfluxDB)
# ---------------------------------------------------------------------------
recent_readings: List[Dict[str, Any]] = []
MAX_RECENT_READINGS = 200

# Active WebSocket connections for broadcasting
active_websockets: List[WebSocket] = []

# ---------------------------------------------------------------------------
# Auth Helpers
# ---------------------------------------------------------------------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    # bcrypt has a 72-byte limit; truncate safely after UTF-8 encoding
    return pwd_context.verify(plain_password.encode("utf-8")[:72], hashed_password)

def get_password_hash(password: str) -> str:
    # bcrypt has a 72-byte limit; truncate safely after UTF-8 encoding
    return pwd_context.hash(password.encode("utf-8")[:72])

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Optional[UserModel]:
    if token is None:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
    user = db.query(UserModel).filter(UserModel.id == int(user_id)).first()
    return user

async def get_current_active_user(current_user: Optional[UserModel] = Depends(get_current_user)) -> UserModel:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return current_user

# ---------------------------------------------------------------------------
# InfluxDB helper (lazy import to avoid hard dependency failure)
# ---------------------------------------------------------------------------
_influxdb_write_api = None

def _get_influxdb_write_api():
    global _influxdb_write_api
    if _influxdb_write_api is not None:
        return _influxdb_write_api

    try:
        influxdb_client = importlib.import_module("influxdb_client")
        write_api_module = importlib.import_module("influxdb_client.client.write_api")
        InfluxDBClient = influxdb_client.InfluxDBClient
        SYNCHRONOUS = write_api_module.SYNCHRONOUS

        client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG,
        )
        _influxdb_write_api = client.write_api(write_options=SYNCHRONOUS)
        logger.info(f"[InfluxDB] Connected to {INFLUXDB_URL}")
        return _influxdb_write_api
    except ImportError:
        logger.warning("[InfluxDB] influxdb-client not installed. Database writes disabled.")
        return None
    except Exception as exc:
        logger.warning(f"[InfluxDB] Connection failed: {exc}. Database writes disabled.")
        return None


def write_to_influxdb(record: Dict[str, Any]) -> bool:
    """Write a telemetry record to InfluxDB. Returns True on success."""
    api = _get_influxdb_write_api()
    if api is None:
        return False

    try:
        influxdb_client = importlib.import_module("influxdb_client")
        Point = influxdb_client.Point

        point = (
            Point("energy_telemetry")
            .tag("device_id", record.get("device_id", "unknown"))
            .field("voltage", float(record.get("V", 0)))
            .field("current", float(record.get("I", 0)))
            .field("active_power", float(record.get("P", 0)))
            .field("power_factor", float(record.get("PF", 0)))
            .field("reactive_power", float(record.get("Q", 0)))
            .field("anomaly_score", float(record.get("anomaly_score", 0)))
            .field("is_anomaly", bool(record.get("is_anomaly", False)))
            .time(datetime.utcnow())
        )
        api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
        return True
    except Exception as exc:
        logger.error(f"[InfluxDB] Write failed: {exc}")
        return False


# ---------------------------------------------------------------------------
# MQTT Subscriber (runs in background thread)
# ---------------------------------------------------------------------------
_mqtt_client = None

def _on_mqtt_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info(f"[MQTT] Connected to {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
        client.subscribe(MQTT_TOPIC)
        logger.info(f"[MQTT] Subscribed to topic: {MQTT_TOPIC}")
    else:
        logger.error(f"[MQTT] Connection failed with code {rc}")


def _on_mqtt_message(client, userdata, msg):
    raw_payload = msg.payload.decode("utf-8", errors="ignore")
    logger.debug(f"[MQTT] Message on {msg.topic}: {raw_payload[:200]}")

    # 1. Validate schema
    result = validate_payload(raw_payload)
    if not result.is_valid:
        logger.warning(f"[MQTT] Rejected invalid payload: {result.error_msg}")
        return

    record = result.record

    # 2. Run ML inference
    try:
        ml_result = get_ml_service(MODEL_PATH).predict(record)
        if ml_result:
            record.update(ml_result)
    except Exception as exc:
        logger.error(f"[ML] Inference error: {exc}")

    # 3. Write to InfluxDB
    write_to_influxdb(record)

    # 4. Store in memory for dashboard
    recent_readings.append(record)
    if len(recent_readings) > MAX_RECENT_READINGS:
        recent_readings.pop(0)

    # 5. Broadcast to all connected WebSocket clients
    asyncio.run_coroutine_threadsafe(
        _broadcast_ws(json.dumps(record, default=str)),
        _async_loop,
    )

    logger.info(
        f"[PIPELINE] Processed reading from {record.get('device_id')} "
        f"| V={record.get('V')}V I={record.get('I')}A "
        f"| anomaly={record.get('is_anomaly', False)} "
        f"| score={record.get('anomaly_score', 'N/A')}"
    )


_async_loop: asyncio.AbstractEventLoop


def start_mqtt_subscriber():
    global _mqtt_client, _async_loop
    if mqtt is None:
        logger.warning("[MQTT] paho-mqtt not installed. MQTT subscriber disabled.")
        return

    _async_loop = asyncio.get_event_loop()

    _mqtt_client = mqtt.Client()
    _mqtt_client.on_connect = _on_mqtt_connect
    _mqtt_client.on_message = _on_mqtt_message

    try:
        _mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
        _mqtt_client.loop_start()
        logger.info("[MQTT] Subscriber thread started.")
    except Exception as exc:
        logger.warning(f"[MQTT] Could not connect to broker: {exc}")


def stop_mqtt_subscriber():
    if _mqtt_client:
        _mqtt_client.loop_stop()
        _mqtt_client.disconnect()
        logger.info("[MQTT] Subscriber stopped.")


# ---------------------------------------------------------------------------
# WebSocket broadcasting helper
# ---------------------------------------------------------------------------
async def _broadcast_ws(message: str):
    dead_sockets = []
    for ws in active_websockets:
        try:
            await ws.send_text(message)
        except Exception:
            dead_sockets.append(ws)
    for ws in dead_sockets:
        if ws in active_websockets:
            active_websockets.remove(ws)


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[BOOT] Starting Energy Monitoring Backend...")
    init_db()
    logger.info("[DB] SQLite database initialized.")
    start_mqtt_subscriber()
    yield
    logger.info("[SHUTDOWN] Stopping Energy Monitoring Backend...")
    stop_mqtt_subscriber()


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Smart Home Energy Monitoring API",
    description="Real-time energy telemetry ingestion, anomaly detection, and dashboard backend.",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS: allow frontend running on localhost:8080 (or any origin during dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend files from "static/" directory
try:
    app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")
except RuntimeError:
    logger.warning('[StaticFiles] "static/" directory not found. Frontend will not be served.')


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]

class DeviceClaim(BaseModel):
    device_id: str

class ApplianceItem(BaseModel):
    name: str
    wattage: float
    quantity: int = 1

class ApplianceCreateRequest(BaseModel):
    appliances: PyList[ApplianceItem]

class ApplianceResponse(BaseModel):
    id: int
    user_id: int
    name: str
    wattage: float
    quantity: int
    created_at: Optional[str]

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Auth Endpoints
# ---------------------------------------------------------------------------

@app.post("/auth/register", response_model=UserResponse)
def register_user(payload: UserRegister, db: Session = Depends(get_db)):
    """Register a new user account."""
    existing = db.query(UserModel).filter(UserModel.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = UserModel(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"[AUTH] Registered user: {payload.email}")
    return UserResponse(id=user.id, email=user.email, full_name=user.full_name)


@app.post("/auth/login", response_model=Token)
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/auth/me", response_model=UserResponse)
def get_me(current_user: UserModel = Depends(get_current_active_user)):
    """Get current authenticated user profile."""
    return UserResponse(id=current_user.id, email=current_user.email, full_name=current_user.full_name)


@app.get("/claim", response_class=HTMLResponse)
def claim_page():
    """Serve the device claiming page."""
    return FileResponse("../frontend/static/claim.html")


# ---------------------------------------------------------------------------
# Device Claiming Endpoints
# ---------------------------------------------------------------------------

@app.post("/device/claim")
def claim_device(
    payload: DeviceClaim,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Claim an ESP32 device for the current user."""
    # Check if user already has a device
    existing = db.query(DeviceModel).filter(DeviceModel.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already has a claimed device")

    device = DeviceModel(
        user_id=current_user.id,
        device_id=payload.device_id,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    logger.info(f"[DEVICE] User {current_user.id} claimed device {payload.device_id}")
    return {"status": "claimed", "device_id": device.device_id}


@app.get("/device/status")
def device_status(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Check if the current user has claimed a device and its online status."""
    device = db.query(DeviceModel).filter(DeviceModel.user_id == current_user.id).first()
    if not device:
        return {"has_device": False, "device_id": None, "online": False, "last_seen": None}

    # Check if device has sent data recently (within last 60 seconds)
    last_seen = None
    online = False
    for reading in reversed(recent_readings):
        if reading.get("device_id") == device.device_id:
            last_seen = reading.get("timestamp")
            if isinstance(last_seen, (int, float)):
                online = (datetime.utcnow().timestamp() - last_seen) < 60
            break

    return {
        "has_device": True,
        "device_id": device.device_id,
        "online": online,
        "last_seen": last_seen,
    }


@app.post("/device/unclaim")
def unclaim_device(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Unclaim the current user's device."""
    device = db.query(DeviceModel).filter(DeviceModel.user_id == current_user.id).first()
    if not device:
        raise HTTPException(status_code=404, detail="No device found")

    db.delete(device)
    db.commit()
    logger.info(f"[DEVICE] User {current_user.id} unclaimed device")
    return {"status": "unclaimed"}


# ---------------------------------------------------------------------------
# Landing Page & Root
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def root():
    """Serve the premium landing page."""
    return FileResponse("../frontend/static/landing.html")


@app.get("/login", response_class=HTMLResponse)
def login_page():
    """Serve the login page."""
    return FileResponse("../frontend/static/login.html")


@app.get("/onboarding", response_class=HTMLResponse)
def onboarding_page():
    """Serve the appliance onboarding wizard page."""
    return FileResponse("../frontend/static/onboarding.html")


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page():
    """Serve the main business dashboard."""
    return FileResponse("../frontend/static/index.html")


# ---------------------------------------------------------------------------
# Health & Telemetry Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "ml_service": get_ml_service(MODEL_PATH).health(),
        "recent_readings_count": len(recent_readings),
        "mqtt_connected": _mqtt_client is not None and _mqtt_client.is_connected()
        if _mqtt_client else False,
    }


@app.get("/api/readings")
def get_readings(limit: int = 50) -> List[Dict[str, Any]]:
    """Get the most recent telemetry readings."""
    return recent_readings[-limit:]


@app.get("/api/readings/latest")
def get_latest_reading() -> Optional[Dict[str, Any]]:
    """Get the single most recent telemetry reading."""
    if not recent_readings:
        raise HTTPException(status_code=404, detail="No readings available yet.")
    return recent_readings[-1]


@app.get("/api/anomalies")
def get_anomalies(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent readings flagged as anomalies."""
    anomalies = [r for r in recent_readings if r.get("is_anomaly")]
    return anomalies[-limit:]


@app.post("/api/ingest")
def ingest_manual(record: Dict[str, Any]) -> Dict[str, Any]:
    """Manually ingest a telemetry record (for testing without MQTT)."""
    result = validate_payload(json.dumps(record))
    if not result.is_valid:
        raise HTTPException(status_code=422, detail=result.error_msg)

    validated = result.record
    ml_result = get_ml_service(MODEL_PATH).predict(validated)
    if ml_result:
        validated.update(ml_result)

    recent_readings.append(validated)
    if len(recent_readings) > MAX_RECENT_READINGS:
        recent_readings.pop(0)

    write_to_influxdb(validated)
    return {"status": "accepted", "record": validated}


# ---------------------------------------------------------------------------
# Appliances REST Endpoints (Auth-protected)
# ---------------------------------------------------------------------------

@app.post("/api/appliances", response_model=PyList[ApplianceResponse])
def create_appliances(
    payload: ApplianceCreateRequest,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PyList[ApplianceResponse]:
    """Batch-create appliances for the authenticated user."""
    # Clear existing appliances for clean re-runs
    db.query(ApplianceModel).filter(ApplianceModel.user_id == current_user.id).delete()
    db.commit()

    created = []
    for item in payload.appliances:
        db_appliance = ApplianceModel(
            user_id=current_user.id,
            name=item.name,
            wattage=item.wattage,
            quantity=item.quantity,
        )
        db.add(db_appliance)
        created.append(db_appliance)

    db.commit()
    for a in created:
        db.refresh(a)

    logger.info(f"[ONBOARDING] Saved {len(created)} appliances for user={current_user.id}")
    return [ApplianceResponse(**a.to_dict()) for a in created]


@app.get("/api/appliances", response_model=PyList[ApplianceResponse])
def get_appliances(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PyList[ApplianceResponse]:
    """Retrieve all registered appliances for the authenticated user."""
    items = db.query(ApplianceModel).filter(ApplianceModel.user_id == current_user.id).all()
    return [ApplianceResponse(**a.to_dict()) for a in items]


@app.get("/api/appliances/check")
def check_onboarding_status(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Check whether the user has completed onboarding."""
    count = db.query(ApplianceModel).filter(ApplianceModel.user_id == current_user.id).count()
    return {"onboarded": count > 0, "count": count}


# ---------------------------------------------------------------------------
# WebSocket Endpoint (real-time dashboard)
# ---------------------------------------------------------------------------
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    logger.info(f"[WS] Client connected. Total clients: {len(active_websockets)}")

    try:
        history = recent_readings[-20:]
        await websocket.send_text(json.dumps({"type": "history", "data": history}, default=str))

        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        logger.info("[WS] Client disconnected.")
    except Exception as exc:
        logger.warning(f"[WS] Error: {exc}")
    finally:
        if websocket in active_websockets:
            active_websockets.remove(websocket)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=80,
        reload=True,
        log_level="info",
    )
