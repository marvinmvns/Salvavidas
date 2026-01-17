"""Core domain entities."""
from .audio import AudioChunk, Speaker
from .conversation import (
    TranscriptionSegment,
    Translation,
    SuggestionResponse,
    ConversationTurn
)

__all__ = [
    "AudioChunk",
    "Speaker",
    "TranscriptionSegment",
    "Translation",
    "SuggestionResponse",
    "ConversationTurn",
]
