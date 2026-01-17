"""Service interfaces (ports) for Clean Architecture."""
from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Optional
from datetime import datetime
from ..entities import (
    AudioChunk,
    Speaker,
    TranscriptionSegment,
    Translation,
    SuggestionResponse,
    SentimentAnalysis,
    ArgumentationSuggestion,
    MeetingContext,
    ObjectionContext,
    MeetingSummary,
)
from ..entities.analytics import (
    MeetingAnalytics,
    SpeakerAnalytics,
    AnalyticsSummary,
    TimeRange,
    ExportRequest,
    ExportResult,
)
from ..entities.speaker_management import (
    SpeakerEnrollmentRequest,
    SpeakerEnrollmentSession,
    EnrolledSpeaker,
    SpeakerIdentificationResult,
    SpeakerUpdateRequest,
    VoiceProfileQuality,
)


class ISpeechToTextService(ABC):
    """Interface for Speech-to-Text services."""

    @abstractmethod
    async def transcribe(
        self,
        audio_chunk: AudioChunk,
        language: Optional[str] = None
    ) -> TranscriptionSegment:
        """Transcribe audio chunk to text."""
        pass

    @abstractmethod
    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[AudioChunk],
        language: Optional[str] = None
    ) -> AsyncIterator[TranscriptionSegment]:
        """Transcribe audio stream in realtime."""
        pass


class ITextToSpeechService(ABC):
    """Interface for Text-to-Speech services."""

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        language: str,
        speaker_id: Optional[str] = None
    ) -> AudioChunk:
        """Synthesize text to speech."""
        pass

    @abstractmethod
    async def synthesize_stream(
        self,
        text: str,
        language: str,
        speaker_id: Optional[str] = None
    ) -> AsyncIterator[AudioChunk]:
        """Synthesize text to speech with streaming."""
        pass


class ISpeakerIdentificationService(ABC):
    """Interface for Speaker Identification services."""

    @abstractmethod
    async def identify_speaker(
        self,
        audio_chunk: AudioChunk,
        known_speakers: List[Speaker]
    ) -> Speaker:
        """Identify speaker from audio chunk."""
        pass

    @abstractmethod
    async def enroll_speaker(
        self,
        audio_chunks: List[AudioChunk],
        speaker_name: Optional[str] = None
    ) -> Speaker:
        """Enroll a new speaker."""
        pass


class ITranslationService(ABC):
    """Interface for Translation services."""

    @abstractmethod
    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str
    ) -> Translation:
        """Translate text from source to target language."""
        pass


class ILanguageModelService(ABC):
    """Interface for Language Model services."""

    @abstractmethod
    async def generate_suggestions(
        self,
        conversation_history: List[str],
        current_translation: Translation,
        target_language: str,
        num_suggestions: int = 3
    ) -> List[SuggestionResponse]:
        """Generate response suggestions based on conversation context."""
        pass

    @abstractmethod
    async def detect_language(self, text: str) -> str:
        """Detect the language of the text."""
        pass


class ISentimentAnalysisService(ABC):
    """Interface for Sentiment Analysis services."""

    @abstractmethod
    async def analyze_sentiment(
        self,
        text: str,
        language: Optional[str] = None
    ) -> SentimentAnalysis:
        """Analyze sentiment of text."""
        pass

    @abstractmethod
    async def analyze_conversation_sentiment(
        self,
        conversation_history: List[str]
    ) -> List[SentimentAnalysis]:
        """Analyze sentiment progression through conversation."""
        pass


class IArgumentationEngineService(ABC):
    """Interface for Argumentation Engine services."""

    @abstractmethod
    async def generate_argumentation_suggestions(
        self,
        text: str,
        conversation_history: List[str],
        meeting_context: MeetingContext,
        target_language: str,
        num_suggestions: int = 3
    ) -> List[ArgumentationSuggestion]:
        """Generate advanced argumentation-based suggestions."""
        pass

    @abstractmethod
    async def handle_objection(
        self,
        objection_context: ObjectionContext,
        conversation_history: List[str],
        target_language: str
    ) -> List[ArgumentationSuggestion]:
        """Generate counter-arguments for objections."""
        pass

    @abstractmethod
    async def suggest_closing_strategy(
        self,
        conversation_history: List[str],
        meeting_context: MeetingContext,
        target_language: str
    ) -> List[ArgumentationSuggestion]:
        """Suggest strategies to close/conclude the meeting."""
        pass


class IMeetingSummaryService(ABC):
    """Interface for Meeting Summary services."""

    @abstractmethod
    async def generate_summary(
        self,
        meeting_id: str,
        conversation_history: List[str],
        sentiment_timeline: List[SentimentAnalysis]
    ) -> MeetingSummary:
        """Generate comprehensive meeting summary."""
        pass

    @abstractmethod
    async def extract_action_items(
        self,
        conversation_history: List[str]
    ) -> List[str]:
        """Extract action items from conversation."""
        pass

    @abstractmethod
    async def extract_key_topics(
        self,
        conversation_history: List[str]
    ) -> List[str]:
        """Extract key topics discussed."""
        pass


