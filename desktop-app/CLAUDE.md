# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **Electron desktop application** for Salvavidas, a real-time voice translation assistant. The desktop app provides an invisible overlay for screen sharing scenarios (Zoom, Meet, Teams) and integrates with a Python backend via WebSocket.

This is part of the larger Salvavidas monorepo located at `../`. The backend Python server must be running for full functionality.

## Development Commands

```bash
# Install dependencies
npm install

# Run in development mode
npm start

# Build for production
npm run build:win    # Windows (.exe)
npm run build:mac    # macOS (.dmg)
npm run build:linux  # Linux (.AppImage, .deb, .rpm)

# Package without full build (for testing)
npm run pack
```

**Note:** The app requires `--no-sandbox` flag (already included in `npm start`).

## Starting the Full Stack

1. Start the Python backend first:
   ```bash
   cd ..
   python main.py web  # Runs on localhost:8000
   ```

2. Then start the desktop app:
   ```bash
   npm start
   ```

## Architecture

### Process Model (Electron)

- **Main Process** (`src/main.js`): Window management, system tray, global shortcuts, IPC handlers, Teams detection orchestration
- **Preload Script** (`src/preload.js`): Secure bridge exposing `window.electronAPI` to renderer processes
- **Renderer Processes**: Overlay window (`public/overlay.html`) and settings window (`public/settings.html`)

### Key Modules

| File | Purpose |
|------|---------|
| `src/main.js` | Main process - creates windows, tray, shortcuts, handles IPC |
| `src/preload.js` | Context bridge - exposes safe API to renderer via `contextBridge` |
| `src/teams-detector.js` | Cross-platform Teams meeting detection (polls every 5s) |
| `src/audio-capture.js` | Audio capture manager (microphone + system audio mixing) |
| `public/overlay.html` | Invisible overlay UI with audio controls and suggestions display |
| `public/settings.html` | Settings UI with tabs for general, AI, audio, Teams config |
| `public/audio-client.js` | WebSocket client for streaming audio to backend |

### IPC Communication

The preload script exposes these methods via `window.electronAPI`:

```javascript
// Config & Settings
getConfig(), setConfig(key, value)
getSettings(), saveSettings(settings)
clearCache(), clearSpeakers()

// Controls
toggleOverlay(), toggleInvisible()

// Events (from main process)
on('teams-meeting-started', callback)
on('teams-meeting-ended', callback)
```

### Invisible Mode Implementation

The overlay window is configured to be invisible to screen capture:
- Uses `type: 'panel'` window type
- `skipTaskbar: true`
- Windows: `setAlwaysOnTop(true, 'screen-saver')`
- macOS: `vibrancy: 'ultra-dark'`

## Global Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+O` | Toggle overlay |
| `Ctrl+Shift+I` | Toggle invisible mode |
| `Ctrl+Shift+S` | Show/hide main window |
| `Ctrl+Shift+H` | Hide all windows |
| `Ctrl+,` | Open settings |

## Backend Communication

The app connects to `ws://localhost:8000/ws/voice` for real-time audio streaming and receives:
- Transcription results
- Speaker identification
- Suggestion responses
- Performance metrics (latency)

Settings are persisted locally using `electron-store`.

## Teams Detection

`TeamsDetector` class polls for Teams meetings using platform-specific methods:
- **Windows**: PowerShell to query `Teams.exe` process and window titles
- **macOS**: AppleScript to check "Microsoft Teams" process windows
- **Linux**: `ps aux` + `wmctrl`/`xdotool` for window titles

Emits `meeting-started` and `meeting-ended` events.

## Build Output

Built binaries are placed in `dist/`:
- Windows: NSIS installer + portable exe
- macOS: .dmg + .zip
- Linux: .AppImage, .deb, .rpm
