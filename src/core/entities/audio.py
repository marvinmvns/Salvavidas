"""Audio domain entities."""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class AudioChunk:
    """Represents a chunk of audio data."""
    data: bytes
    timestamp: datetime
    sample_rate: int
    channels: int
    duration_ms: float

    @property
    def size_bytes(self) -> int:
        """Get size in bytes."""
        return len(self.data)


@dataclass
class Speaker:
    """Represents a speaker in the conversation."""
    speaker_id: str
    name: Optional[str] = None
    language: Optional[str] = None
    confidence: float = 0.0
    embedding: Optional[bytes] = None

    def __hash__(self) -> int:
        """Hash based on speaker_id."""
        return hash(self.speaker_id)

    def __eq__(self, other) -> bool:
        """Equality based on speaker_id."""
        if not isinstance(other, Speaker):
            return False
        return self.speaker_id == other.speaker_id
