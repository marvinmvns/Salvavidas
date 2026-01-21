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
        print(f"[UseCase] === Starting audio processing ===")
        print(f"[UseCase] Audio chunk: {len(audio_chunk.data)} bytes, source_lang: {source_language}")

        # Step 1: Identify speaker (if enabled)
        speaker = await self._identify_speaker(audio_chunk)
        print(f"[UseCase] Speaker identified: {speaker.speaker_id}")

        # Step 2: Transcribe audio
        transcription = await self.stt_service.transcribe(
            audio_chunk,
            language=source_language or speaker.language
        )
        transcription.speaker = speaker
        print(f"[UseCase] Transcription: '{transcription.text}' (lang: {transcription.language})")

        # Step 3: Use Whisper's detected language (more accurate than langdetect for short texts)
        if not source_language:
            # Whisper already detected the language during transcription
            source_language = transcription.language
            print(f"[UseCase] Using Whisper detected language: {source_language}")
            
            # STICKY LANGUAGE: If confident (e.g. not empty), save to speaker to avoid re-detection
            if source_language and transcription.text and len(transcription.text) > 5 and not speaker.language:
                try:
                    print(f"[UseCase] Setting language '{source_language}' for speaker {speaker.speaker_id}")
                    # Update local object
                    speaker.language = source_language
                    if hasattr(self.speaker_id_service, 'update_speaker_language'):
                         # Run update in background task if possible, but strict await here for now
                         print(f"[UseCase] Persisting language '{source_language}' for speaker {speaker.speaker_id}")
                         await self.speaker_id_service.update_speaker_language(speaker.speaker_id, source_language)
                    else:
                         print("[UseCase] Service does not support update_speaker_language")
                except Exception as e:
                    print(f"[UseCase] Failed to update speaker language: {e}")

        # Step 4: Translate to target language
        print(f"[UseCase] Translating: '{transcription.text}' from {source_language} to {self.target_language}")
        translation = await self.translation_service.translate(
            text=transcription.text,
            source_language=source_language,
            target_language=self.target_language
        )
        print(f"[UseCase] Translation result: '{translation.translated_text}'")

        # Step 5: Generate suggestions (if enabled)
        suggestions = []
        if self.enable_suggestions and transcription.text:
            print(f"[UseCase] Generating suggestions...")
            # Note: This adds latency. Ideally should be async/background.
            try:
                suggestions = await self.llm_service.generate_suggestions(
                    conversation_history=self.conversation_history,
                    current_translation=translation,
                    target_language=source_language,
                    num_suggestions=3
                )
                print(f"[UseCase] Generated {len(suggestions)} suggestions")
            except Exception as e:
                print(f"[UseCase] Error generating suggestions: {e}")

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
