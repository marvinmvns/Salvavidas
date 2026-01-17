/**
 * Salvavidas ESP32-S3 Audio Client
 * Ultra low-latency audio capture and streaming
 *
 * Hardware: ESP32-S3 with I2S microphone (INMP441 or similar)
 * Purpose: Capture audio and stream to Salvavidas server via WebSocket
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WebSocketsClient.h>
#include <driver/i2s.h>
#include <ArduinoJson.h>

// ============================================================
// CONFIGURATION - EDIT THESE VALUES
// ============================================================

// WiFi Configuration
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// Server Configuration
const char* SERVER_HOST = "192.168.1.100";  // Your Salvavidas server IP
const uint16_t SERVER_PORT = 8000;
const char* SERVER_PATH = "/ws";

// Audio Configuration
#define SAMPLE_RATE 16000      // 16kHz - optimal for speech
#define SAMPLE_BITS 16         // 16-bit audio
#define CHANNELS 1             // Mono audio
#define DMA_BUFFER_COUNT 8     // Number of DMA buffers
#define DMA_BUFFER_SIZE 1024   // Size of each DMA buffer

// I2S Pins (adjust for your board)
#define I2S_WS_PIN 15          // Word Select (LRCLK)
#define I2S_SCK_PIN 14         // Bit Clock (BCLK)
#define I2S_SD_PIN 32          // Serial Data (DOUT)

// Streaming Configuration
#define CHUNK_SIZE 1024        // Audio chunk size to send
#define SEND_INTERVAL_MS 100   // Send every 100ms for low latency

// ============================================================
// GLOBAL VARIABLES
// ============================================================

WebSocketsClient webSocket;
bool isConnected = false;
bool isStreaming = false;

// Audio buffers
int16_t audioBuffer[CHUNK_SIZE];
size_t bufferIndex = 0;

// Statistics
unsigned long packetsent = 0;
unsigned long lastStatsPrint = 0;

// ============================================================
// I2S CONFIGURATION
// ============================================================

void setupI2S() {
    Serial.println("[I2S] Initializing I2S microphone...");

    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate = SAMPLE_RATE,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = DMA_BUFFER_COUNT,
        .dma_buf_len = DMA_BUFFER_SIZE,
        .use_apll = false,
        .tx_desc_auto_clear = false,
        .fixed_mclk = 0
    };

    i2s_pin_config_t pin_config = {
        .bck_io_num = I2S_SCK_PIN,
        .ws_io_num = I2S_WS_PIN,
        .data_out_num = I2S_PIN_NO_CHANGE,
        .data_in_num = I2S_SD_PIN
    };

    esp_err_t err = i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
    if (err != ESP_OK) {
        Serial.printf("[I2S] ERROR: Failed to install driver: %d\n", err);
        return;
    }

    err = i2s_set_pin(I2S_NUM_0, &pin_config);
    if (err != ESP_OK) {
        Serial.printf("[I2S] ERROR: Failed to set pins: %d\n", err);
        return;
    }

    // Clear DMA buffers
    i2s_zero_dma_buffer(I2S_NUM_0);

    Serial.println("[I2S] ✓ I2S initialized successfully");
    Serial.printf("[I2S] Sample Rate: %d Hz\n", SAMPLE_RATE);
    Serial.printf("[I2S] Channels: %d\n", CHANNELS);
    Serial.printf("[I2S] Bits: %d\n", SAMPLE_BITS);
}

// ============================================================
// WIFI CONNECTION
// ============================================================

void connectWiFi() {
    Serial.println("[WiFi] Connecting to WiFi...");
    Serial.printf("[WiFi] SSID: %s\n", WIFI_SSID);

    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 30) {
        delay(500);
        Serial.print(".");
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println();
        Serial.println("[WiFi] ✓ Connected!");
        Serial.printf("[WiFi] IP Address: %s\n", WiFi.localIP().toString().c_str());
        Serial.printf("[WiFi] Signal: %d dBm\n", WiFi.RSSI());
    } else {
        Serial.println();
        Serial.println("[WiFi] ✗ Failed to connect!");
    }
}

// ============================================================
// WEBSOCKET HANDLERS
// ============================================================

void webSocketEvent(WStype_t type, uint8_t* payload, size_t length) {
    switch (type) {
        case WStype_DISCONNECTED:
            Serial.println("[WS] Disconnected");
            isConnected = false;
            isStreaming = false;
            break;

        case WStype_CONNECTED:
            Serial.printf("[WS] Connected to %s:%d%s\n", SERVER_HOST, SERVER_PORT, SERVER_PATH);
            isConnected = true;

            // Send ready signal
            webSocket.sendTXT("{\"type\":\"client_ready\",\"device\":\"ESP32-S3\"}");

            // Start streaming after 1 second
            delay(1000);
            isStreaming = true;
            Serial.println("[WS] ✓ Ready to stream audio");
            break;

        case WStype_TEXT:
            Serial.printf("[WS] Received text: %s\n", payload);
            // Handle server responses (transcriptions, translations, etc.)
            break;

        case WStype_BIN:
            // Binary data from server (TTS audio, etc.)
            Serial.printf("[WS] Received binary data: %d bytes\n", length);
            break;

        case WStype_ERROR:
            Serial.printf("[WS] Error: %s\n", payload);
            break;

        case WStype_PING:
            Serial.println("[WS] Ping");
            break;

        case WStype_PONG:
            Serial.println("[WS] Pong");
            break;
    }
}

void connectWebSocket() {
    Serial.println("[WS] Connecting to WebSocket server...");
    Serial.printf("[WS] Host: %s:%d\n", SERVER_HOST, SERVER_PORT);
    Serial.printf("[WS] Path: %s\n", SERVER_PATH);

    webSocket.begin(SERVER_HOST, SERVER_PORT, SERVER_PATH);
    webSocket.onEvent(webSocketEvent);

    // Configure WebSocket
    webSocket.setReconnectInterval(5000);  // Reconnect every 5s if disconnected
    webSocket.enableHeartbeat(15000, 3000, 2);  // Ping every 15s, timeout 3s, 2 retries
}

// ============================================================
// AUDIO CAPTURE & STREAMING
// ============================================================

void captureAndStreamAudio() {
    if (!isConnected || !isStreaming) {
        return;
    }

    size_t bytesRead = 0;
    int16_t i2sData[CHUNK_SIZE];

    // Read from I2S
    esp_err_t result = i2s_read(
        I2S_NUM_0,
        (void*)i2sData,
        CHUNK_SIZE * sizeof(int16_t),
        &bytesRead,
        portMAX_DELAY
    );

    if (result != ESP_OK) {
        Serial.printf("[I2S] Read error: %d\n", result);
        return;
    }

    if (bytesRead == 0) {
        return;
    }

    // Convert to mono if needed and copy to buffer
    size_t samplesRead = bytesRead / sizeof(int16_t);

    for (size_t i = 0; i < samplesRead && bufferIndex < CHUNK_SIZE; i++) {
        // Apply simple noise gate (-30dB threshold)
        int16_t sample = i2sData[i];
        if (abs(sample) < 100) {  // ~-50dB
            sample = 0;
        }

        audioBuffer[bufferIndex++] = sample;
    }

    // Send chunk when buffer is full
    if (bufferIndex >= CHUNK_SIZE) {
        // Send as binary WebSocket message
        webSocket.sendBIN((uint8_t*)audioBuffer, CHUNK_SIZE * sizeof(int16_t));

        packetsent++;
        bufferIndex = 0;

        // Print stats every 10 seconds
        if (millis() - lastStatsPrint > 10000) {
            Serial.printf("[Stats] Packets sent: %lu | Rate: %.1f pkt/s\n",
                         packetsent,
                         packetsent / ((millis() - lastStatsPrint) / 1000.0));
            lastStatsPrint = millis();
        }
    }
}

// ============================================================
// ARDUINO SETUP & LOOP
// ============================================================

void setup() {
    // Initialize Serial
    Serial.begin(115200);
    delay(1000);

    Serial.println();
    Serial.println("╔════════════════════════════════════════╗");
    Serial.println("║  🚁 Salvavidas ESP32-S3 Audio Client  ║");
    Serial.println("║     Ultra Low-Latency Streaming        ║");
    Serial.println("╚════════════════════════════════════════╝");
    Serial.println();

    // Initialize I2S microphone
    setupI2S();

    // Connect to WiFi
    connectWiFi();

    // Connect to WebSocket server
    if (WiFi.status() == WL_CONNECTED) {
        connectWebSocket();
    } else {
        Serial.println("[ERROR] Cannot connect to server - WiFi not connected");
    }

    lastStatsPrint = millis();

    Serial.println();
    Serial.println("✓ Setup complete - starting audio capture...");
    Serial.println();
}

void loop() {
    // Handle WebSocket events
    webSocket.loop();

    // Capture and stream audio
    captureAndStreamAudio();

    // Small delay to prevent watchdog timeout
    delay(1);
}
