# 🚁 Salvavidas - Chrome Extension

AI-powered meeting assistant extension for Google Meet, Zoom, and Microsoft Teams.

## Features

✅ **Real-time Transcription** - Live speech-to-text during meetings
✅ **Speaker Identification** - Automatic speaker detection
✅ **Multi-language Translation** - Translate conversations in real-time
✅ **Sentiment Analysis** - Understand emotional context
✅ **Smart Suggestions** - AI-powered response recommendations
✅ **Objection Handling** - Detect and counter objections
✅ **Meeting Summaries** - Auto-generated action items and key points
✅ **Invisible Overlay** - Works seamlessly without disrupting screen sharing

## Installation

### Prerequisites

1. **Backend Server Running**
   ```bash
   cd /path/to/Salvavidas
   python main.py web --host 0.0.0.0 --port 8000
   ```

2. **Chrome Browser** (version 88 or higher)

### Install Extension

#### Method 1: Load Unpacked (Development)

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `chrome-extension` folder from this repository
5. The extension icon should appear in your toolbar

#### Method 2: Pack and Install (Production-like)

1. In `chrome://extensions/`, click "Pack extension"
2. Select the `chrome-extension` folder
3. Click "Pack extension" (creates a .crx file)
4. Drag the .crx file into Chrome to install

## Usage

### Quick Start

1. **Start Backend Server**
   ```bash
   python main.py web
   ```

2. **Open a Meeting**
   - Go to Google Meet, Zoom, or Teams
   - Join or start a meeting

3. **Activate Extension**
   - Click the Salvavidas icon in toolbar
   - Click "Start Assistant"
   - Grant microphone permissions when prompted

4. **Use the Overlay**
   - The overlay appears in the top-right corner
   - Drag to reposition if needed
   - Click minimize (-) to collapse
   - Click the recording button to pause/resume

### Configuration

Click the extension icon to open settings:

#### Backend URL
- Default: `ws://localhost:8000/ws`
- Change if running on different host/port

#### Mode
- **Meeting Assistant** (recommended): Full features including sentiment, suggestions, summaries
- **Translator Only**: Just transcription and translation

#### Processing Mode
- **Local** (Free): Runs on your machine, slower but private
- **API Fast** ($$): Balanced speed and quality
- **API Premium** ($$$): Best quality, requires API keys

#### Target Language
- Choose the language you want translations in
- Supports 30+ languages

#### Auto-start
- Enable to automatically start when joining meetings

## Features Explained

### Real-time Transcription
- Live speech-to-text as people speak
- Speaker identification with labels
- Timestamps for each segment

### Translation
- Automatic language detection
- Instant translation to your preferred language
- Shown below each transcription

### Sentiment Analysis
- 8 sentiment types: Very Positive, Positive, Neutral, Negative, Very Negative, Confused, Concerned, Excited
- Confidence scores
- Real-time emotional tracking

### Smart Suggestions
- 8 types of suggestions:
  - Sales (persuasive responses)
  - Objection Handling (counter-arguments)
  - Negotiation (strategic positioning)
  - Clarification (follow-up questions)
  - Closing (next steps)
  - Empathy (emotional connection)
  - Technical (detailed explanations)
  - General (engagement)

### Objection Detection
Automatically detects 4 types of objections:
- **Price**: Cost concerns, budget issues
- **Timeline**: Time constraints, urgency
- **Features**: Functionality requests, missing capabilities
- **Competitor**: Comparison with alternatives

### Meeting Stats
- Meeting duration
- Number of speakers
- Overall sentiment trend

### Privacy Features
- Overlay is invisible to screen sharing
- All audio processing can be done locally
- No data stored unless configured

## Keyboard Shortcuts

- `Ctrl+Shift+S` (Windows/Linux) or `Cmd+Shift+S` (Mac): Start/stop recording
- `Ctrl+Shift+O`: Toggle overlay visibility

