"""Core domain entities."""
from .audio import AudioChunk, Speaker
from .conversation import (
    TranscriptionSegment,
    Translation,
    SuggestionResponse,
    ConversationTurn
)
from .meeting import (
    SentimentAnalysis,
    SentimentType,
    ArgumentationSuggestion,
    SuggestionType,
    MeetingSummary,
    MeetingContext,
    ObjectionContext,
    MeetingStats,
)

__all__ = [
    "AudioChunk",
    "Speaker",
    "TranscriptionSegment",
    "Translation",
    "SuggestionResponse",
    "ConversationTurn",
    "SentimentAnalysis",
    "SentimentType",
    "ArgumentationSuggestion",
    "SuggestionType",
    "MeetingSummary",
    "MeetingContext",
    "ObjectionContext",
    "MeetingStats",
]
