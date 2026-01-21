# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Salvavidas** is a real-time voice translation system with speaker identification and intelligent response suggestions. Built using **Clean Architecture** with a Python backend (FastAPI) and multiple client platforms.

## Development Commands

### Backend (Python)

```bash
# Setup virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run web server (development)
python main.py web --reload

# Run web server (production)
python main.py web --host 0.0.0.0 --port 8000

# Run CLI mode (testing)
python main.py cli

# Run tests
pytest
pytest tests/unit/
pytest --cov=src --cov-report=html
```

### Docker Deployment

```bash
cd docker
cp .env.example .env     # Configure environment
./deploy.sh start        # Build and start
./deploy.sh logs -f      # View logs
./deploy.sh status       # Check health
./deploy.sh stop         # Stop services
```

### Desktop App (Electron)

```bash
cd desktop-app
npm install
npm start                # Development
npm run build:linux      # Build for Linux
npm run build:win        # Build for Windows
npm run build:mac        # Build for macOS
```

### Chrome Extension

Load unpacked extension from `chrome-extension/` directory in `chrome://extensions/`

### ESP32 Client

```bash
cd esp32-client
pio run                  # Build
pio run -t upload        # Flash to device
pio device monitor       # Serial monitor
```

## Architecture

### Clean Architecture Layers

```
src/
├── core/                    # Domain Layer (innermost)
│   ├── entities/           # Business objects (AudioChunk, Speaker, ConversationTurn)
│   ├── use_cases/          # Application business rules
│   └── interfaces/         # Port definitions (abstract services)
├── adapters/               # Interface Adapters Layer
│   ├── controllers/        # Handle requests (VoiceController, ConfigController)
│   ├── presenters/         # API endpoints (web_api.py, analytics_api.py)
│   └── gateways/           # External service adapters
└── infrastructure/         # Frameworks & Drivers Layer (outermost)
    ├── services/           # Concrete service implementations
    │   ├── stt/           # Whisper, Deepgram
    │   ├── tts/           # Piper, ElevenLabs
    │   ├── speaker_id/    # Pyannote
    │   ├── translation/   # Helsinki-NLP, DeepL
    │   ├── llm/           # Llama.cpp, OpenAI
    │   └── ...
    ├── database.py        # SQLite via SQLAlchemy
    └── service_factory.py # Creates services based on ProcessingMode
```

### Processing Modes

The `ServiceFactory` creates different service implementations based on `ProcessingMode`:

| Mode | STT | Translation | LLM | Cost |
|------|-----|-------------|-----|------|
| `local` | Whisper v3-turbo | Helsinki-NLP | Llama.cpp | Free |
| `api_fast` | Deepgram Nova | DeepL | GPT-3.5 | $ |
| `api_premium` | Deepgram Nova-2 | DeepL | GPT-4 | $$$ |

### Key Data Flow

1. Audio arrives via WebSocket (`/ws/voice`) as binary PCM data
2. `VoiceTranslationController` creates `AudioChunk` entity
3. `ProcessVoiceTranslationUseCase` orchestrates: STT → Speaker ID → Translation → LLM suggestions
4. Results sent back as JSON with transcription, translation, speaker info, and suggestions

## Project Structure

```
Salvavidas/
├── src/                     # Python backend (Clean Architecture)
├── frontend/                # Web UI (HTML/JS/CSS)
├── desktop-app/             # Electron app (Windows/Mac/Linux)
├── chrome-extension/        # Browser extension (Meet/Zoom/Teams)
├── esp32-client/            # ESP32-S3 firmware (PlatformIO)
├── android-client/          # Android app (Kotlin, WIP)
├── docker/                  # Docker deployment configs
├── config/settings.py       # Pydantic settings model
├── main.py                  # Entry point
└── tests/                   # Unit and integration tests
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main web interface |
| `/analytics` | GET | Analytics dashboard |
| `/speakers` | GET | Speaker management page |
| `/health` | GET | Health check |
| `/api/config` | GET/POST | Configuration CRUD |
| `/api/speakers` | GET | List known speakers |
| `/api/speakers/name` | POST | Name a speaker |
| `/api/speakers/enroll` | POST | Start enrollment session |
| `/ws/voice` | WebSocket | Real-time audio streaming |

## WebSocket Protocol

**Client → Server:** Binary PCM audio (16-bit, 16kHz, mono)

**Server → Client:** JSON messages:
```json
{
  "type": "transcription",
  "speaker_id": "speaker_001",
  "speaker_name": "John",
  "original_text": "Hello world",
  "translated_text": "Olá mundo",
  "source_language": "en",
  "target_language": "pt",
  "suggestions": [{"text": "...", "confidence": 0.9}],
  "performance": {"stt_latency_ms": 350, "total_latency_ms": 500}
}
```

## Configuration

Settings are managed via:
1. Environment variables (`.env` file)
2. `config/settings.py` (Pydantic model with defaults)
3. SQLite database (runtime overrides)

Key settings:
- `PROCESSING_MODE`: local | api_fast | api_premium
- `WHISPER_MODEL`: tiny | base | small | medium | large-v3
- `TARGET_LANGUAGE`: en | pt | es | fr | de | ...
- `ENABLE_SPEAKER_ID`: true | false
- `ENABLE_SUGGESTIONS`: true | false

## Service Interfaces

All services implement interfaces from `src/core/interfaces/services.py`:

- `ISpeechToTextService` - `transcribe(audio) -> Transcription`
- `ISpeakerIdentificationService` - `identify(audio) -> Speaker`
- `ITranslationService` - `translate(text, target_lang) -> Translation`
- `ILanguageModelService` - `generate_suggestions(context) -> List[Suggestion]`
- `ITextToSpeechService` - `synthesize(text) -> AudioData`

## Docker Volumes

```
salvavidas_speaker-data   # Speaker profiles and embeddings
salvavidas_analytics-data # Usage analytics
salvavidas_model-cache    # AI models (~6-7GB)
```

## Testing

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/unit/test_voice_controller.py

# Integration tests
pytest tests/integration/
```
