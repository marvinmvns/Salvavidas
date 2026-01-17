"""
Analytics entities for tracking and reporting meeting data.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum


class TimeRange(str, Enum):
    """Time range for analytics queries."""
    LAST_HOUR = "last_hour"
    LAST_DAY = "last_day"
    LAST_WEEK = "last_week"
    LAST_MONTH = "last_month"
    LAST_YEAR = "last_year"
    ALL_TIME = "all_time"
    CUSTOM = "custom"


@dataclass
class MeetingAnalytics:
    """Analytics data for a single meeting."""
    meeting_id: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: int
    total_speakers: int
    total_transcriptions: int
    total_translations: int
    total_suggestions: int

    # Sentiment metrics
    average_sentiment_score: float  # -1 to 1 scale
    sentiment_distribution: Dict[str, int]  # count per sentiment type

    # Speaker metrics
    speaker_talk_time: Dict[str, int]  # seconds per speaker
    most_active_speaker: Optional[str]

    # Language metrics
    languages_detected: List[str]
    primary_language: str

    # Engagement metrics
    questions_asked: int
    objections_raised: int
    positive_moments: int
    negative_moments: int

    # Metadata
    meeting_type: str  # "sales", "support", "internal", "other"
    meeting_platform: str  # "meet", "zoom", "teams", "desktop", "web"
    processing_mode: str  # "local", "fast", "premium"

    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class SentimentTrend:
    """Sentiment data point for trending analysis."""
    timestamp: datetime
    sentiment_type: str
    sentiment_score: float
    confidence: float
    text_snippet: str
    speaker_id: Optional[str] = None


@dataclass
class SpeakerAnalytics:
    """Analytics for a specific speaker across meetings."""
    speaker_id: str
    speaker_name: str
    total_meetings: int
    total_talk_time_seconds: int
    average_sentiment_score: float

    # Speaking patterns
    average_words_per_minute: float
    most_common_topics: List[str]

    # Emotional patterns
    emotional_range: Dict[str, float]  # percentage per emotion
    most_frequent_emotion: str

    # Engagement
    questions_asked: int
    objections_raised: int

    # Time-based
    first_seen: datetime
    last_seen: datetime


@dataclass
class DailyAnalytics:
    """Aggregated analytics for a single day."""
    date: datetime
    total_meetings: int
    total_duration_seconds: int
    total_speakers: int
    total_transcriptions: int
    average_sentiment_score: float

    # Peak activity
    peak_hour: int  # hour of day (0-23)
    peak_hour_meetings: int

    # Platform breakdown
    platform_usage: Dict[str, int]  # count per platform

    # Processing breakdown
    processing_mode_usage: Dict[str, int]  # count per mode


@dataclass
class AnalyticsSummary:
    """High-level analytics summary."""
    time_range: TimeRange
    start_date: datetime
    end_date: datetime

    # Meeting metrics
    total_meetings: int
    total_duration_seconds: int
    average_meeting_duration_seconds: float

    # Speaker metrics
    unique_speakers: int
    total_transcriptions: int
    total_words_transcribed: int

    # Sentiment metrics
    overall_sentiment_score: float
    sentiment_trend: str  # "improving", "declining", "stable"
    sentiment_distribution: Dict[str, int]

    # Engagement metrics
    total_suggestions_generated: int
    total_objections_handled: int
    total_questions_asked: int

    # Usage metrics
    most_used_platform: str
    most_used_processing_mode: str
    most_active_day: str
    most_active_hour: int

    # Language metrics
    languages_used: List[str]
    most_common_language: str

    # Trends
    daily_breakdown: List[DailyAnalytics] = field(default_factory=list)
    sentiment_timeline: List[SentimentTrend] = field(default_factory=list)
    speaker_rankings: List[SpeakerAnalytics] = field(default_factory=list)


@dataclass
class ExportRequest:
    """Request for exporting analytics data."""
    format: str  # "csv", "json", "pdf", "excel"
    time_range: TimeRange
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_detailed_transcripts: bool = False
    include_speaker_breakdown: bool = True
    include_sentiment_analysis: bool = True
    include_charts: bool = False  # for PDF export


@dataclass
class ExportResult:
    """Result of analytics export operation."""
    export_id: str
    format: str
    file_path: str
    file_size_bytes: int
    rows_exported: int
    created_at: datetime
    expires_at: Optional[datetime] = None
