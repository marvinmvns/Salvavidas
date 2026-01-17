"""Voice translation controller (MVC)."""
from typing import AsyncIterator, Optional, List
from datetime import datetime
from ...core.use_cases import ProcessVoiceTranslationUseCase
from ...core.entities import AudioChunk, ConversationTurn, Speaker
from ...infrastructure.database import Database


class VoiceTranslationController:
    """Controller for voice translation operations."""

    def __init__(
        self,
        use_case: ProcessVoiceTranslationUseCase,
        database: Database,
        session_id: Optional[str] = None
    ):
        """Initialize controller."""
        self.use_case = use_case
        self.database = database
        self.session_id = session_id or f"session_{datetime.now().timestamp()}"

    async def initialize(self):
        """Initialize controller - load known speakers from database."""
        speakers = await self.database.get_all_speakers()
        for speaker in speakers:
            self.use_case.add_known_speaker(speaker)

    async def process_audio(
        self,
        audio_chunk: AudioChunk,
        source_language: Optional[str] = None
    ) -> ConversationTurn:
        """Process a single audio chunk."""
        # Execute use case
        conversation_turn = await self.use_case.execute(
            audio_chunk,
            source_language
        )

        # Save speaker to database
        await self.database.save_speaker(conversation_turn.speaker)

        # Save conversation history
        # (Could be implemented to save to database)

        return conversation_turn

    async def process_audio_stream(
        self,
        audio_stream: AsyncIterator[AudioChunk],
        source_language: Optional[str] = None
    ) -> AsyncIterator[ConversationTurn]:
        """Process streaming audio."""
        async for conversation_turn in self.use_case.execute_stream(
            audio_stream,
            source_language
        ):
            # Save speaker
            await self.database.save_speaker(conversation_turn.speaker)

            yield conversation_turn

    async def get_known_speakers(self) -> List[Speaker]:
        """Get all known speakers."""
        return await self.database.get_all_speakers()

    async def enroll_speaker(
        self,
        audio_chunks: List[AudioChunk],
        speaker_name: str
    ) -> Speaker:
        """Enroll a new speaker."""
        speaker = await self.use_case.speaker_id_service.enroll_speaker(
            audio_chunks,
            speaker_name
        )

        # Save to database
        await self.database.save_speaker(speaker)

        # Add to use case
        self.use_case.add_known_speaker(speaker)

        return speaker

    def clear_conversation_history(self):
        """Clear conversation history."""
        self.use_case.clear_conversation_history()