class IAnalyticsService(ABC):
    """Interface for Analytics service."""

    @abstractmethod
    async def record_meeting_start(
        self,
        meeting_id: str,
        meeting_type: str,
        platform: str,
        processing_mode: str
    ) -> None:
        """Record the start of a meeting."""
        pass

    @abstractmethod
    async def record_meeting_end(
        self,
        meeting_id: str
    ) -> MeetingAnalytics:
        """Record the end of a meeting and return analytics."""
        pass

    @abstractmethod
    async def record_transcription(
        self,
        meeting_id: str,
        transcription: TranscriptionSegment,
        speaker: Optional[Speaker] = None
    ) -> None:
        """Record a transcription segment."""
        pass

    @abstractmethod
    async def record_sentiment(
        self,
        meeting_id: str,
        sentiment: SentimentAnalysis,
        speaker: Optional[Speaker] = None
    ) -> None:
        """Record sentiment analysis."""
        pass

    @abstractmethod
    async def record_suggestion(
        self,
        meeting_id: str,
        suggestion: ArgumentationSuggestion
    ) -> None:
        """Record a suggestion generated."""
        pass

    @abstractmethod
    async def get_meeting_analytics(
        self,
        meeting_id: str
    ) -> Optional[MeetingAnalytics]:
        """Get analytics for a specific meeting."""
        pass

    @abstractmethod
    async def get_summary(
        self,
        time_range: TimeRange,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> AnalyticsSummary:
        """Get analytics summary for a time range."""
        pass

    @abstractmethod
    async def get_speaker_analytics(
        self,
        speaker_id: str,
        time_range: TimeRange = TimeRange.ALL_TIME
    ) -> Optional[SpeakerAnalytics]:
        """Get analytics for a specific speaker."""
        pass

    @abstractmethod
    async def export_analytics(
        self,
        export_request: ExportRequest
    ) -> ExportResult:
        """Export analytics data to file."""
        pass

    @abstractmethod
    async def get_sentiment_timeline(
        self,
        time_range: TimeRange,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        granularity: str = "hour"  # "minute", "hour", "day"
    ) -> List[dict]:
        """Get sentiment data over time for charting."""
        pass

    @abstractmethod
    async def get_speaker_rankings(
        self,
        time_range: TimeRange,
        limit: int = 10
    ) -> List[SpeakerAnalytics]:
        """Get top speakers by talk time."""
        pass


class ISpeakerManagementService(ABC):
    """Interface for Speaker Management service."""

    @abstractmethod
    async def start_enrollment(
        self,
        request: SpeakerEnrollmentRequest
    ) -> SpeakerEnrollmentSession:
        """Start a new speaker enrollment session."""
        pass

    @abstractmethod
    async def add_enrollment_sample(
        self,
        session_id: str,
        audio_chunk: AudioChunk
    ) -> SpeakerEnrollmentSession:
        """Add voice sample to enrollment session."""
        pass

    @abstractmethod
    async def complete_enrollment(
        self,
        session_id: str
    ) -> EnrolledSpeaker:
        """Complete enrollment and create speaker profile."""
        pass

    @abstractmethod
    async def cancel_enrollment(
        self,
        session_id: str
    ) -> None:
        """Cancel enrollment session."""
        pass

    @abstractmethod
    async def identify_speaker(
        self,
        audio_chunk: AudioChunk
    ) -> SpeakerIdentificationResult:
        """Identify speaker from audio or detect new speaker."""
        pass

    @abstractmethod
    async def get_all_speakers(
        self
    ) -> List[EnrolledSpeaker]:
        """Get all enrolled speakers."""
        pass

    @abstractmethod
    async def get_speaker(
        self,
        speaker_id: str
    ) -> Optional[EnrolledSpeaker]:
        """Get specific enrolled speaker."""
        pass

    @abstractmethod
    async def update_speaker(
        self,
        request: SpeakerUpdateRequest
    ) -> EnrolledSpeaker:
        """Update speaker information."""
        pass

    @abstractmethod
    async def delete_speaker(
        self,
        speaker_id: str
    ) -> None:
        """Delete enrolled speaker."""
        pass

    @abstractmethod
    async def assess_voice_quality(
        self,
        speaker_id: str
    ) -> VoiceProfileQuality:
        """Assess quality of speaker's voice profile."""
        pass

    @abstractmethod
    async def retrain_speaker(
        self,
        speaker_id: str,
        audio_samples: List[AudioChunk]
    ) -> EnrolledSpeaker:
        """Retrain speaker voice profile with new samples."""
        pass
