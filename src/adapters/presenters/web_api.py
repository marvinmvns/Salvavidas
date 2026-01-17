"""FastAPI web API for frontend."""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import json
from datetime import datetime

from ...infrastructure.database import Database
from ...infrastructure.service_factory import ServiceFactory
from ..controllers import VoiceTranslationController, ConfigController
from ...core.use_cases import ProcessVoiceTranslationUseCase
from ...core.entities import AudioChunk
from config.settings import get_settings
from ...infrastructure.services.analytics import AnalyticsService
from .analytics_api import create_analytics_router


app = FastAPI(
    title="Salvavidas Voice Translation",
    description="Real-time voice translation with speaker identification",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Global instances
database: Database = None
config_controller: ConfigController = None
analytics_service: AnalyticsService = None


class ConfigUpdate(BaseModel):
    """Configuration update model."""
    key: str
    value: Any
    category: Optional[str] = "general"


class SpeakerEnrollment(BaseModel):
    """Speaker enrollment model."""
    speaker_name: str
    audio_duration_seconds: int = 10


@app.on_event("startup")
async def startup():
    """Initialize application."""
    global database, config_controller, analytics_service

    # Initialize database
    database = Database()
    await database.init_db()

    # Initialize config controller
    config_controller = ConfigController(database)

    # Initialize analytics service
    analytics_service = AnalyticsService()

    # Mount analytics router
    analytics_router = create_analytics_router(analytics_service)
    app.include_router(analytics_router)


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    if database:
        await database.close()


@app.get("/", response_class=HTMLResponse)
async def get_index():
    """Serve frontend."""
    with open("frontend/index.html", "r") as f:
        return f.read()


@app.get("/analytics", response_class=HTMLResponse)
async def get_analytics():
    """Serve analytics dashboard."""
    with open("frontend/analytics.html", "r") as f:
        return f.read()


@app.get("/api/config")
async def get_all_configs():
    """Get all configurations."""
    configs = await config_controller.get_all_configs()
    return JSONResponse(configs)


@app.get("/api/config/{key}")
async def get_config(key: str):
    """Get specific configuration."""
    value = await config_controller.get_config(key)
    if value is None:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return JSONResponse({"key": key, "value": value})


@app.post("/api/config")
async def update_config(config: ConfigUpdate):
    """Update configuration."""
    await config_controller.set_config(config.key, config.value, config.category)
    return JSONResponse({"status": "success", "key": config.key})


@app.post("/api/config/reset")
async def reset_configs():
    """Reset configurations to defaults."""
    await config_controller.reset_to_defaults()
    return JSONResponse({"status": "success"})


@app.get("/api/speakers")
async def get_speakers():
    """Get all known speakers."""
    speakers = await database.get_all_speakers()
    return JSONResponse([
        {
            "speaker_id": s.speaker_id,
            "name": s.name,
            "language": s.language,
            "confidence": s.confidence
        }
        for s in speakers
    ])


@app.websocket("/ws/voice")
async def websocket_voice_translation(websocket: WebSocket):
    """WebSocket endpoint for real-time voice translation."""
    await websocket.accept()

    try:
        # Get settings
        settings = get_settings()
        configs = await config_controller.get_all_configs()

        # Update settings from database
        for key, value in configs.items():
            if hasattr(settings, key):
                setattr(settings, key, value)

        # Create services
        use_intel_gpu = configs.get("use_intel_gpu", False)
        factory = ServiceFactory(settings, use_intel_gpu=use_intel_gpu)

        # Create use case
        use_case = ProcessVoiceTranslationUseCase(
            stt_service=factory.create_stt_service(),
            speaker_id_service=factory.create_speaker_id_service(),
            translation_service=factory.create_translation_service(),
            llm_service=factory.create_llm_service(),
            target_language=settings.target_language,
            enable_speaker_id=settings.enable_speaker_id,
            enable_suggestions=settings.enable_suggestions,
        )

        # Create controller
        controller = VoiceTranslationController(use_case, database)
        await controller.initialize()

        # Send ready signal
        await websocket.send_json({"type": "ready"})

        # Process audio stream
        while True:
            # Receive audio data
            message = await websocket.receive()

            if "bytes" in message:
                # Binary audio data
                audio_data = message["bytes"]

                # Create audio chunk
                audio_chunk = AudioChunk(
                    data=audio_data,
                    timestamp=datetime.now(),
                    sample_rate=settings.sample_rate,
                    channels=settings.channels,
                    duration_ms=len(audio_data) / (settings.sample_rate * 2) * 1000
                )

                # Process
                conversation_turn = await controller.process_audio(
                    audio_chunk,
                    source_language=settings.source_language
                )

                # Send result
                result = {
                    "type": "transcription",
                    "speaker_id": conversation_turn.speaker.speaker_id,
                    "speaker_name": conversation_turn.speaker.name,
                    "speaker_language": conversation_turn.transcription.language,
                    "original_text": conversation_turn.transcription.text,
                    "translated_text": conversation_turn.translation.translated_text,
                    "source_language": conversation_turn.translation.source_language,
                    "target_language": conversation_turn.translation.target_language,
                    "suggestions": [
                        {
                            "text": s.text,
                            "language": s.language,
                            "confidence": s.confidence
                        }
                        for s in conversation_turn.suggestions
                    ],
                    "timestamp": conversation_turn.timestamp.isoformat()
                }

                await websocket.send_json(result)

            elif "text" in message:
                # Control messages
                data = json.loads(message["text"])

                if data.get("type") == "clear_history":
                    controller.clear_conversation_history()
                    await websocket.send_json({"type": "history_cleared"})

    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.send_json({"type": "error", "message": str(e)})
