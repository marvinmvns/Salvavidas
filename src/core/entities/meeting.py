"""Meeting-related entities."""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class SentimentType(str, Enum):
    """Sentiment types."""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"
    CONFUSED = "confused"
    CONCERNED = "concerned"
    EXCITED = "excited"


class SuggestionType(str, Enum):
    """Types of suggestions."""
    SALES = "sales"
    OBJECTION_HANDLING = "objection_handling"
    NEGOTIATION = "negotiation"
    CLARIFICATION = "clarification"
    CLOSING = "closing"
    EMPATHY = "empathy"
    TECHNICAL = "technical"
    GENERAL = "general"


class MeetingContext(str, Enum):
    """Meeting context types."""
    SALES = "sales"
    INTERVIEW = "interview"
    PRESENTATION = "presentation"
    NEGOTIATION = "negotiation"
    GENERAL = "general"


@dataclass
class SentimentAnalysis:
    """Sentiment analysis result."""
    sentiment: SentimentType
    confidence: float  # 0.0 to 1.0
    emotion_scores: Dict[str, float]  # e.g., {"happy": 0.8, "sad": 0.1, ...}
    text_analyzed: str
    timestamp: datetime

    def get_emoji(self) -> str:
        """Get emoji representation of sentiment."""
        emoji_map = {
            SentimentType.VERY_POSITIVE: "😄",
            SentimentType.POSITIVE: "🙂",
            SentimentType.NEUTRAL: "😐",
            SentimentType.NEGATIVE: "😟",
            SentimentType.VERY_NEGATIVE: "😢",
            SentimentType.CONFUSED: "😕",
            SentimentType.CONCERNED: "😰",
            SentimentType.EXCITED: "🤩",
        }
        return emoji_map.get(self.sentiment, "😐")


@dataclass
class ArgumentationSuggestion:
    """Suggestion with argumentation strategy."""
    text: str
    suggestion_type: SuggestionType
    priority: int  # 1 (highest) to 5 (lowest)
    confidence: float  # 0.0 to 1.0
    context: str  # Why this suggestion was made
    keywords: List[str]  # Key points to emphasize
    expected_outcome: str  # What this might achieve
    timestamp: datetime


@dataclass
class MeetingSummary:
    """Summary of a meeting."""
    meeting_id: str
    start_time: datetime
    end_time: datetime
    duration_seconds: int
    total_messages: int
    speakers_count: int
    key_topics: List[str]
    decisions_made: List[str]
    action_items: List[str]
    overall_sentiment: SentimentType
    sentiment_timeline: List[SentimentAnalysis]
    most_discussed_topics: List[str]
    summary_text: str


@dataclass
class ObjectionContext:
    """Context about an objection raised."""
    objection_text: str
    objection_type: str  # e.g., "price", "timeline", "features", "competitor"
    severity: float  # 0.0 (minor) to 1.0 (critical)
    speaker_id: str
    timestamp: datetime
    previous_context: List[str]  # Previous messages for context


@dataclass
class MeetingStats:
    """Real-time meeting statistics."""
    duration_seconds: int
    message_count: int
    speakers_count: int
    current_topic: Optional[str]
    sentiment_trend: str  # "improving", "declining", "stable"
    engagement_score: float  # 0.0 to 1.0
    last_updated: datetime
