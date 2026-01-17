"""
Speaker Management entities for voice enrollment and identification.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum


class EnrollmentStatus(str, Enum):
    """Status of speaker enrollment process."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SpeakerEnrollmentRequest:
    """Request to enroll a new speaker."""
    name: str
    email: Optional[str] = None
    language: str = "en"
    organization: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class SpeakerEnrollmentSession:
    """Active speaker enrollment session."""
    session_id: str
    speaker_name: str
    status: EnrollmentStatus
    samples_required: int = 3  # Minimum 3 voice samples
    samples_collected: int = 0
    audio_samples: List[bytes] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None


@dataclass
class EnrolledSpeaker:
    """Enrolled speaker with voice profile."""
    speaker_id: str
    name: str
    email: Optional[str]
    language: str
    organization: Optional[str]
    notes: Optional[str]

    # Voice profile data
    voice_embedding: Optional[bytes]  # Serialized embedding vector
    sample_count: int
    enrollment_date: datetime

    # Metadata
    last_seen: Optional[datetime] = None
    total_meetings: int = 0
    total_talk_time_seconds: int = 0

    # Quality metrics
    recognition_accuracy: float = 0.0  # Average confidence when identified

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class SpeakerIdentificationResult:
    """Result of speaker identification."""
    identified: bool
    speaker: Optional[EnrolledSpeaker]
    confidence: float
    is_new_speaker: bool
    suggested_name: Optional[str] = None  # "Speaker 1", "Speaker 2", etc.


@dataclass
class SpeakerUpdateRequest:
    """Request to update speaker information."""
    speaker_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    language: Optional[str] = None
    organization: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class VoiceProfileQuality:
    """Quality assessment of voice profile."""
    speaker_id: str
    sample_count: int
    average_snr: float  # Signal-to-noise ratio
    embedding_consistency: float  # 0-1 score
    recommended_retrain: bool
    quality_score: float  # Overall 0-1 score
