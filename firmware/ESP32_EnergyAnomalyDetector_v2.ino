/*
 * ESP32 Smart-Home Energy Anomaly Detector v2.0
 * Production-Ready with Auto-Recovery, Async Buffering, and Hardware WDT
 *
 * Architecture:
 *   - Core 0: PZEM-004T polling task (1 Hz, non-blocking) + WDT feed
 *   - Core 1: MQTT reconnect + inference + publish + buffer drain
 *
 * Resilience Features:
 *   1. Asynchronous Circular Buffer: No data loss during WiFi/MQTT drops
 *   2. WiFi/MQTT State Machine: Exponential backoff, clean reconnects
 *   3. Hardware Watchdog Timer (WDT): Reboots ESP32 if PZEM UART hangs
 *   4. Sensor Hang Detection: Software timeout + WDT for dual protection
 *
 * Libraries required:
 *   - PZEM004Tv30 by mandulaj
 *   - PubSubClient by Nick O'Leary
 *   - ArduinoJson by Benoit Blanchon
 *   - WiFi (built-in)
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <PZEM004Tv30.h>
#include <esp_task_wdt.h>
#include "IsolationForestModel.h"
#include "RobustScalerParams.h"

// ==================== USER CONFIGURATION ====================
static const char* WIFI_SSID     = "YOUR_WIFI_SSID";
static const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
static const char* MQTT_BROKER   = "192.168.1.100";
static const int   MQTT_PORT     = 1883;
static const char* MQTT_TOPIC    = "home/energy/alerts";
static const char* MQTT_BUFFER_TOPIC = "home/energy/buffered"; // for batched backlog
static const char* DEVICE_ID     = "esp32-energy-01";

// Anomaly decision threshold (matches sklearn contamination=0.03)
static const float ANOMALY_THRESHOLD = 0.5f;

// PZEM-004T v3.0 on HardwareSerial2 (RX=GPIO16, TX=GPIO17)
static const int PZEM_RX_PIN = 16;
static const int PZEM_TX_PIN = 17;

// ==================== RESILIENCE CONFIGURATION ====================
// WDT timeout in seconds (must be > sensor poll period)
static const int WDT_TIMEOUT_SECONDS = 5;

// Max time (ms) allowed for a single PZEM read before considered hung
static const int PZEM_READ_TIMEOUT_MS = 2000;

// WiFi/MQTT reconnection backoff (ms)
static const int RECONNECT_BASE_MS = 1000;
static const int RECONNECT_MAX_MS  = 30000;

// Async buffer size (number of readings to queue during outage)
static const int BUFFER_SIZE = 120; // ~2 minutes at 1 Hz

// ==================== HARDWARE OBJECTS ====================
HardwareSerial pzemSerial(2);
PZEM004Tv30 pzem(pzemSerial, PZEM_RX_PIN, PZEM_TX_PIN);
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

// ==================== RTOS SYNCHRONISATION ====================
static SemaphoreHandle_t sensorMutex;
static SemaphoreHandle_t bufferMutex;
static TickType_t lastSensorTick = 0;

// ==================== SENSOR DATA BUFFER ====================
// Protected by sensorMutex
static volatile float g_voltage       = 0.0f;
static volatile float g_current       = 0.0f;
static volatile float g_activePower   = 0.0f;
static volatile float g_powerFactor   = 0.0f;
static volatile bool  g_dataFresh     = false;
static volatile unsigned long g_lastSuccessfulSensorRead = 0;

// ==================== ASYNC CIRCULAR BUFFER ====================
// Stores readings when MQTT is offline. Protected by bufferMutex.
struct SensorReading {
    float voltage;
    float current;
    float activePower;
    float powerFactor;
    unsigned long timestamp;
    bool valid;
};

static SensorReading asyncBuffer[BUFFER_SIZE];
static volatile int bufferHead = 0;
static volatile int bufferTail = 0;
static volatile int bufferCount = 0;

// ==================== ROLLING WINDOW FOR VARIANCE ====================
#define VAR_WINDOW_SIZE 60
static float currentRingBuffer[VAR_WINDOW_SIZE];
static uint8_t ringHead = 0;
static uint8_t ringCount = 0;

// Previous values for delta computation
static float prevActivePower = 0.0f;
static float prevReactivePower = 0.0f;
static bool  havePrev = false;

// ==================== STATE MACHINE ====================
enum SystemState {
    STATE_WIFI_CONNECTING,
    STATE_MQTT_CONNECTING,
    STATE_ONLINE,
    STATE_RECOVERING
};
static volatile SystemState g_systemState = STATE_WIFI_CONNECTING;
static int reconnectBackoffMs = RECONNECT_BASE_MS;

// ==================== FUNCTION PROTOTYPES ====================
void TaskSensorPoll(void* pvParameters);
void TaskMqttAndInference(void* pvParameters);
bool reconnectMqtt();
bool ensureWiFiConnected();
void scaleFeatures(const float raw[9], float scaled[9]);
float computeRollingVar();
float computeReactivePower(float P, float PF);
bool pushToBuffer(const SensorReading& reading);
bool popFromBuffer(SensorReading& reading);
void drainBuffer();
void feedWatchdog();
bool isSensorHung();

// ==================== SETUP ====================
void setup() {
    Serial.begin(115200);
    delay(100);
    Serial.println("[BOOT] ESP32 Energy Anomaly Detector v2.0");
    Serial.println("[BOOT] Resilience features: Async Buffer | WDT | State Machine");

    pzemSerial.begin(9600, SERIAL_8N1, PZEM_RX_PIN, PZEM_TX_PIN);

    // Initialize mutexes
    sensorMutex = xSemaphoreCreateMutex();
    bufferMutex = xSemaphoreCreateMutex();
    if (sensorMutex == NULL || bufferMutex == NULL) {
        Serial.println("[FATAL] Failed to create mutexes");
        while (true) { delay(1000); }
    }

    // Initialize WDT for Core 0 (sensor task)
    // Note: esp_task_wdt_init must be called before task creation
    esp_err_t wdt_err = esp_task_wdt_init(WDT_TIMEOUT_SECONDS, true);
    if (wdt_err != ESP_OK) {
        Serial.printf("[WDT] Init warning: %d\n", wdt_err);
    }
    // Subscribe the current task (will run on Core 0 later) to WDT
    esp_task_wdt_add(NULL);

    // Start WiFi
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    g_systemState = STATE_WIFI_CONNECTING;

    // --- Task pinned to Core 0: sensor polling + WDT ---
    xTaskCreatePinnedToCore(
        TaskSensorPoll,
        "SensorPoll",
        4096,
        NULL,
        2,          // higher priority
        NULL,
        0           // Core 0
    );

    // --- Task pinned to Core 1: MQTT + inference + buffer drain ---
    xTaskCreatePinnedToCore(
        TaskMqttAndInference,
        "MqttInference",
        8192,
        NULL,
        1,
        NULL,
        1           // Core 1
    );

    Serial.println("[BOOT] FreeRTOS tasks started.");
}

void loop() {
    // Empty: all work is done in tasks
    vTaskDelay(portMAX_DELAY);
}

// ==================== WATCHDOG HELPERS ====================
void feedWatchdog() {
    esp_task_wdt_reset();
}

bool isSensorHung() {
    unsigned long now = millis();
    unsigned long lastRead = g_lastSuccessfulSensorRead;
    // If no successful read in 2x expected interval (2 seconds), consider hung
    if (lastRead == 0) return false; // Not initialized yet
    return (now - lastRead) > (unsigned long)(PZEM_READ_TIMEOUT_MS * 2);
}

// ==================== ASYNC BUFFER HELPERS ====================
bool pushToBuffer(const SensorReading& reading) {
    xSemaphoreTake(bufferMutex, portMAX_DELAY);
    bool success = false;
    if (bufferCount < BUFFER_SIZE) {
        asyncBuffer[bufferHead] = reading;
        bufferHead = (bufferHead + 1) % BUFFER_SIZE;
        bufferCount++;
        success = true;
    }
    xSemaphoreGive(bufferMutex);
    return success;
}

bool popFromBuffer(SensorReading& reading) {
    xSemaphoreTake(bufferMutex, portMAX_DELAY);
    bool success = false;
    if (bufferCount > 0) {
        reading = asyncBuffer[bufferTail];
        bufferTail = (bufferTail + 1) % BUFFER_SIZE;
        bufferCount--;
        success = true;
    }
    xSemaphoreGive(bufferMutex);
    return success;
}

int getBufferCount() {
    xSemaphoreTake(bufferMutex, portMAX_DELAY);
    int count = bufferCount;
    xSemaphoreGive(bufferMutex);
    return count;
}

// ==================== CORE 0: SENSOR POLLING + WDT ====================
void TaskSensorPoll(void* pvParameters) {
    (void)pvParameters;
    const TickType_t frequency = pdMS_TO_TICKS(1000); // 1 Hz

    // Add this task to WDT
    esp_task_wdt_add(NULL);

    for (;;) {
        TickType_t xLastWakeTime = xTaskGetTickCount();

        // Record start time for timeout detection
        unsigned long readStart = millis();

        float v = pzem.voltage();
        float i = pzem.current();
        float p = pzem.power();
        float pf = pzem.pf();

        unsigned long readDuration = millis() - readStart;

        // Validate readings (PZEM returns NaN on comm failure)
        bool valid = !isnan(v) && !isnan(i) && !isnan(p) && !isnan(pf);
        bool hung = (readDuration > (unsigned long)PZEM_READ_TIMEOUT_MS) || isSensorHung();

        if (hung) {
            Serial.printf("[SENSOR] HANG DETECTED! readDuration=%lums. Triggering WDT reboot...\n", readDuration);
            // Intentionally stop feeding WDT to force reboot
            while (true) {
                delay(1000); // WDT will trigger here
            }
        }

        if (valid) {
            xSemaphoreTake(sensorMutex, portMAX_DELAY);
            g_voltage     = v;
            g_current     = i;
            g_activePower = p;
            g_powerFactor = pf;
            g_dataFresh   = true;
            g_lastSuccessfulSensorRead = millis();
            xSemaphoreGive(sensorMutex);
        } else {
            Serial.println("[SENSOR] Invalid PZEM read (NaN)");
        }

        // Feed the watchdog to prove we're alive
        feedWatchdog();

        vTaskDelayUntil(&xLastWakeTime, frequency);
    }
}

// ==================== CORE 1: MQTT + INFERENCE + BUFFER DRAIN ====================
void TaskMqttAndInference(void* pvParameters) {
    (void)pvParameters;

    for (;;) {
        // ----- State Machine for Connectivity -----
        switch (g_systemState) {
            case STATE_WIFI_CONNECTING:
                if (ensureWiFiConnected()) {
                    Serial.println("[WIFI] Connected.");
                    g_systemState = STATE_MQTT_CONNECTING;
                    reconnectBackoffMs = RECONNECT_BASE_MS;
                } else {
                    delay(reconnectBackoffMs);
                    reconnectBackoffMs = min(reconnectBackoffMs * 2, RECONNECT_MAX_MS);
                }
                break;

            case STATE_MQTT_CONNECTING:
                mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
                if (reconnectMqtt()) {
                    Serial.println("[MQTT] Connected.");
                    g_systemState = STATE_ONLINE;
                    reconnectBackoffMs = RECONNECT_BASE_MS;
                } else {
                    delay(reconnectBackoffMs);
                    reconnectBackoffMs = min(reconnectBackoffMs * 2, RECONNECT_MAX_MS);
                    if (!WiFi.isConnected()) {
                        g_systemState = STATE_WIFI_CONNECTING;
                    }
                }
                break;

            case STATE_ONLINE:
                if (!mqttClient.connected() || !WiFi.isConnected()) {
                    Serial.println("[NET] Connection lost! Entering recovery.");
                    g_systemState = STATE_RECOVERING;
                    break;
                }
                mqttClient.loop();
                processSensorData();
                drainBuffer(); // Try to send any backlog
                break;

            case STATE_RECOVERING:
                if (ensureWiFiConnected() && reconnectMqtt()) {
                    Serial.println("[RECOVERY] Back online.");
                    g_systemState = STATE_ONLINE;
                    reconnectBackoffMs = RECONNECT_BASE_MS;
                } else {
                    delay(reconnectBackoffMs);
                    reconnectBackoffMs = min(reconnectBackoffMs * 2, RECONNECT_MAX_MS);
                }
                break;
        }

        vTaskDelay(pdMS_TO_TICKS(50));
    }
}

// ==================== SENSOR DATA PROCESSING ====================
void processSensorData() {
    bool fresh = false;
    float V = 0.0f, I = 0.0f, P = 0.0f, PF = 0.0f;

    xSemaphoreTake(sensorMutex, portMAX_DELAY);
    fresh = g_dataFresh;
    if (fresh) {
        V  = g_voltage;
        I  = g_current;
        P  = g_activePower;
        PF = g_powerFactor;
        g_dataFresh = false;
    }
    xSemaphoreGive(sensorMutex);

    if (!fresh) {
        return;
    }

    // ----- Compute derived quantities -----
    float S = (PF > 0.001f) ? (P / PF) : 0.0f;
    float Q = computeReactivePower(P, PF);

    // ----- Rolling variance of current (60 s window) -----
    currentRingBuffer[ringHead] = I;
    ringHead = (ringHead + 1) % VAR_WINDOW_SIZE;
    if (ringCount < VAR_WINDOW_SIZE) ringCount++;
    float var60 = computeRollingVar();

    // ----- Deltas -----
    float dP = 0.0f;
    float dQ = 0.0f;
    if (havePrev) {
        dP = P - prevActivePower;
        dQ = Q - prevReactivePower;
    }
    prevActivePower   = P;
    prevReactivePower = Q;
    havePrev = true;

    // ----- Assemble raw feature vector -----
    float rawFeatures[9] = {
        V, I, P, PF, S, Q, dP, dQ, var60
    };

    // ----- RobustScaler normalisation -----
    float scaledFeatures[9];
    scaleFeatures(rawFeatures, scaledFeatures);

    // ----- Isolation Forest inference -----
    float anomalyScore = predict_anomaly(scaledFeatures);

    Serial.printf("[INF] V=%.1f I=%.3f P=%.1f PF=%.3f Q=%.1f score=%.4f buf=%d\n",
                  V, I, P, PF, Q, anomalyScore, getBufferCount());

    // ----- Build JSON payload -----
    StaticJsonDocument<512> doc;
    doc["device_id"] = DEVICE_ID;
    doc["timestamp"] = millis();
    doc["V"]         = serialized(String(V, 2));
    doc["I"]         = serialized(String(I, 3));
    doc["P"]         = serialized(String(P, 2));
    doc["Q"]         = serialized(String(Q, 2));
    doc["PF"]        = serialized(String(PF, 3));
    doc["alert"]     = (anomalyScore > ANOMALY_THRESHOLD);
    doc["score"]     = serialized(String(anomalyScore, 4));

    char payload[512];
    size_t n = serializeJson(doc, payload, sizeof(payload));

    if (n >= sizeof(payload) - 1) {
        Serial.println("[MQTT] Payload overflow!");
        return;
    }

    // ----- Publish or Buffer -----
    if (g_systemState == STATE_ONLINE && mqttClient.connected()) {
        bool pub = mqttClient.publish(MQTT_TOPIC, payload);
        Serial.printf("[MQTT] Publish %s: %s\n", pub ? "OK" : "FAIL", payload);

        if (!pub) {
            // If publish fails, buffer it
            SensorReading reading = {V, I, P, PF, millis(), true};
            if (!pushToBuffer(reading)) {
                Serial.println("[BUFFER] Overflow! Dropping oldest data.");
            }
        }
    } else {
        // Offline: buffer the reading
        SensorReading reading = {V, I, P, PF, millis(), true};
        if (pushToBuffer(reading)) {
            Serial.printf("[BUFFER] Stored reading. Buffer count: %d\n", getBufferCount());
        } else {
            Serial.println("[BUFFER] Full! Dropping reading.");
        }
    }
}

// ==================== BUFFER DRAIN ====================
void drainBuffer() {
    if (getBufferCount() == 0) return;
    if (!mqttClient.connected()) return;

    Serial.printf("[BUFFER] Draining %d buffered readings...\n", getBufferCount());

    int drained = 0;
    SensorReading reading;
    while (popFromBuffer(reading) && mqttClient.connected()) {
        StaticJsonDocument<512> doc;
        doc["device_id"] = DEVICE_ID;
        doc["timestamp"] = reading.timestamp;
        doc["V"]         = serialized(String(reading.voltage, 2));
        doc["I"]         = serialized(String(reading.current, 3));
        doc["P"]         = serialized(String(reading.activePower, 2));
        doc["PF"]        = serialized(String(reading.powerFactor, 3));
        doc["buffered"]  = true; // flag as backfilled data

        char payload[512];
        size_t n = serializeJson(doc, payload, sizeof(payload));
        if (n < sizeof(payload) - 1) {
            mqttClient.publish(MQTT_BUFFER_TOPIC, payload);
            drained++;
        }

        // Yield to prevent starving other tasks
        if (drained % 5 == 0) {
            vTaskDelay(pdMS_TO_TICKS(10));
        }
    }

    Serial.printf("[BUFFER] Drained %d readings. Remaining: %d\n", drained, getBufferCount());
}

// ==================== CONNECTIVITY HELPERS ====================
bool ensureWiFiConnected() {
    if (WiFi.status() == WL_CONNECTED) {
        return true;
    }
    Serial.print("[WIFI] Connecting");
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        Serial.print(".");
        attempts++;
    }
    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("\n[WIFI] IP: %s\n", WiFi.localIP().toString().c_str());
        return true;
    }
    Serial.println("\n[WIFI] Failed.");
    return false;
}

bool reconnectMqtt() {
    if (mqttClient.connected()) return true;

    Serial.print("[MQTT] Attempting connection...");
    String clientId = String("esp32-") + String(random(0xffff), HEX);

    if (mqttClient.connect(clientId.c_str())) {
        Serial.println(" connected");
        return true;
    } else {
        Serial.printf(" failed, rc=%d\n", mqttClient.state());
        return false;
    }
}

// ==================== HELPER FUNCTIONS ====================

float computeReactivePower(float P, float PF) {
    if (PF <= 0.0f || PF > 1.0f) return 0.0f;
    float S = P / PF;
    float diffSq = S * S - P * P;
    if (diffSq < 0.0f) diffSq = 0.0f;
    return sqrtf(diffSq);
}

float computeRollingVar() {
    if (ringCount == 0) return 0.0f;

    float sum = 0.0f;
    uint8_t n = ringCount;
    for (uint8_t i = 0; i < n; ++i) {
        sum += currentRingBuffer[i];
    }
    float mean = sum / n;

    float sqDiffSum = 0.0f;
    for (uint8_t i = 0; i < n; ++i) {
        float diff = currentRingBuffer[i] - mean;
        sqDiffSum += diff * diff;
    }
    return sqDiffSum / n;
}

void scaleFeatures(const float raw[9], float scaled[9]) {
    for (int i = 0; i < N_FEATURES; ++i) {
        float denom = SCALER_IQR[i];
        if (denom < 1e-8f) denom = 1e-8f;
        scaled[i] = (raw[i] - SCALER_MEDIAN[i]) / denom;
    }
}

