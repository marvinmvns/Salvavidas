"""
Speaker Management API endpoints using FastAPI.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Optional
from pydantic import BaseModel

from ...core.interfaces.services import ISpeakerManagementService
from ...core.entities import AudioChunk
from datetime import datetime


# Request/Response models
class EnrollmentStartRequest(BaseModel):
    """Request to start speaker enrollment."""
    name: str
    email: Optional[str] = None
    language: str = "en"
    organization: Optional[str] = None
    notes: Optional[str] = None


class SpeakerUpdateRequestModel(BaseModel):
    """Request to update speaker."""
    name: Optional[str] = None
    email: Optional[str] = None
    language: Optional[str] = None
    organization: Optional[str] = None
    notes: Optional[str] = None


def create_speaker_router(speaker_service: ISpeakerManagementService) -> APIRouter:
    """
    Create FastAPI router for speaker management endpoints.

    Args:
        speaker_service: Speaker management service instance

    Returns:
        Configured APIRouter
    """
    router = APIRouter(prefix="/api/speakers", tags=["speakers"])

    @router.post("/enroll/start")
    async def start_enrollment(request: EnrollmentStartRequest):
        """Start a new speaker enrollment session."""
        try:
            from ...core.entities.speaker_management import SpeakerEnrollmentRequest

            enrollment_request = SpeakerEnrollmentRequest(
                name=request.name,
                email=request.email,
                language=request.language,
                organization=request.organization,
                notes=request.notes
            )

            session = await speaker_service.start_enrollment(enrollment_request)

            return {
                "session_id": session.session_id,
                "speaker_name": session.speaker_name,
                "status": session.status.value,
                "samples_required": session.samples_required,
                "samples_collected": session.samples_collected,
                "created_at": session.created_at.isoformat(),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/enroll/{session_id}/sample")
    async def add_enrollment_sample(
        session_id: str,
        audio: UploadFile = File(...)
    ):
        """Add voice sample to enrollment session."""
        try:
            # Read audio data
            audio_data = await audio.read()

            # Create audio chunk
            audio_chunk = AudioChunk(
                data=audio_data,
                timestamp=datetime.now(),
                sample_rate=16000,  # Assume 16kHz
                channels=1,  # Mono
                duration_ms=len(audio_data) / (16000 * 2) * 1000  # Rough estimate
            )

            session = await speaker_service.add_enrollment_sample(session_id, audio_chunk)

            return {
                "session_id": session.session_id,
                "status": session.status.value,
                "samples_collected": session.samples_collected,
                "samples_required": session.samples_required,
                "complete": session.samples_collected >= session.samples_required,
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/enroll/{session_id}/complete")
    async def complete_enrollment(session_id: str):
        """Complete enrollment and create speaker profile."""
        try:
            speaker = await speaker_service.complete_enrollment(session_id)

            return {
                "speaker_id": speaker.speaker_id,
                "name": speaker.name,
                "email": speaker.email,
                "language": speaker.language,
                "sample_count": speaker.sample_count,
                "enrollment_date": speaker.enrollment_date.isoformat(),
                "message": "Speaker enrolled successfully"
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.delete("/enroll/{session_id}")
    async def cancel_enrollment(session_id: str):
        """Cancel enrollment session."""
        try:
            await speaker_service.cancel_enrollment(session_id)
            return {"message": "Enrollment cancelled"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("")
    async def get_all_speakers():
        """Get all enrolled speakers."""
        try:
            speakers = await speaker_service.get_all_speakers()

            return {
                "speakers": [
                    {
                        "speaker_id": s.speaker_id,
                        "name": s.name,
                        "email": s.email,
                        "language": s.language,
                        "organization": s.organization,
                        "sample_count": s.sample_count,
                        "enrollment_date": s.enrollment_date.isoformat(),
                        "last_seen": s.last_seen.isoformat() if s.last_seen else None,
                        "total_meetings": s.total_meetings,
                        "total_talk_time_seconds": s.total_talk_time_seconds,
                        "recognition_accuracy": s.recognition_accuracy,
                    }
                    for s in speakers
                ],
                "total": len(speakers)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/{speaker_id}")
    async def get_speaker(speaker_id: str):
        """Get specific enrolled speaker."""
        try:
            speaker = await speaker_service.get_speaker(speaker_id)

            if not speaker:
                raise HTTPException(status_code=404, detail="Speaker not found")

            return {
                "speaker_id": speaker.speaker_id,
                "name": speaker.name,
                "email": speaker.email,
                "language": speaker.language,
                "organization": speaker.organization,
                "notes": speaker.notes,
                "sample_count": speaker.sample_count,
                "enrollment_date": speaker.enrollment_date.isoformat(),
                "last_seen": speaker.last_seen.isoformat() if speaker.last_seen else None,
                "total_meetings": speaker.total_meetings,
                "total_talk_time_seconds": speaker.total_talk_time_seconds,
                "recognition_accuracy": speaker.recognition_accuracy,
                "created_at": speaker.created_at.isoformat(),
                "updated_at": speaker.updated_at.isoformat(),
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.patch("/{speaker_id}")
    async def update_speaker(speaker_id: str, request: SpeakerUpdateRequestModel):
        """Update speaker information."""
        try:
            from ...core.entities.speaker_management import SpeakerUpdateRequest

            update_request = SpeakerUpdateRequest(
                speaker_id=speaker_id,
                name=request.name,
                email=request.email,
                language=request.language,
                organization=request.organization,
                notes=request.notes
            )

            speaker = await speaker_service.update_speaker(update_request)

            return {
                "speaker_id": speaker.speaker_id,
                "name": speaker.name,
                "email": speaker.email,
                "language": speaker.language,
                "organization": speaker.organization,
                "notes": speaker.notes,
                "updated_at": speaker.updated_at.isoformat(),
                "message": "Speaker updated successfully"
            }
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.delete("/{speaker_id}")
    async def delete_speaker(speaker_id: str):
        """Delete enrolled speaker."""
        try:
            await speaker_service.delete_speaker(speaker_id)
            return {"message": "Speaker deleted successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/{speaker_id}/quality")
    async def assess_voice_quality(speaker_id: str):
        """Assess quality of speaker's voice profile."""
        try:
            quality = await speaker_service.assess_voice_quality(speaker_id)

            return {
                "speaker_id": quality.speaker_id,
                "sample_count": quality.sample_count,
                "average_snr": quality.average_snr,
                "embedding_consistency": quality.embedding_consistency,
                "recommended_retrain": quality.recommended_retrain,
                "quality_score": quality.quality_score,
                "quality_level": (
                    "excellent" if quality.quality_score >= 0.9 else
                    "good" if quality.quality_score >= 0.7 else
                    "fair" if quality.quality_score >= 0.5 else
                    "poor"
                )
            }
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/{speaker_id}/retrain")
    async def retrain_speaker(
        speaker_id: str,
        audio_files: list[UploadFile] = File(...)
    ):
        """Retrain speaker voice profile with new samples."""
        try:
            # Read all audio files
            audio_chunks = []
            for audio_file in audio_files:
                audio_data = await audio_file.read()

                audio_chunk = AudioChunk(
                    data=audio_data,
                    timestamp=datetime.now(),
                    sample_rate=16000,
                    channels=1,
                    duration_ms=len(audio_data) / (16000 * 2) * 1000
                )

                audio_chunks.append(audio_chunk)

            speaker = await speaker_service.retrain_speaker(speaker_id, audio_chunks)

            return {
                "speaker_id": speaker.speaker_id,
                "name": speaker.name,
                "sample_count": speaker.sample_count,
                "updated_at": speaker.updated_at.isoformat(),
                "message": "Speaker retrained successfully"
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/identify")
    async def identify_speaker(audio: UploadFile = File(...)):
        """Identify speaker from audio sample."""
        try:
            # Read audio data
            audio_data = await audio.read()

            # Create audio chunk
            audio_chunk = AudioChunk(
                data=audio_data,
                timestamp=datetime.now(),
                sample_rate=16000,
                channels=1,
                duration_ms=len(audio_data) / (16000 * 2) * 1000
            )

            result = await speaker_service.identify_speaker(audio_chunk)

            return {
                "identified": result.identified,
                "is_new_speaker": result.is_new_speaker,
                "confidence": result.confidence,
                "speaker": {
                    "speaker_id": result.speaker.speaker_id,
                    "name": result.speaker.name,
                    "language": result.speaker.language,
                } if result.speaker else None,
                "suggested_name": result.suggested_name,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "speaker_management"}

    return router
