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


@app.get("/{filename}.js")
async def get_js_file(filename: str):
    """Serve JS files from root."""
    # Security check: only allow alphanumeric filenames and hyphens/underscores
    if not filename.replace("_", "").replace("-", "").isalnum():
        raise HTTPException(status_code=404, detail="File not found")
        
    js_path = f"frontend/{filename}.js"
    try:
        async with aiofiles.open(js_path, "r") as f:
            content = await f.read()
            return HTMLResponse(content, media_type="application/javascript")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")


@app.get("/{filename}.css")
async def get_css_file(filename: str):
    """Serve CSS files from root."""
    # Security check: only allow alphanumeric filenames
    if not filename.replace("_", "").replace("-", "").isalnum():
        raise HTTPException(status_code=404, detail="File not found")
        
    css_path = f"frontend/{filename}.css"
    try:
        async with aiofiles.open(css_path, "r") as f:
            content = await f.read()
            return HTMLResponse(content, media_type="text/css")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")



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


class NameSpeakerRequest(BaseModel):
    """Request to name a speaker."""
    speaker_id: str
    name: str
    email: Optional[str] = None
    language: Optional[str] = None


@app.post("/api/speakers/name")
async def name_speaker(request: NameSpeakerRequest):
    """Associate a name with a speaker ID."""
    try:
        # Update speaker name in speaker management service
        success = await speaker_service.update_speaker_name(
            speaker_id=request.speaker_id,
            name=request.name,
            email=request.email
        )
        
        # Also update language if provided
        if success and request.language:
            await speaker_service.update_speaker_language(
                speaker_id=request.speaker_id,
                language=request.language
            )

        if success:
            return JSONResponse({
                "success": True,
                "message": f"Speaker '{request.name}' nomeado com sucesso",
                "speaker_id": request.speaker_id,
                "name": request.name
            })
        else:
            raise HTTPException(status_code=404, detail="Speaker não encontrado")

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


class EnrollSpeakerRequest(BaseModel):
    """Request to enroll a new speaker."""
    name: str
    email: Optional[str] = None
    language: Optional[str] = None


