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
    ISpeakerManagementService,
    ITranslationService,
    ILanguageModelService,
)


class ProcessVoiceTranslationUseCase:
    """Use case for processing voice translation with speaker identification."""

    def __init__(
        self,
        stt_service: ISpeechToTextService,
        speaker_id_service: ISpeakerManagementService,
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
        self.conversation_history: List[str] = []

    async def execute(
        self,
        audio_chunk: AudioChunk,
        source_language: Optional[str] = None
    ) -> ConversationTurn:
        """Execute the use case for a single audio chunk."""
        import time

        print(f"[UseCase] === Starting audio processing ===")
        print(f"[UseCase] Audio chunk: {len(audio_chunk.data)} bytes, source_lang: {source_language}")

        # Performance tracking
        perf = {}
        start_total = time.time()

        # Step 1: Identify speaker (if enabled)
        start_speaker = time.time()
        speaker = await self._identify_speaker(audio_chunk)
        perf['speaker_id_ms'] = int((time.time() - start_speaker) * 1000)
        print(f"[UseCase] Speaker identified: {speaker.speaker_id} ({perf['speaker_id_ms']}ms)")

        # Step 2: Transcribe audio
        start_stt = time.time()
        transcription = await self.stt_service.transcribe(
            audio_chunk,
            language=source_language or speaker.language
        )
        perf['stt_ms'] = int((time.time() - start_stt) * 1000)
        transcription.speaker = speaker
        print(f"[UseCase] Transcription: '{transcription.text}' (lang: {transcription.language}) ({perf['stt_ms']}ms)")

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
        start_translation = time.time()
        print(f"[UseCase] Translating: '{transcription.text}' from {source_language} to {self.target_language}")
        translation = await self.translation_service.translate(
            text=transcription.text,
            source_language=source_language,
            target_language=self.target_language
        )
        perf['translation_ms'] = int((time.time() - start_translation) * 1000)
        print(f"[UseCase] Translation result: '{translation.translated_text}' ({perf['translation_ms']}ms)")

        # Step 5: Generate suggestions (if enabled)
        suggestions = []
        perf['llm_ms'] = 0
        if self.enable_suggestions and transcription.text:
            start_llm = time.time()
            print(f"[UseCase] Generating suggestions...")
            # Note: This adds latency. Ideally should be async/background.
            try:
                suggestions = await self.llm_service.generate_suggestions(
                    conversation_history=self.conversation_history,
                    current_translation=translation,
                    target_language=source_language,
                    num_suggestions=3
                )
                perf['llm_ms'] = int((time.time() - start_llm) * 1000)
                print(f"[UseCase] Generated {len(suggestions)} suggestions ({perf['llm_ms']}ms)")
            except Exception as e:
                print(f"[UseCase] Error generating suggestions: {e}")

        # Update conversation history
        self.conversation_history.append(f"{speaker.speaker_id}: {transcription.text}")

        # Calculate total
        perf['total_ms'] = int((time.time() - start_total) * 1000)

        # Log detailed performance
        print(f"[PERF] Speaker: {perf['speaker_id_ms']}ms | STT: {perf['stt_ms']}ms | Translation: {perf['translation_ms']}ms | LLM: {perf['llm_ms']}ms | TOTAL: {perf['total_ms']}ms")

        # Create conversation turn
        turn = ConversationTurn(
            transcription=transcription,
            translation=translation,
            suggestions=suggestions,
            timestamp=datetime.now()
        )

        # Attach performance metrics to the turn (add as attribute)
        turn.performance = perf

        return turn

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
        """Identify speaker using modern SpeakerManagementService."""
        if not self.enable_speaker_id:
            return Speaker(speaker_id="default", confidence=1.0)

        try:
            # Use new API - returns SpeakerIdentificationResult
            result = await self.speaker_id_service.identify_speaker(audio_chunk)

            # Convert result to Speaker entity
            if result.identified and result.speaker:
                # Enrolled speaker recognized
                return Speaker(
                    speaker_id=result.speaker.speaker_id,
                    name=result.speaker.name,
                    language=result.speaker.language,
                    confidence=result.confidence,
                    embedding=result.speaker.voice_embedding
                )
            elif result.speaker:
                # Temporary speaker (matched existing temp)
                return Speaker(
                    speaker_id=result.speaker.speaker_id,
                    name=result.speaker.name or result.suggested_name,
                    language=result.speaker.language,
                    confidence=result.confidence,
                    embedding=None
                )
            else:
                # New temporary speaker
                return Speaker(
                    speaker_id=result.suggested_name or "Unknown",
                    name=result.suggested_name,
                    language=None,
                    confidence=result.confidence,
                    embedding=None
                )
        except Exception as e:
            print(f"[UseCase] Error identifying speaker: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to default speaker
            return Speaker(speaker_id="default", confidence=0.0)

    def add_known_speaker(self, speaker: Speaker) -> None:
        """Add a known speaker - deprecated with new speaker management."""
        # No-op: SpeakerManagementService handles this internally
        pass

    def clear_conversation_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history.clear()
