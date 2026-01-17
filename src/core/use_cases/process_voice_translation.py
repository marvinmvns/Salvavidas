"""Process voice translation use case."""
from typing import AsyncIterator, List, Optional
from datetime import datetime
from ..entities import (
    AudioChunk,
    Speaker,
    TranscriptionSegment,
    Translation,
    ConversationTurn
)
from ..interfaces import (
    ISpeechToTextService,
    ISpeakerIdentificationService,
    ITranslationService,
    ILanguageModelService,
)


class ProcessVoiceTranslationUseCase:
    """Use case for processing voice translation with speaker identification."""

    def __init__(
        self,
        stt_service: ISpeechToTextService,
        speaker_id_service: ISpeakerIdentificationService,
        translation_service: ITranslationService,
        llm_service: ILanguageModelService,
        target_language: str,
        enable_speaker_id: bool = True,
        enable_suggestions: bool = True,
    ):
        """Initialize use case."""
        self.stt_service = stt_service
        self.speaker_id_service = speaker_id_service
        self.translation_service = translation_service
        self.llm_service = llm_service
        self.target_language = target_language
        self.enable_speaker_id = enable_speaker_id
        self.enable_suggestions = enable_suggestions
        self.known_speakers: List[Speaker] = []
        self.conversation_history: List[str] = []

    async def execute(
        self,
        audio_chunk: AudioChunk,
        source_language: Optional[str] = None
    ) -> ConversationTurn:
        """Execute the use case for a single audio chunk."""
        # Step 1: Identify speaker (if enabled)
        speaker = await self._identify_speaker(audio_chunk)

        # Step 2: Transcribe audio
        transcription = await self.stt_service.transcribe(
            audio_chunk,
            language=source_language or speaker.language
        )
        transcription.speaker = speaker

        # Step 3: Detect language if not specified
        if not source_language:
            source_language = await self.llm_service.detect_language(
                transcription.text
            )

        # Step 4: Translate to target language
        translation = await self.translation_service.translate(
            text=transcription.text,
            source_language=source_language,
            target_language=self.target_language
        )

        # Step 5: Generate suggestions (if enabled)
        suggestions = []
        if self.enable_suggestions:
            suggestions = await self.llm_service.generate_suggestions(
                conversation_history=self.conversation_history,
                current_translation=translation,
                target_language=source_language,  # Suggest in speaker's language
                num_suggestions=3
            )

        # Update conversation history
        self.conversation_history.append(f"{speaker.speaker_id}: {transcription.text}")

        # Create conversation turn
        return ConversationTurn(
            transcription=transcription,
            translation=translation,
            suggestions=suggestions,
            timestamp=datetime.now()
        )

    async def execute_stream(
        self,
        audio_stream: AsyncIterator[AudioChunk],
        source_language: Optional[str] = None
    ) -> AsyncIterator[ConversationTurn]:
        """Execute the use case for streaming audio."""
        async for transcription in self.stt_service.transcribe_stream(
            audio_stream,
            language=source_language
        ):
            # For streaming, we process each transcription segment
            # Identify speaker from the transcription
            speaker = transcription.speaker

            # Detect language if not specified
            if not source_language:
                detected_lang = await self.llm_service.detect_language(
                    transcription.text
                )
            else:
                detected_lang = source_language

            # Translate
            translation = await self.translation_service.translate(
                text=transcription.text,
                source_language=detected_lang,
                target_language=self.target_language
            )

            # Generate suggestions
            suggestions = []
            if self.enable_suggestions:
                suggestions = await self.llm_service.generate_suggestions(
                    conversation_history=self.conversation_history,
                    current_translation=translation,
                    target_language=detected_lang,
                    num_suggestions=3
                )

            # Update history
            self.conversation_history.append(
                f"{speaker.speaker_id}: {transcription.text}"
            )

            # Yield conversation turn
            yield ConversationTurn(
                transcription=transcription,
                translation=translation,
                suggestions=suggestions,
                timestamp=datetime.now()
            )

    async def _identify_speaker(self, audio_chunk: AudioChunk) -> Speaker:
        """Identify or enroll speaker."""
        if not self.enable_speaker_id:
            return Speaker(speaker_id="default", confidence=1.0)

        try:
            speaker = await self.speaker_id_service.identify_speaker(
                audio_chunk,
                self.known_speakers
            )

            # If confidence is low, this might be a new speaker
            if speaker.confidence < 0.6:
                new_speaker = await self.speaker_id_service.enroll_speaker(
                    [audio_chunk]
                )
                self.known_speakers.append(new_speaker)
                return new_speaker

            return speaker
        except Exception:
            # Fallback to default speaker
            return Speaker(speaker_id="default", confidence=0.0)

    def add_known_speaker(self, speaker: Speaker) -> None:
        """Add a known speaker to the list."""
        if speaker not in self.known_speakers:
            self.known_speakers.append(speaker)

    def clear_conversation_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history.clear()