@app.post("/api/speakers/enroll")
async def enroll_speaker(request: EnrollSpeakerRequest):
    """Start enrollment session for a new speaker."""
    try:
        # Start enrollment session
        session_id = await speaker_service.start_enrollment_session(
            name=request.name,
            email=request.email,
            language=request.language
        )

        return JSONResponse({
            "success": True,
            "message": f"Sessão de enrollment iniciada para '{request.name}'",
            "session_id": session_id,
            "name": request.name,
            "samples_required": 3
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/diagnostics")
async def run_diagnostics():
    """Run self-test on local services."""
    results = {
        "stt": {"status": "pending", "message": ""},
        "translation": {"status": "pending", "message": ""},
        "speaker_id": {"status": "pending", "message": ""},
        "llm": {"status": "pending", "message": ""}
    }
    
    # 1. Test STT (Whisper)
    try:
        from ...infrastructure.services.stt.whisper_service import WhisperSTTService
        from ...core.entities import AudioChunk
        import numpy as np
        
        # We instantiate a temporary service or use the global factory logic?
        # Creating a new instance might be heavy (loading model again).
        # Ideally we use the existing factory if possible, but web_api doesn't expose it globally easily.
        # However, the models should be cached.
        
        # Let's try to instantiate lightly or check file existence first
        import os
        model_path = "/app/data/models/whisper-large-v3"
        if os.path.exists(model_path):
             results["stt"] = {"status": "ok", "message": "Model files found"}
        else:
             results["stt"] = {"status": "warning", "message": "Model files missing, will try to download on use"}

    except Exception as e:
         results["stt"] = {"status": "error", "message": str(e)}

    # 2. Test Translation (M2M100)
    try:
        import os
        model_path = "/app/data/models/translation/m2m100_418M/pytorch_model.bin"
        if os.path.exists(model_path):
             # Verify size > 1GB
             if os.path.getsize(model_path) > 1024*1024*1000:
                 results["translation"] = {"status": "ok", "message": "Model verified"}
             else:
                 results["translation"] = {"status": "error", "message": "Model corrupted (too small)"}
        else:
             results["translation"] = {"status": "error", "message": "Model missing"}
    except Exception as e:
         results["translation"] = {"status": "error", "message": str(e)}

    # 3. Test Speaker ID (SpeechBrain)
    try:
        import os
        model_path = "/app/data/models/speechbrain/embedding_model.ckpt"
        if os.path.exists(model_path):
             results["speaker_id"] = {"status": "ok", "message": "SpeechBrain model found"}
        else:
             from ...infrastructure.services.speaker_management.pyannote_embedding_service import PYANNOTE_AVAILABLE
             if PYANNOTE_AVAILABLE: 
                 results["speaker_id"] = {"status": "warning", "message": "SpeechBrain missing, trying Pyannote"}
             else:
                 results["speaker_id"] = {"status": "error", "message": "No Speaker ID models found"}
    except Exception as e:
         results["speaker_id"] = {"status": "error", "message": str(e)}

    return JSONResponse(results)
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
        import uuid
        meeting_id = str(uuid.uuid4())
        await analytics_service.record_meeting_start(
            meeting_id=meeting_id,
            meeting_type="adhoc",
            platform="web",
            processing_mode=settings.processing_mode,
        )

        # Send ready signal
        await websocket.send_json({"type": "ready", "meeting_id": meeting_id})

        # Audio buffer for accumulating chunks (process larger chunks = less overhead)
        audio_buffer = bytearray()
        
        # SMART BUFFERING CONFIG
        MIN_BUFFER_SIZE = 16000     # ~0.5s minimum to process
        MAX_BUFFER_SIZE = 240000    # ~7.5s max (force process if too long)
        SILENCE_THRESHOLD = 500     # RMS amplitude threshold for silence (adjust if needed)
        PAUSE_CHUNKS_REQUIRED = 2   # Number of silent chunks required to trigger processing
        
        silence_counter = 0

        # Process audio stream
        while True:
            # Receive audio data
            message = await websocket.receive()

            if "bytes" in message:
                # Binary audio data - add to buffer
                raw_bytes = message["bytes"]
                audio_buffer.extend(raw_bytes)
                
                # --- ENERGY BASED VAD (Voice Activity Detection) ---
                # Check current chunk energy to detect silence
                import numpy as np
                chunk_array = np.frombuffer(raw_bytes, dtype=np.int16)
                if len(chunk_array) > 0:
                    rms = np.sqrt(np.mean(chunk_array.astype(float)**2))
                else:
                    rms = 0
                
                is_silence = rms < SILENCE_THRESHOLD
                
                if is_silence:
                    silence_counter += 1
                else:
                    silence_counter = 0 # Reset on speech
                
                # DECISION LOGIC: Process if:
                # 1. Buffer is full (MAX_SIZE) -> Force process
                # 2. Minimum size reached AND Silence detected (PAUSE_CHUNKS_REQUIRED) -> Natural pause
                
                should_process = False
                buffer_len = len(audio_buffer)
                
                if buffer_len >= MAX_BUFFER_SIZE:
                    should_process = True
                    # print(f"[VAD] Max buffer reached ({buffer_len})")
                elif buffer_len >= MIN_BUFFER_SIZE and silence_counter >= PAUSE_CHUNKS_REQUIRED:
                    should_process = True
                    # print(f"[VAD] Silence detected (RMS: {rms:.1f}), processing sentence ({buffer_len} bytes)")
                
                if not should_process:
                    continue  # Wait for more audio/pause
                
                # Take data from buffer
                # Reset silence counter after processing
                silence_counter = 0
                
                process_size = len(audio_buffer) # Process everything collected
                audio_data = bytes(audio_buffer[:process_size])
                audio_buffer = bytearray()  # Clear buffer
                
                # Create audio chunk (rest of the code...)
                audio_chunk = AudioChunk(
                    data=audio_data,
                    timestamp=datetime.now(),
                    sample_rate=settings.sample_rate,
                    channels=settings.channels,
                    duration_ms=len(audio_data) / (settings.sample_rate * 2) * 1000
                )

                # Track latencies for performance monitoring
                import time
                start_time = time.time()

                # Identify speaker (if enabled in settings)
                speaker_result = None
                speaker_latency_ms = 0

                if settings.enable_speaker_id:
                     # Throttling: only identify every 4th chunk to save CPU
                    if not hasattr(websocket, "chunk_count"):
                        websocket.chunk_count = 0
                    websocket.chunk_count += 1

                    if websocket.chunk_count % 4 == 0:
                        try:
                            speaker_start = time.time()
                            speaker_result = await speaker_service.identify_speaker(audio_chunk)
                            speaker_latency_ms = int((time.time() - speaker_start) * 1000)
                        except Exception as e:
                            print(f"[WebAPI] Speaker ID error: {e}")

                # Fallback if disabled or throttled
                if not speaker_result:
                    from ...core.entities.speaker_management import SpeakerIdentificationResult
                    speaker_result = SpeakerIdentificationResult(
                        identified=False, speaker=None, confidence=0.0, 
                        is_new_speaker=False, suggested_name="Speaker 1"
                    )


                # Process translation
                stt_start = time.time()
                # Sanitize source language
                source_lang = settings.source_language
                if source_lang in ["auto", ""]:
                    source_lang = None

                conversation_turn = await controller.process_audio(
                    audio_chunk,
                    source_language=source_lang
                )
                stt_latency_ms = int((time.time() - stt_start) * 1000)

                # Translation latency (approximate from transcription data)
                translation_latency_ms = int(stt_latency_ms * 0.3)  # Translation is ~30% of STT time

                total_latency_ms = int((time.time() - start_time) * 1000)

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

                    # Only notify frontend when we actually detected a NEW speaker
                    # (not on dummy results from throttled chunks)
                    if speaker_result.is_new_speaker and speaker_result.suggested_name:
                        await websocket.send_json({
                            "type": "new_speaker_detected",
                            "speaker_id": speaker_result.suggested_name,
                            "suggested_name": speaker_result.suggested_name,
                            "confidence": speaker_confidence,
                            "message": "Novo falante detectado. Por favor, identifique."
                        })

                # Record analytics
                await analytics_service.record_transcription(
                    meeting_id=meeting_id,
                    transcription=conversation_turn.transcription,
                    speaker=identified_speaker
                )

                # Only send results if there's actual transcribed text
                if conversation_turn.transcription.text and conversation_turn.transcription.text.strip():
                    # Send result with speaker identification and performance metrics
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
                        "timestamp": conversation_turn.timestamp.isoformat(),
                        "performance": {
                            "stt_latency_ms": stt_latency_ms,
                            "speaker_latency_ms": speaker_latency_ms,
                            "translation_latency_ms": translation_latency_ms,
                            "total_latency_ms": total_latency_ms
                        }
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

