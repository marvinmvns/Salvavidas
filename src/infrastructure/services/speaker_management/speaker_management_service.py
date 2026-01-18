"""
Speaker Management Service Implementation
Handles speaker enrollment, identification, and profile management.
"""

import uuid
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict

from ....core.interfaces.services import ISpeakerManagementService
from ....core.entities import AudioChunk
from ....core.entities.speaker_management import (
    SpeakerEnrollmentRequest,
    SpeakerEnrollmentSession,
    EnrolledSpeaker,
    SpeakerIdentificationResult,
    SpeakerUpdateRequest,
    VoiceProfileQuality,
    EnrollmentStatus,
)


class SpeakerManagementService(ISpeakerManagementService):
    """
    Speaker Management Service.
    Manages speaker enrollment, identification, and voice profiles.
    """

    def __init__(self, database_path: str = "speakers.db"):
        """
        Initialize speaker management service.

        Args:
            database_path: Path to SQLite database for persistence
        """
        self.database_path = database_path

        # In-memory storage
        self.enrolled_speakers: Dict[str, EnrolledSpeaker] = {}
        self.enrollment_sessions: Dict[str, SpeakerEnrollmentSession] = {}

        # Speaker embeddings cache (speaker_id -> embedding vector)
        self.speaker_embeddings: Dict[str, np.ndarray] = {}

        # Unknown speaker counter
        self.unknown_speaker_count = 0

        # Configuration
        self.min_samples_required = 3
        self.max_samples_allowed = 10
        self.identification_threshold = 0.7  # Confidence threshold for identification

    async def start_enrollment(
        self,
        request: SpeakerEnrollmentRequest
    ) -> SpeakerEnrollmentSession:
        """Start a new speaker enrollment session."""
        session_id = str(uuid.uuid4())

        session = SpeakerEnrollmentSession(
            session_id=session_id,
            speaker_name=request.name,
            status=EnrollmentStatus.PENDING,
            samples_required=self.min_samples_required,
            samples_collected=0,
            audio_samples=[],
        )

        self.enrollment_sessions[session_id] = session

        return session

    async def add_enrollment_sample(
        self,
        session_id: str,
        audio_chunk: AudioChunk
    ) -> SpeakerEnrollmentSession:
        """Add voice sample to enrollment session."""
        if session_id not in self.enrollment_sessions:
            raise ValueError(f"Enrollment session {session_id} not found")

        session = self.enrollment_sessions[session_id]

        if session.status == EnrollmentStatus.COMPLETED:
            raise ValueError("Enrollment session already completed")

        if session.status == EnrollmentStatus.FAILED:
            raise ValueError("Enrollment session has failed")

        if session.samples_collected >= self.max_samples_allowed:
            raise ValueError(f"Maximum {self.max_samples_allowed} samples already collected")

        # Update session status
        session.status = EnrollmentStatus.IN_PROGRESS

        # Add audio sample
        session.audio_samples.append(audio_chunk.data)
        session.samples_collected += 1
        session.updated_at = datetime.now()

        return session

    async def complete_enrollment(
        self,
        session_id: str
    ) -> EnrolledSpeaker:
        """Complete enrollment and create speaker profile."""
        if session_id not in self.enrollment_sessions:
            raise ValueError(f"Enrollment session {session_id} not found")

        session = self.enrollment_sessions[session_id]

        if session.samples_collected < self.min_samples_required:
            session.status = EnrollmentStatus.FAILED
            session.error_message = f"Insufficient samples: {session.samples_collected}/{self.min_samples_required}"
            raise ValueError(session.error_message)

        # Generate voice embedding from samples
        voice_embedding = self._generate_voice_embedding(session.audio_samples)

        # Create enrolled speaker
        speaker_id = str(uuid.uuid4())
        speaker = EnrolledSpeaker(
            speaker_id=speaker_id,
            name=session.speaker_name,
            email=None,
            language="en",  # Default language
            organization=None,
            notes=None,
            voice_embedding=voice_embedding.tobytes(),
            sample_count=session.samples_collected,
            enrollment_date=datetime.now(),
        )

        # Store speaker
        self.enrolled_speakers[speaker_id] = speaker
        self.speaker_embeddings[speaker_id] = voice_embedding

        # Update session status
        session.status = EnrollmentStatus.COMPLETED
        session.updated_at = datetime.now()

        # Clean up session after some time (keep for reference)
        # In production, would be cleaned by background task

        return speaker

    async def cancel_enrollment(
        self,
        session_id: str
    ) -> None:
        """Cancel enrollment session."""
        if session_id in self.enrollment_sessions:
            session = self.enrollment_sessions[session_id]
            session.status = EnrollmentStatus.FAILED
            session.error_message = "Cancelled by user"
            session.updated_at = datetime.now()

    async def identify_speaker(
        self,
        audio_chunk: AudioChunk
    ) -> SpeakerIdentificationResult:
        """Identify speaker from audio or detect new speaker."""
        # Generate embedding from audio
        query_embedding = self._generate_voice_embedding([audio_chunk.data])

        # If no enrolled speakers, it's a new speaker
        if not self.speaker_embeddings:
            self.unknown_speaker_count += 1
            return SpeakerIdentificationResult(
                identified=False,
                speaker=None,
                confidence=0.0,
                is_new_speaker=True,
                suggested_name=f"Speaker {self.unknown_speaker_count}"
            )

        # Compare with all enrolled speakers
        best_match_id = None
        best_similarity = 0.0

        for speaker_id, speaker_embedding in self.speaker_embeddings.items():
            similarity = self._calculate_similarity(query_embedding, speaker_embedding)

            if similarity > best_similarity:
                best_similarity = similarity
                best_match_id = speaker_id

        # Check if similarity exceeds threshold
        if best_similarity >= self.identification_threshold:
            speaker = self.enrolled_speakers[best_match_id]

            # Update speaker statistics
            speaker.last_seen = datetime.now()
            speaker.recognition_accuracy = (
                (speaker.recognition_accuracy * speaker.total_meetings + best_similarity) /
                (speaker.total_meetings + 1)
            )

            return SpeakerIdentificationResult(
                identified=True,
                speaker=speaker,
                confidence=best_similarity,
                is_new_speaker=False,
            )
        else:
            # Unknown speaker
            self.unknown_speaker_count += 1
            return SpeakerIdentificationResult(
                identified=False,
                speaker=None,
                confidence=best_similarity,
                is_new_speaker=True,
                suggested_name=f"Speaker {self.unknown_speaker_count}"
            )

    async def get_all_speakers(self) -> List[EnrolledSpeaker]:
        """Get all enrolled speakers."""
        return list(self.enrolled_speakers.values())

    async def get_speaker(
        self,
        speaker_id: str
    ) -> Optional[EnrolledSpeaker]:
        """Get specific enrolled speaker."""
        return self.enrolled_speakers.get(speaker_id)

    async def update_speaker(
        self,
        request: SpeakerUpdateRequest
    ) -> EnrolledSpeaker:
        """Update speaker information."""
        speaker = self.enrolled_speakers.get(request.speaker_id)

        if not speaker:
            raise ValueError(f"Speaker {request.speaker_id} not found")

        # Update fields if provided
        if request.name is not None:
            speaker.name = request.name
        if request.email is not None:
            speaker.email = request.email
        if request.language is not None:
            speaker.language = request.language
        if request.organization is not None:
            speaker.organization = request.organization
        if request.notes is not None:
            speaker.notes = request.notes

        speaker.updated_at = datetime.now()

        return speaker

    async def delete_speaker(
        self,
        speaker_id: str
    ) -> None:
        """Delete enrolled speaker."""
        if speaker_id in self.enrolled_speakers:
            del self.enrolled_speakers[speaker_id]

        if speaker_id in self.speaker_embeddings:
            del self.speaker_embeddings[speaker_id]

    async def assess_voice_quality(
        self,
        speaker_id: str
    ) -> VoiceProfileQuality:
        """Assess quality of speaker's voice profile."""
        speaker = self.enrolled_speakers.get(speaker_id)

        if not speaker:
            raise ValueError(f"Speaker {speaker_id} not found")

        # Simple quality assessment
        # In production, would analyze embedding consistency, SNR, etc.

        sample_count = speaker.sample_count

        # More samples = better quality (up to a point)
        sample_quality = min(sample_count / 5.0, 1.0)

        # Check recognition accuracy
        accuracy_quality = speaker.recognition_accuracy

        # Overall quality score
        quality_score = (sample_quality + accuracy_quality) / 2.0

        # Recommend retrain if quality is low or few samples
        recommended_retrain = quality_score < 0.7 or sample_count < 5

        return VoiceProfileQuality(
            speaker_id=speaker_id,
            sample_count=sample_count,
            average_snr=0.0,  # Would be calculated from audio
            embedding_consistency=accuracy_quality,
            recommended_retrain=recommended_retrain,
            quality_score=quality_score,
        )

    async def retrain_speaker(
        self,
        speaker_id: str,
        audio_samples: List[AudioChunk]
    ) -> EnrolledSpeaker:
        """Retrain speaker voice profile with new samples."""
        speaker = self.enrolled_speakers.get(speaker_id)

        if not speaker:
            raise ValueError(f"Speaker {speaker_id} not found")

        if len(audio_samples) < self.min_samples_required:
            raise ValueError(f"Need at least {self.min_samples_required} samples for retraining")

        # Generate new voice embedding
        audio_data = [chunk.data for chunk in audio_samples]
        new_embedding = self._generate_voice_embedding(audio_data)

        # Update speaker profile
        speaker.voice_embedding = new_embedding.tobytes()
        speaker.sample_count = len(audio_samples)
        speaker.updated_at = datetime.now()

        # Update cached embedding
        self.speaker_embeddings[speaker_id] = new_embedding

        return speaker

    async def update_speaker_stats(
        self,
        speaker_id: str,
        talk_time_seconds: float = 0.0,
        increment_meetings: bool = False,
        recognition_success: bool = True
    ) -> None:
        """
        Update speaker statistics during real-time usage.

        Args:
            speaker_id: Speaker ID to update
            talk_time_seconds: Add to total talk time
            increment_meetings: Increment total meetings counter
            recognition_success: Whether recognition was successful (for accuracy tracking)
        """
        speaker = self.enrolled_speakers.get(speaker_id)

        if not speaker:
            return  # Silently ignore if speaker not found

        # Update talk time
        if talk_time_seconds > 0:
            speaker.total_talk_time_seconds += int(talk_time_seconds)

        # Update meeting count
        if increment_meetings:
            speaker.total_meetings += 1

        # Update recognition accuracy (running average)
        if recognition_success:
            # Simple running average: new_avg = (old_avg * n + new_value) / (n + 1)
            total_recognitions = speaker.total_meetings * 10  # Rough estimate
            current_total = speaker.recognition_accuracy * total_recognitions
            speaker.recognition_accuracy = (current_total + 1.0) / (total_recognitions + 1)
        else:
            total_recognitions = speaker.total_meetings * 10
            current_total = speaker.recognition_accuracy * total_recognitions
            speaker.recognition_accuracy = (current_total + 0.0) / (total_recognitions + 1)

        # Update last seen
        speaker.last_seen = datetime.now()
        speaker.updated_at = datetime.now()

    # Helper methods

    def _generate_voice_embedding(self, audio_samples: List[bytes]) -> np.ndarray:
        """
        Generate voice embedding from audio samples.

        In production, this would use:
        - Pyannote.audio for speaker embeddings
        - SpeechBrain
        - WeSpeaker
        - Or cloud service (Azure Speaker Recognition, AWS Transcribe, etc.)

        For now, we generate a simple hash-based embedding for demonstration.
        """
        # Simplified embedding: hash-based features
        # In production, use proper speaker embedding models

        combined_audio = b''.join(audio_samples)

        # Generate 128-dimensional embedding
        embedding_size = 128
        embedding = np.zeros(embedding_size)

        # Simple hash-based features (just for demonstration)
        for i in range(embedding_size):
            # Use different parts of audio for different dimensions
            chunk_size = len(combined_audio) // embedding_size
            start = i * chunk_size
            end = start + chunk_size

            if end <= len(combined_audio):
                chunk = combined_audio[start:end]
                # Simple hash
                hash_val = hash(chunk) % 1000000
                embedding[i] = hash_val / 1000000.0

        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    def _calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Returns value between 0 and 1 (higher = more similar).
        """
        # Cosine similarity
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)

        # Convert to 0-1 range (cosine similarity is -1 to 1)
        similarity = (similarity + 1) / 2

        return float(similarity)
