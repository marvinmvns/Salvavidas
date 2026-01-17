"""Service interfaces (ports) for Clean Architecture."""
from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Optional
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
