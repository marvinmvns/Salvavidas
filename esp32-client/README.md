# 🚁 Salvavidas ESP32-S3 Audio Client

Ultra low-latency audio capture and streaming client for ESP32-S3.

## Features

- ✅ Real-time audio capture via I2S microphone
- ✅ WebSocket streaming to Salvavidas server
- ✅ Ultra-low latency (~100ms)
- ✅ Automatic WiFi reconnection
- ✅ WebSocket heartbeat and auto-reconnect
- ✅ Simple noise gate
- ✅ LED status indicators

## Hardware Requirements

### ESP32-S3 Board
- ESP32-S3-DevKitC-1 (or compatible)
- Minimum 8MB Flash
- PSRAM recommended

### I2S Microphone (INMP441 or similar)
- **WS (Word Select)** → GPIO 15
- **SCK (Bit Clock)** → GPIO 14
- **SD (Serial Data)** → GPIO 32
- **VDD** → 3.3V
- **GND** → GND

## Software Requirements

- [PlatformIO](https://platformio.org/) (recommended)
- OR [Arduino IDE](https://www.arduino.cc/) with ESP32 support

## Installation

### Using PlatformIO (Recommended)

1. **Install PlatformIO**:
   ```bash
   # VS Code extension or CLI
   pip install platformio
   ```

2. **Clone and Configure**:
   ```bash
   cd esp32-client
   ```

3. **Edit Configuration** in `src/main.cpp`:
   ```cpp
   const char* WIFI_SSID = "YOUR_WIFI_SSID";
   const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
   const char* SERVER_HOST = "192.168.1.100";  // Your server IP
   ```

4. **Adjust I2S Pins** if needed:
   ```cpp
   #define I2S_WS_PIN 15
   #define I2S_SCK_PIN 14
   #define I2S_SD_PIN 32
   ```

5. **Build and Upload**:
   ```bash
   pio run --target upload
   ```

6. **Monitor Serial**:
   ```bash
   pio device monitor
   ```

### Using Arduino IDE

1. Install ESP32 board support
2. Install libraries:
   - WebSockets by Markus Sattler
   - ArduinoJson by Benoit Blanchon
3. Open `src/main.cpp` in Arduino IDE
4. Select board: "ESP32S3 Dev Module"
5. Configure settings and upload

## Configuration

### Audio Settings

```cpp
#define SAMPLE_RATE 16000      // 16kHz (optimal for speech)
#define SAMPLE_BITS 16         // 16-bit audio
#define CHANNELS 1             // Mono
#define CHUNK_SIZE 1024        // Samples per packet
```

### Network Settings

```cpp
#define SERVER_HOST "192.168.1.100"
#define SERVER_PORT 8000
#define SERVER_PATH "/ws"
```

## Usage

1. Power on ESP32-S3
2. Device connects to WiFi automatically
3. Device connects to WebSocket server
4. Starts streaming audio automatically
5. Monitor via serial console:
   ```
   [WiFi] Connected! IP: 192.168.1.123
   [WS] Connected to server
   [WS] ✓ Ready to stream audio
   [Stats] Packets sent: 1234 | Rate: 10.2 pkt/s
   ```

## Troubleshooting

### WiFi not connecting
- Check SSID and password
- Ensure 2.4GHz WiFi (ESP32 doesn't support 5GHz)
- Check signal strength

### WebSocket fails
- Verify server IP and port
- Ensure server is running
- Check firewall settings

### No audio / Poor quality
- Check I2S wiring
- Verify microphone power (3.3V)
- Check pin assignments
- Try different microphone

### Watchdog timeout
- Reduce `CHUNK_SIZE`
- Increase `SEND_INTERVAL_MS`
- Check for blocking code

## Performance

- **Latency**: ~100-150ms end-to-end
- **Sample Rate**: 16kHz
- **Bit Depth**: 16-bit PCM
- **Bandwidth**: ~256 kbps
- **Power**: ~150mA @ 3.3V (WiFi active)

## LED Indicators

If you add LEDs to the board:
- **WiFi LED**: Blinks during connection, solid when connected
- **Stream LED**: Blinks when sending data

## Pinout Reference

```
ESP32-S3          INMP441
---------         --------
GPIO 15    →      WS (LRCLK)
GPIO 14    →      SCK (BCLK)
GPIO 32    →      SD (DOUT)
3.3V       →      VDD
GND        →      GND
                  L/R → GND (for left channel)
```

## Advanced Configuration

### Power Saving Mode

To enable power saving (reduces WiFi power but may increase latency):

```cpp
WiFi.setSleep(WIFI_PS_MIN_MODEM);  // Minimum modem sleep
```

### Custom Audio Processing

Add processing in `captureAndStreamAudio()`:

```cpp
// Apply gain
sample = sample * 2;

// Apply filtering
// ... your code here
```

## License

Same license as Salvavidas main project.

## Support

- Documentation: [Main README](../README.md)
- Issues: [GitHub Issues](https://github.com/marvinmvns/Salvavidas/issues)
