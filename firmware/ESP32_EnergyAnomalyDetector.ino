/*
 * ESP32 Smart-Home Energy Anomaly Detector
 * 
 * Architecture:
 *   - Core 0: PZEM-004T polling task (1 Hz, non-blocking)
 *   - Core 1: MQTT reconnect + inference + publish
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
#include "IsolationForestModel.h"
#include "RobustScalerParams.h"

// ==================== USER CONFIGURATION ====================
static const char* WIFI_SSID     = "YOUR_WIFI_SSID";
static const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
static const char* MQTT_BROKER   = "192.168.1.100";
static const int   MQTT_PORT     = 1883;
static const char* MQTT_TOPIC    = "home/energy/alerts";
static const char* DEVICE_ID     = "esp32-energy-01";

// Anomaly decision threshold (matches sklearn contamination=0.03)
static const float ANOMALY_THRESHOLD = 0.5f;

// PZEM-004T v3.0 on HardwareSerial2 (RX=GPIO16, TX=GPIO17)
static const int PZEM_RX_PIN = 16;
static const int PZEM_TX_PIN = 17;

// ==================== HARDWARE OBJECTS ====================
HardwareSerial pzemSerial(2);
PZEM004Tv30 pzem(pzemSerial, PZEM_RX_PIN, PZEM_TX_PIN);
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

// ==================== RTOS SYNCHRONISATION ====================
static SemaphoreHandle_t sensorMutex;
static TickType_t lastSensorTick = 0;

// ==================== SENSOR DATA BUFFER ====================
// Protected by sensorMutex
static volatile float g_voltage       = 0.0f;
static volatile float g_current       = 0.0f;
static volatile float g_activePower   = 0.0f;
static volatile float g_powerFactor   = 0.0f;
static volatile bool  g_dataFresh     = false;

// ==================== ROLLING WINDOW FOR VARIANCE ====================
// 60-second circular buffer for current samples
#define VAR_WINDOW_SIZE 60
static float currentRingBuffer[VAR_WINDOW_SIZE];
static uint8_t ringHead = 0;
static uint8_t ringCount = 0;

// Previous values for delta computation
static float prevActivePower = 0.0f;
static float prevReactivePower = 0.0f;
static bool  havePrev = false;

// ==================== FUNCTION PROTOTYPES ====================
void TaskSensorPoll(void* pvParameters);
void TaskMqttAndInference(void* pvParameters);
bool reconnectMqtt();
void scaleFeatures(const float raw[9], float scaled[9]);
float computeRollingVar();
float computeReactivePower(float P, float PF);

// ==================== SETUP ====================
void setup() {
    Serial.begin(115200);
    delay(100);
    Serial.println("[BOOT] ESP32 Energy Anomaly Detector");

    pzemSerial.begin(9600, SERIAL_8N1, PZEM_RX_PIN, PZEM_TX_PIN);

    sensorMutex = xSemaphoreCreateMutex();
    if (sensorMutex == NULL) {
        Serial.println("[FATAL] Failed to create sensorMutex");
        while (true) { delay(1000); }
    }

    // Start WiFi
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    Serial.print("[WIFI] Connecting");
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.printf("\n[WIFI] Connected, IP: %s\n", WiFi.localIP().toString().c_str());

    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);

    // --- Task pinned to Core 0: sensor polling ---
    xTaskCreatePinnedToCore(
        TaskSensorPoll,
        "SensorPoll",
        4096,
        NULL,
        2,          // higher priority
        NULL,
        0           // Core 0
    );

    // --- Task pinned to Core 1: MQTT + inference ---
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

// ==================== CORE 0: SENSOR POLLING ====================
void TaskSensorPoll(void* pvParameters) {
    (void)pvParameters;
    const TickType_t frequency = pdMS_TO_TICKS(1000); // 1 Hz

    for (;;) {
        TickType_t xLastWakeTime = xTaskGetTickCount();

        float v = pzem.voltage();
        float i = pzem.current();
        float p = pzem.power();
        float pf = pzem.pf();

        // Validate readings (PZEM returns NaN on comm failure)
        bool valid = !isnan(v) && !isnan(i) && !isnan(p) && !isnan(pf);

        if (valid) {
            xSemaphoreTake(sensorMutex, portMAX_DELAY);
            g_voltage     = v;
            g_current     = i;
            g_activePower = p;
            g_powerFactor = pf;
            g_dataFresh   = true;
            xSemaphoreGive(sensorMutex);
        } else {
            Serial.println("[SENSOR] Invalid PZEM read (NaN)");
        }

        vTaskDelayUntil(&xLastWakeTime, frequency);
    }
}

// ==================== CORE 1: MQTT + INFERENCE ====================
void TaskMqttAndInference(void* pvParameters) {
    (void)pvParameters;

    for (;;) {
        // ----- Non-blocking MQTT reconnect -----
        if (!mqttClient.connected()) {
            reconnectMqtt();
        }
        mqttClient.loop();

        // ----- Process new sensor data -----
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
            vTaskDelay(pdMS_TO_TICKS(50));
            continue;
        }

        // ----- Compute derived quantities -----
        float S = (PF > 0.001f) ? (P / PF) : 0.0f;          // Apparent power
        float Q = computeReactivePower(P, PF);              // Reactive power

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
        // Order must match training exactly:
        // [voltage, current, active_power, power_factor,
        //  apparent_power, reactive_power, delta_P, delta_Q,
        //  current_rolling_var_60s]
        float rawFeatures[9] = {
            V, I, P, PF, S, Q, dP, dQ, var60
        };

        // ----- RobustScaler normalisation -----
        float scaledFeatures[9];
        scaleFeatures(rawFeatures, scaledFeatures);

        // ----- Isolation Forest inference -----
        float anomalyScore = predict_anomaly(scaledFeatures);

        Serial.printf("[INF] V=%.1f I=%.3f P=%.1f PF=%.3f Q=%.1f score=%.4f\n",
                      V, I, P, PF, Q, anomalyScore);

        // ----- Publish if anomaly -----
        if (anomalyScore > ANOMALY_THRESHOLD) {
            StaticJsonDocument<512> doc;
            doc["device_id"] = DEVICE_ID;
            doc["timestamp"] = millis();          // epoch-free uptime ms
            doc["V"]         = serialized(String(V, 2));
            doc["I"]         = serialized(String(I, 3));
            doc["P"]         = serialized(String(P, 2));
            doc["Q"]         = serialized(String(Q, 2));
            doc["PF"]        = serialized(String(PF, 3));
            doc["alert"]     = true;
            doc["score"]     = serialized(String(anomalyScore, 4));

            char payload[512];
            size_t n = serializeJson(doc, payload, sizeof(payload));
            if (n < sizeof(payload) - 1) {
                bool pub = mqttClient.publish(MQTT_TOPIC, payload);
                Serial.printf("[MQTT] Publish %s: %s\n", pub ? "OK" : "FAIL", payload);
            } else {
                Serial.println("[MQTT] Payload overflow!");
            }
        }

        vTaskDelay(pdMS_TO_TICKS(50));
    }
}

// ==================== HELPER FUNCTIONS ====================

float computeReactivePower(float P, float PF) {
    if (PF <= 0.0f || PF > 1.0f) return 0.0f;
    float S = P / PF;
    float diffSq = S * S - P * P;
    if (diffSq < 0.0f) diffSq = 0.0f;  // clamp sensor noise
    return sqrtf(diffSq);
}

float computeRollingVar() {
    if (ringCount == 0) return 0.0f;

    // Two-pass algorithm for numerical stability
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
    return sqDiffSum / n;  // population variance
}

void scaleFeatures(const float raw[9], float scaled[9]) {
    for (int i = 0; i < N_FEATURES; ++i) {
        float denom = SCALER_IQR[i];
        if (denom < 1e-8f) denom = 1e-8f;  // protect div-by-zero
        scaled[i] = (raw[i] - SCALER_MEDIAN[i]) / denom;
    }
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