*Configure shortcuts in `chrome://extensions/shortcuts`*

## Supported Platforms

✅ **Google Meet** - `meet.google.com`
✅ **Zoom** - `*.zoom.us`
✅ **Microsoft Teams** - `teams.microsoft.com`

## Troubleshooting

### Extension Not Working

1. **Check Backend Status**
   - Open extension popup
   - Click "Test Connection"
   - Ensure backend is running on correct port

2. **Microphone Permissions**
   - Chrome may block microphone access
   - Click the camera icon in address bar
   - Allow microphone access

3. **WebSocket Connection Failed**
   - Check firewall settings
   - Verify backend URL in settings
   - Try `ws://127.0.0.1:8000/ws` instead of `localhost`

### Overlay Not Appearing

1. **Refresh the meeting page**
2. **Check if content script loaded**
   - Right-click page → "Inspect"
   - Look for `[Salvavidas]` logs in console
3. **Reinstall extension**

### Audio Not Capturing

1. **Check browser permissions**
   - `chrome://settings/content/microphone`
   - Ensure Chrome can access microphone
2. **Check meeting platform audio**
   - Some platforms block tab audio capture
   - Use desktop app version instead

### Poor Transcription Quality

1. **Switch to API mode**
   - Local mode uses smaller models
   - API Premium provides best accuracy
2. **Check audio quality**
   - Ensure good microphone input
   - Reduce background noise
3. **Verify language settings**
   - Auto-detection works best with clear speech

## Architecture

```
chrome-extension/
├── manifest.json          # Extension configuration (Manifest V3)
├── background/
│   └── service-worker.js  # Background processes & state management
├── content/
│   ├── content.js         # Injected into meeting pages
│   └── overlay.css        # Overlay styling
├── popup/
│   ├── popup.html         # Settings UI
│   └── popup.js           # Settings logic
└── icons/                 # Extension icons (16x16, 48x48, 128x128)
```

## API Integration

The extension communicates with the Salvavidas backend via WebSocket:

```javascript
// Connect to backend
ws = new WebSocket('ws://localhost:8000/ws');

// Send audio chunks
ws.send(JSON.stringify({
  type: 'audio',
  data: base64Audio,
  format: 'webm'
}));

// Receive results
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // data.type: 'transcription', 'translation', 'sentiment', 'suggestions', etc.
};
```

## Development

### File Structure

- **manifest.json**: Extension metadata and permissions
- **background/service-worker.js**: Manages extension lifecycle, settings, alarms
- **content/content.js**: Injected into meeting pages, handles audio capture and UI
- **content/overlay.css**: Styles for the overlay interface
- **popup/popup.html**: Settings panel UI
- **popup/popup.js**: Settings logic and controls

### Testing

1. Make changes to files
2. Go to `chrome://extensions/`
3. Click reload button on Salvavidas extension
4. Refresh meeting page to see changes

### Debugging

**Background Script:**
- `chrome://extensions/` → Click "service worker" link

**Content Script:**
- Right-click meeting page → "Inspect"
- Check console for `[Salvavidas]` logs

**Popup:**
- Right-click extension icon → "Inspect popup"

## Privacy & Security

- ✅ All audio processing is configurable (local or API)
- ✅ No data is stored without explicit configuration
- ✅ WebSocket connections use localhost by default
- ✅ Microphone access requires user permission
- ✅ Open source - audit the code yourself

## Contributing

Found a bug or want to add a feature?

1. Open an issue on GitHub
2. Submit a pull request
3. Join the discussion

## License

Same license as the main Salvavidas project.

## Support

- 📖 [Full Documentation](https://github.com/marvinmvns/Salvavidas#readme)
- 🐛 [Report Issues](https://github.com/marvinmvns/Salvavidas/issues)
- 💬 [Discussions](https://github.com/marvinmvns/Salvavidas/discussions)

---

**Made with ❤️ by the Salvavidas Team**
