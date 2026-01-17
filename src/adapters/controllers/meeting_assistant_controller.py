"""Meeting Assistant Controller."""
from typing import Optional
from datetime import datetime

from ...core.use_cases import MeetingAssistantUseCase
from ...core.entities import AudioChunk, MeetingContext
from ...infrastructure.database import Database


class MeetingAssistantController:
    """Controller for Meeting Assistant operations."""

    def __init__(
        self,
        use_case: MeetingAssistantUseCase,
        database: Database
    ):
        """Initialize controller."""
        self.use_case = use_case
        self.database = database
        self.meeting_id: Optional[str] = None

    async def initialize(self):
        """Initialize controller."""
        self.meeting_id = self.use_case.meeting_id

    async def process_audio(
        self,
        audio_chunk: AudioChunk
    ) -> dict:
        """Process audio with full meeting assistant analysis."""
        result = await self.use_case.process_audio_with_analysis(audio_chunk)

        # Save speaker to database if new
        if result.get("has_content") and result.get("speaker"):
            from ...core.entities import Speaker
            speaker = Speaker(
                speaker_id=result["speaker"]["id"],
                name=result["speaker"].get("name"),
                language=result["speaker"].get("language"),
            )
            await self.database.save_speaker(speaker)

        return result

    async def get_meeting_summary(self) -> dict:
        """Get comprehensive meeting summary."""
        summary = await self.use_case.generate_meeting_summary()

        return {
            "meeting_id": summary.meeting_id,
            "duration_seconds": summary.duration_seconds,
            "total_messages": summary.total_messages,
            "speakers_count": summary.speakers_count,
            "key_topics": summary.key_topics,
            "decisions_made": summary.decisions_made,
            "action_items": summary.action_items,
            "overall_sentiment": summary.overall_sentiment.value,
            "most_discussed_topics": summary.most_discussed_topics,
            "summary_text": summary.summary_text,
        }

    async def suggest_closing(self) -> list:
        """Get closing strategy suggestions."""
        suggestions = await self.use_case.suggest_closing()

        return [
            {
                "text": s.text,
                "type": s.suggestion_type.value,
                "priority": s.priority,
                "confidence": s.confidence,
                "context": s.context,
                "expected_outcome": s.expected_outcome,
            }
            for s in suggestions
        ]

    def clear_meeting(self):
        """Clear current meeting data."""
        self.use_case.clear_history()
        self.meeting_id = self.use_case.meeting_id
