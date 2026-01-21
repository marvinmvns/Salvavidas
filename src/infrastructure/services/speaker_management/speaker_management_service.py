"""
Speaker Management Service Implementation
Handles speaker enrollment, identification, and profile management.
Uses Pyannote.audio for production-ready speaker embeddings.
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
from .speechbrain_service import SpeechBrainEmbeddingService
from .pyannote_embedding_service import create_embedding_service # Keep for fallback or API mode if needed, but we prefer SpeechBrain now


class SpeakerManagementService(ISpeakerManagementService):
    """
    Speaker Management Service using Pyannote.audio embeddings.

    Features:
    - Production-ready speaker embeddings via Pyannote.audio
    - Multi-sample enrollment for robust voice profiles
    - Real-time speaker identification with confidence scoring
    - Automatic fallback to hash-based embeddings if Pyannote unavailable
    """

    def __init__(
        self,
        database_path: str = "speakers.db",
        use_pyannote: bool = True,
        pyannote_model: str = "pyannote/embedding",
        huggingface_token: Optional[str] = None
    ):
        """
        Initialize speaker management service.

        Args:
            database_path: Path to SQLite database for persistence
            use_pyannote: Whether to use Pyannote.audio (recommended for production)
            pyannote_model: Pyannote model name (default: pyannote/embedding)
            huggingface_token: Hugging Face token for gated models
        """
        self.database_path = database_path

        self.database_path = database_path

        # Initialize embedding service (SpeechBrain for local)
        try:
            self.embedding_service = SpeechBrainEmbeddingService()
        except Exception as e:
            print(f"[SpeakerMgmt] Failed to load SpeechBrain: {e}")
            from .pyannote_embedding_service import FallbackEmbeddingService
            self.embedding_service = FallbackEmbeddingService()

        print(f"[SpeakerMgmt] Embedding service initialized: {type(self.embedding_service).__name__}")
        print(f"[SpeakerMgmt] Embedding dimension: {self.embedding_service.get_embedding_dimension()}")

        # In-memory storage
        self.enrolled_speakers: Dict[str, EnrolledSpeaker] = {}
        self.enrollment_sessions: Dict[str, SpeakerEnrollmentSession] = {}

        # Speaker embeddings cache (speaker_id -> embedding vector)
        self.speaker_embeddings: Dict[str, np.ndarray] = {}

        # Unknown speaker counter
        self.unknown_speaker_count = 0
        self.temporary_speakers: Dict[str, dict] = {}

        # Configuration
        self.min_samples_required = 3
        self.max_samples_allowed = 10
        self.identification_threshold = 0.25  # For enrolled speakers
        self.temp_speaker_threshold = 0.02  # Very low - embeddings seem to have low similarity

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
            temp_id = f"Speaker {self.unknown_speaker_count}"
            
            # Cache for potential enrollment
            if not hasattr(self, 'temporary_speakers'):
                 self.temporary_speakers = {}
                 
            self.temporary_speakers[temp_id] = {
                "embedding": query_embedding,
                "timestamp": datetime.now()
            }

            return SpeakerIdentificationResult(
                identified=False,
                speaker=None,
                confidence=0.0,
                is_new_speaker=True,
                suggested_name=temp_id
            )

        # Compare with all enrolled speakers
        best_match_id = None
        best_similarity = 0.0

        for speaker_id, speaker_embedding in self.speaker_embeddings.items():
            similarity = self._calculate_similarity(query_embedding, speaker_embedding)
            print(f"[SpeakerMgmt] Comparing with {speaker_id}: {similarity:.4f}")

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
            # Check against temporary speakers first
            best_temp_match = None
            best_temp_similarity = 0.0

            for temp_id, temp_data in self.temporary_speakers.items():
                temp_similarity = self._calculate_similarity(query_embedding, temp_data["embedding"])
                print(f"[SpeakerMgmt] Comparing with temp {temp_id}: {temp_similarity:.4f}")
                if temp_similarity > best_temp_similarity:
                    best_temp_similarity = temp_similarity
                    best_temp_match = temp_id

            # If matches existing temporary speaker, reuse it
            if best_temp_match and best_temp_similarity >= self.temp_speaker_threshold:
                # Update the embedding with running average
                temp_data = self.temporary_speakers[best_temp_match]
                temp_data["embedding"] = (temp_data["embedding"] + query_embedding) / 2
                temp_data["timestamp"] = datetime.now()

                # Create temporary speaker object to pass metadata (like language)
                temp_speaker_obj = EnrolledSpeaker(
                    speaker_id=best_temp_match,
                    name=best_temp_match,
                    email=None,
                    language=temp_data.get("language"), # Pass saved language
                    organization=None,
                    notes=None,
                    voice_embedding=None,
                    sample_count=1,
                    enrollment_date=temp_data["timestamp"]
                )

                return SpeakerIdentificationResult(
                    identified=False,
                    speaker=temp_speaker_obj, # Pass object so UseCase can see language
                    confidence=best_temp_similarity,
                    is_new_speaker=False,  # Not new, matched temp speaker
                    suggested_name=best_temp_match
                )

            # Truly unknown speaker - create new temporary speaker
            self.unknown_speaker_count += 1
            temp_id = f"Speaker {self.unknown_speaker_count}"

            # Cache for potential enrollment
            self.temporary_speakers[temp_id] = {
                "embedding": query_embedding,
                "timestamp": datetime.now()
            }

            return SpeakerIdentificationResult(
                identified=False,
                speaker=None,
                confidence=best_similarity,
                is_new_speaker=True,
                suggested_name=temp_id
            )

    async def get_all_speakers(self) -> List[EnrolledSpeaker]:
        """Get all enrolled speakers."""
        return list(self.enrolled_speakers.values())

    async def update_speaker_language(self, speaker_id: str, language: str) -> bool:
        """Update language preference for a speaker (enrolled or temporary)."""
        # Check enrolled speakers
        if speaker_id in self.enrolled_speakers:
            self.enrolled_speakers[speaker_id].language = language
            # TODO: Persist to DB
            return True
        
        # Check temporary speakers (store/update in temp metadata)
        if speaker_id in self.temporary_speakers:
            self.temporary_speakers[speaker_id]["language"] = language
            return True
        
        # Check if speaker_id matches a temporary speaker suggested_name
        for temp_id, data in self.temporary_speakers.items():
            if temp_id == speaker_id:
                data["language"] = language
                return True
                
        return False

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

    async def update_speaker_name(
        self,
        speaker_id: str,
        name: str,
        email: Optional[str] = None
    ) -> bool:
        """
        Update the name and email of an enrolled speaker.
        If speaker_id corresponds to a cached temporary speaker, enroll them.

        Args:
            speaker_id: Unique speaker identifier
            name: New name for the speaker
            email: Optional email address

        Returns:
            True if successful, False if speaker not found
        """
        # Check if it's an enrolled speaker
        if speaker_id in self.enrolled_speakers:
            speaker = self.enrolled_speakers[speaker_id]
            speaker.name = name
            if email:
                speaker.email = email
            speaker.updated_at = datetime.now()
            print(f"[SpeakerMgmt] Updated speaker {speaker_id}: name='{name}'")
            return True

        # Check if it's a temporary unknown speaker
        if hasattr(self, 'temporary_speakers') and speaker_id in self.temporary_speakers:
            print(f"[SpeakerMgmt] Promoting temporary speaker {speaker_id} to enrolled speaker '{name}'")
            try:
                temp_data = self.temporary_speakers[speaker_id]
                embedding = temp_data["embedding"]
                
                # Create new enrolled speaker
                new_id = str(uuid.uuid4())
                print(f"[SpeakerMgmt] Generated new UUID: {new_id} for {name}")
                
                speaker = EnrolledSpeaker(
                    speaker_id=new_id,
                    name=name,
                    email=email,
                    language="en",
                    organization=None,
                    notes="Ad-hoc enrollment from live session",
                    voice_embedding=embedding.tobytes(),
                    sample_count=1,
                    enrollment_date=datetime.now(),
                )
                
                # Save using the ORIGINAL ID (Speaker N) as key so the frontend stays consistent
                # But the internal object has the new UUID.
                # This ensures we can look it up by "Speaker N" until refresh.
                self.enrolled_speakers[speaker_id] = speaker
                self.speaker_embeddings[speaker_id] = embedding
                
                # Also save with the NEW UUID for future persistence correctness
                self.enrolled_speakers[new_id] = speaker
                self.speaker_embeddings[new_id] = embedding
                
                del self.temporary_speakers[speaker_id]
                print(f"[SpeakerMgmt] Successfully promoted {speaker_id}")
                return True
            except Exception as e:
                print(f"[SpeakerMgmt] Error promoting speaker: {e}")
                import traceback
                traceback.print_exc()
                raise e

        # If we get here, speaker was not found in temporary list
        print(f"[SpeakerMgmt] Update failed: Speaker ID '{speaker_id}' not found. Available Temp: {list(self.temporary_speakers.keys()) if hasattr(self, 'temporary_speakers') else 'None'}")
        return False

    # Helper methods

    def _generate_voice_embedding(self, audio_samples: List[bytes]) -> np.ndarray:
        """
        Generate voice embedding from audio samples using Pyannote.audio.

        Args:
            audio_samples: List of audio byte arrays (PCM 16-bit)

        Returns:
            Speaker embedding vector (512-dimensional for Pyannote, 128 for fallback)
        """
        try:
            embedding = self.embedding_service.generate_embedding(
                audio_samples=audio_samples,
                sample_rate=16000
            )
            return embedding

        except Exception as e:
            print(f"[SpeakerMgmt] Error generating embedding: {e}")
            # Return zero embedding on error
            dim = self.embedding_service.get_embedding_dimension()
            return np.zeros(dim)

    def _calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First speaker embedding
            embedding2: Second speaker embedding

        Returns:
            Similarity score between 0 and 1 (higher = more similar)
        """
        try:
            similarity = self.embedding_service.calculate_similarity(
                embedding1=embedding1,
                embedding2=embedding2
            )
            return similarity

        except Exception as e:
            print(f"[SpeakerMgmt] Error calculating similarity: {e}")
            return 0.0
