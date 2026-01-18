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
import aiofiles

from ...infrastructure.database import Database
from ...infrastructure.service_factory import ServiceFactory
from ..controllers import VoiceTranslationController, ConfigController
from ...core.use_cases import ProcessVoiceTranslationUseCase
from ...core.entities import AudioChunk
from config.settings import get_settings
from ...infrastructure.services.analytics import AnalyticsService
from .analytics_api import create_analytics_router
from ...infrastructure.services.speaker_management import SpeakerManagementService
from .speaker_api import create_speaker_router


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
speaker_service: SpeakerManagementService = None


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
    global database, config_controller, analytics_service, speaker_service

    # Initialize database
    database = Database()
    await database.init_db()

    # Initialize config controller
    config_controller = ConfigController(database)

    # Initialize analytics service
    analytics_service = AnalyticsService()

    # Initialize speaker management service
    speaker_service = SpeakerManagementService()

    # Mount analytics router
    analytics_router = create_analytics_router(analytics_service)
    app.include_router(analytics_router)

    # Mount speaker management router
    speaker_router = create_speaker_router(speaker_service)
    app.include_router(speaker_router)


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    if database:
        await database.close()


@app.get("/", response_class=HTMLResponse)
async def get_index():
    """Serve frontend."""
    async with aiofiles.open("frontend/index.html", "r") as f:
        return await f.read()


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {
            "database": "ready" if database else "not_initialized",
            "analytics": "ready" if analytics_service else "not_initialized",
            "speaker_management": "ready" if speaker_service else "not_initialized"
        }
    }


@app.get("/analytics", response_class=HTMLResponse)
async def get_analytics():
    """Serve analytics dashboard."""
    async with aiofiles.open("frontend/analytics.html", "r") as f:
        return await f.read()


@app.get("/speakers", response_class=HTMLResponse)
async def get_speakers():
    """Serve speaker management page."""
    async with aiofiles.open("frontend/speakers.html", "r") as f:
        return await f.read()


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

    meeting_id = None
    session_start_time = datetime.now()

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

        # Start analytics meeting session
        meeting_id = await analytics_service.record_meeting_start()

        # Send ready signal
        await websocket.send_json({"type": "ready", "meeting_id": meeting_id})

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

                # Identify speaker using speaker management service
                speaker_result = await speaker_service.identify_speaker(audio_chunk)

                # Process translation
                conversation_turn = await controller.process_audio(
                    audio_chunk,
                    source_language=settings.source_language
                )

                # Use identified speaker if available, otherwise use fallback
                if speaker_result.identified and speaker_result.speaker:
                    identified_speaker = speaker_result.speaker
                    speaker_confidence = speaker_result.confidence

                    # Update speaker stats
                    await speaker_service.update_speaker_stats(
                        identified_speaker.speaker_id,
                        talk_time_seconds=audio_chunk.duration_ms / 1000
                    )
                else:
                    # Unknown speaker
                    identified_speaker = None
                    speaker_confidence = 0.0

                # Record analytics
                await analytics_service.record_transcription(
                    meeting_id=meeting_id,
                    speaker_id=identified_speaker.speaker_id if identified_speaker else "unknown",
                    speaker_name=identified_speaker.name if identified_speaker else speaker_result.suggested_name,
                    text=conversation_turn.transcription.text,
                    language=conversation_turn.transcription.language,
                    duration_seconds=audio_chunk.duration_ms / 1000
                )

                # Send result with speaker identification
                result = {
                    "type": "transcription",
                    "speaker_id": identified_speaker.speaker_id if identified_speaker else "unknown",
                    "speaker_name": identified_speaker.name if identified_speaker else speaker_result.suggested_name,
                    "speaker_email": identified_speaker.email if identified_speaker else None,
                    "speaker_language": conversation_turn.transcription.language,
                    "speaker_confidence": speaker_confidence,
                    "is_enrolled_speaker": speaker_result.identified,
                    "is_new_speaker": speaker_result.is_new_speaker,
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
        print(f"[WebSocket] Client disconnected - session duration: {(datetime.now() - session_start_time).total_seconds():.1f}s")
        # End analytics meeting
        if meeting_id:
            await analytics_service.record_meeting_end(meeting_id)
    except Exception as e:
        print(f"[WebSocket] Error: {e}")
        import traceback
        traceback.print_exc()
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass
        # End analytics meeting on error
        if meeting_id:
            await analytics_service.record_meeting_end(meeting_id)
