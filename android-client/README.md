# 🚁 Salvavidas Android Audio Client

Simple, ultra low-latency audio streaming client for Android.

## Features

- ✅ Real-time microphone capture
- ✅ WebSocket streaming to Salvavidas server
- ✅ Ultra-low latency (~80-120ms)
- ✅ Simple, clean UI
- ✅ Real-time statistics
- ✅ Automatic reconnection
- ✅ SERVANT mode - audio only, no processing

## Requirements

- **Android**: 7.0+ (API 24+)
- **Microphone**: Required
- **Internet**: WiFi or mobile data
- **Server**: Salvavidas backend running

## Installation

### Build from Source

1. **Clone Repository**:
   ```bash
   cd android-client
   ```

2. **Open in Android Studio**:
   - File → Open → Select `android-client` folder
   - Wait for Gradle sync

3. **Build APK**:
   - Build → Build Bundle(s) / APK(s) → Build APK(s)
   - APK will be in `app/build/outputs/apk/debug/`

4. **Install on Device**:
   ```bash
   adb install app/build/outputs/apk/debug/app-debug.apk
   ```

### Direct Install (Pre-built APK)

Download latest APK from releases and install on your Android device.

## Usage

### First Launch

1. **Grant Microphone Permission**
   - App will request microphone access
   - REQUIRED for audio capture

2. **Configure Server**
   - Enter server URL: `ws://YOUR_SERVER_IP:8000/ws`
   - Example: `ws://192.168.1.100:8000/ws`

3. **Connect**
   - Tap "Connect" button
   - Wait for "✓ Connected to server"

4. **Start Streaming**
   - Tap "Start" button
   - Speak into microphone
   - Monitor statistics

5. **Stop Streaming**
   - Tap "Stop" button when done

### Connection Tips

#### Local Network
```
ws://192.168.1.100:8000/ws
```

#### Public Server
```
wss://your-domain.com/ws
```

#### With Authentication (if configured)
```
ws://192.168.1.100:8000/ws?token=YOUR_TOKEN
```

## Configuration

### Audio Settings

Located in `MainActivity.kt`:

```kotlin
private const val SAMPLE_RATE = 16000  // 16kHz
private const val CHANNEL_CONFIG = AudioFormat.CHANNEL_IN_MONO
private const val AUDIO_FORMAT = AudioFormat.ENCODING_PCM_16BIT
private const val CHUNK_SIZE = 1024  // Samples per packet
```

### Network Settings

```kotlin
private const val DEFAULT_SERVER_URL = "ws://192.168.1.100:8000/ws"
```

## UI Elements

### Server URL Input
- Enter WebSocket URL of Salvavidas server
- Format: `ws://host:port/path` or `wss://host:port/path`

### Connect Button
- Connects/disconnects to server
- Shows connection status

### Start Button
- Starts audio capture and streaming
- Enabled only when connected

### Stop Button
- Stops audio capture
- Enabled only when recording

### Status Display
- Shows current connection/recording status
- Updates in real-time

### Statistics Display
- **Packets sent**: Number of audio packets transmitted
- **Data sent**: Total data in KB
- **Rate**: Packets per second
- **Bitrate**: Network bitrate in kbps
- **Duration**: Recording duration

## Permissions

### Required
- **RECORD_AUDIO**: Microphone access
- **INTERNET**: Network communication
- **ACCESS_NETWORK_STATE**: Check connectivity

### Optional
- **MODIFY_AUDIO_SETTINGS**: Audio optimization (future)

## Performance

- **Latency**: ~80-120ms (device dependent)
- **Sample Rate**: 16kHz
- **Bit Depth**: 16-bit PCM
- **Channels**: Mono
- **Bandwidth**: ~256 kbps
- **Battery**: ~5-8% per hour (varies)

## Troubleshooting

### Microphone Permission Denied
1. Go to Settings → Apps → Salvavidas Audio
2. Permissions → Microphone → Allow

### Cannot Connect
- Verify server URL is correct
- Check server is running: `python main.py web`
- Ensure device and server on same network
- Check firewall settings
- Try ping server IP

### Audio Quality Issues
- Ensure quiet environment
- Hold device ~30cm from mouth
- Check network stability
- Reduce background noise

### High Latency
- Use WiFi instead of mobile data
- Move closer to WiFi router
- Reduce server load
- Check server processing mode

### App Crashes
- Check Android version (7.0+)
- Clear app cache
- Reinstall app
- Check logcat: `adb logcat | grep Salvavidas`

## Battery Optimization

### Recommended Settings
1. **Keep screen on during use**
   - Prevents Android from throttling

2. **Disable battery optimization**
   - Settings → Apps → Salvavidas → Battery → Unrestricted

3. **Use WiFi over mobile data**
   - Lower power consumption
   - More stable connection

## Development

### Project Structure
```
android-client/
├── app/
│   ├── src/main/
│   │   ├── java/com/salvavidas/audioclient/
│   │   │   └── MainActivity.kt
│   │   ├── res/
│   │   │   ├── layout/activity_main.xml
│   │   │   ├── values/colors.xml
│   │   │   └── values/strings.xml
│   │   └── AndroidManifest.xml
│   └── build.gradle
└── build.gradle
```

### Dependencies
- **AndroidX**: Core libraries
- **Material Design**: UI components
- **Kotlin Coroutines**: Async operations
- **OkHttp**: WebSocket client

### Building Release APK

1. **Generate Keystore**:
   ```bash
   keytool -genkey -v -keystore release.keystore \
     -alias salvavidas -keyalg RSA -keysize 2048 -validity 10000
   ```

2. **Build Release**:
   ```bash
   ./gradlew assembleRelease
   ```

3. **Sign APK**:
   ```bash
   jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 \
     -keystore release.keystore \
     app/build/outputs/apk/release/app-release-unsigned.apk salvavidas
   ```

## Customization

### Change App Name
Edit `app/src/main/res/values/strings.xml`:
```xml
<string name="app_name">Your App Name</string>
```

### Change Colors
Edit `app/src/main/res/values/colors.xml`:
```xml
<color name="primary">#YOUR_COLOR</color>
```

### Change Icon
Replace files in `app/src/main/res/mipmap-*/`

## License

Same license as Salvavidas main project.

## Support

- Documentation: [Main README](../README.md)
- Issues: [GitHub Issues](https://github.com/marvinmvns/Salvavidas/issues)
