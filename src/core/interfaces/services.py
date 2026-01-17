"""Service interfaces (ports) for Clean Architecture."""
from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Optional
from ..entities import (
    AudioChunk,
    Speaker,
    TranscriptionSegment,
    Translation,
    SuggestionResponse
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
