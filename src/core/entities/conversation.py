"""Conversation domain entities."""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from .audio import Speaker


@dataclass
class TranscriptionSegment:
    """Represents a transcribed segment of speech."""
    text: str
    speaker: Speaker
    language: str
    timestamp: datetime
    confidence: float
    start_time: float
    end_time: float

    @property
    def duration(self) -> float:
        """Get duration in seconds."""
        return self.end_time - self.start_time


@dataclass
class Translation:
    """Represents a translation of text."""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    timestamp: datetime
    confidence: float = 1.0
    service: str = "unknown"


@dataclass
class SuggestionResponse:
    """Represents a suggested response."""
    text: str
    language: str
    confidence: float
    context: str
    alternatives: List[str] = field(default_factory=list)


@dataclass
class ConversationTurn:
    """Represents a complete conversation turn."""
    transcription: TranscriptionSegment
    translation: Translation
    suggestions: List[SuggestionResponse] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def speaker(self) -> Speaker:
        """Get the speaker."""
        return self.transcription.speaker
