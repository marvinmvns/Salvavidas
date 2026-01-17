"""Meeting Assistant Use Case."""
from typing import List, Optional
from datetime import datetime

from ..entities import (
    AudioChunk,
    Speaker,
    ConversationTurn,
    SentimentAnalysis,
    ArgumentationSuggestion,
    MeetingContext,
    ObjectionContext,
    MeetingSummary,
    MeetingStats,
)
from ..interfaces import (
    ISpeechToTextService,
    ISpeakerIdentificationService,
    ITranslationService,
    ISentimentAnalysisService,
    IArgumentationEngineService,
    IMeetingSummaryService,
)


class MeetingAssistantUseCase:
    """Use case for Meeting Assistant functionality."""

    def __init__(
        self,
        stt_service: ISpeechToTextService,
        speaker_id_service: ISpeakerIdentificationService,
        translation_service: ITranslationService,
        sentiment_service: ISentimentAnalysisService,
        argumentation_service: IArgumentationEngineService,
        summary_service: IMeetingSummaryService,
        meeting_context: MeetingContext = MeetingContext.GENERAL,
        target_language: str = "en",
    ):
        """Initialize Meeting Assistant use case."""
        self.stt_service = stt_service
        self.speaker_id_service = speaker_id_service
        self.translation_service = translation_service
        self.sentiment_service = sentiment_service
        self.argumentation_service = argumentation_service
        self.summary_service = summary_service
        self.meeting_context = meeting_context
        self.target_language = target_language

        # Meeting state
        self.meeting_id = f"meeting_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.conversation_history: List[str] = []
        self.sentiment_timeline: List[SentimentAnalysis] = []
        self.known_speakers: List[Speaker] = []
        self.start_time = datetime.now()

    async def process_audio_with_analysis(
        self,
        audio_chunk: AudioChunk,
    ) -> dict:
        """Process audio and return comprehensive analysis."""

        # 1. Transcribe
        transcription = await self.stt_service.transcribe(audio_chunk)

        if not transcription.text.strip():
            return {
                "transcription": "",
                "has_content": False
            }

        # 2. Identify speaker
        speaker = await self.speaker_id_service.identify_speaker(
            audio_chunk,
            self.known_speakers
        )

        # Update known speakers
        if speaker not in self.known_speakers:
            self.known_speakers.append(speaker)

        # 3. Detect language
        detected_language = transcription.language

        # 4. Translate if needed
        translation = None
        if detected_language != self.target_language:
            translation = await self.translation_service.translate(
                transcription.text,
                detected_language,
                self.target_language
            )

        # 5. Analyze sentiment
        sentiment = await self.sentiment_service.analyze_sentiment(
            transcription.text,
            detected_language
        )
        self.sentiment_timeline.append(sentiment)

        # 6. Generate argumentation suggestions
        suggestions = await self.argumentation_service.generate_argumentation_suggestions(
            transcription.text,
            self.conversation_history,
            self.meeting_context,
            detected_language,
            num_suggestions=3
        )

        # 7. Check for objections
        objection_detected = await self._detect_objection(transcription.text)
        objection_responses = []

        if objection_detected:
            objection_context = ObjectionContext(
                objection_text=transcription.text,
                objection_type=objection_detected["type"],
                severity=objection_detected["severity"],
                speaker_id=speaker.speaker_id,
                timestamp=datetime.now(),
                previous_context=self.conversation_history[-3:]
            )

            objection_responses = await self.argumentation_service.handle_objection(
                objection_context,
                self.conversation_history,
                detected_language
            )

        # 8. Update conversation history
        self.conversation_history.append(transcription.text)

        # 9. Calculate meeting stats
        stats = self._calculate_meeting_stats()

        return {
            "has_content": True,
            "transcription": transcription.text,
            "translation": translation.translated_text if translation else transcription.text,
            "speaker": {
                "id": speaker.speaker_id,
                "name": speaker.name,
                "language": detected_language,
            },
            "sentiment": {
                "type": sentiment.sentiment.value,
                "emoji": sentiment.get_emoji(),
                "confidence": sentiment.confidence,
                "emotions": sentiment.emotion_scores,
            },
            "suggestions": [
                {
                    "text": s.text,
                    "type": s.suggestion_type.value,
                    "priority": s.priority,
                    "confidence": s.confidence,
                    "context": s.context,
                    "keywords": s.keywords,
                }
                for s in suggestions
            ],
            "objection": {
                "detected": objection_detected is not None,
                "type": objection_detected["type"] if objection_detected else None,
                "severity": objection_detected["severity"] if objection_detected else 0,
                "responses": [
                    {
                        "text": r.text,
                        "priority": r.priority,
                        "confidence": r.confidence,
                    }
                    for r in objection_responses
                ]
            },
            "meeting_stats": {
                "duration_seconds": stats.duration_seconds,
                "message_count": stats.message_count,
                "speakers_count": stats.speakers_count,
                "sentiment_trend": stats.sentiment_trend,
                "engagement_score": stats.engagement_score,
            }
        }

    async def generate_meeting_summary(self) -> MeetingSummary:
        """Generate comprehensive meeting summary."""
        return await self.summary_service.generate_summary(
            self.meeting_id,
            self.conversation_history,
            self.sentiment_timeline
        )

    async def suggest_closing(self) -> List[ArgumentationSuggestion]:
        """Get closing strategy suggestions."""
        return await self.argumentation_service.suggest_closing_strategy(
            self.conversation_history,
            self.meeting_context,
            self.target_language
        )

    def _calculate_meeting_stats(self) -> MeetingStats:
        """Calculate current meeting statistics."""
        duration = (datetime.now() - self.start_time).total_seconds()

        # Calculate sentiment trend
        if len(self.sentiment_timeline) >= 3:
            recent_sentiments = self.sentiment_timeline[-3:]
            sentiment_scores = [self._sentiment_to_score(s.sentiment) for s in recent_sentiments]

            if sentiment_scores[-1] > sentiment_scores[0]:
                trend = "improving"
            elif sentiment_scores[-1] < sentiment_scores[0]:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"

        # Calculate engagement (based on message frequency)
        messages_per_minute = len(self.conversation_history) / max(1, duration / 60)
        engagement = min(1.0, messages_per_minute / 10)  # Normalize to 0-1

        return MeetingStats(
            duration_seconds=int(duration),
            message_count=len(self.conversation_history),
            speakers_count=len(self.known_speakers),
            current_topic=None,  # Could be extracted from recent messages
            sentiment_trend=trend,
            engagement_score=engagement,
            last_updated=datetime.now()
        )

    async def _detect_objection(self, text: str) -> Optional[dict]:
        """Detect if text contains an objection."""
        text_lower = text.lower()

        # Price objections
        price_keywords = ['expensive', 'cost', 'price', 'budget', 'afford', 'cheap']
        if any(kw in text_lower for kw in price_keywords):
            severity = 0.7 if any(w in text_lower for w in ['too', 'very', 'really']) else 0.5
            return {"type": "price", "severity": severity}

        # Timeline objections
        timeline_keywords = ['time', 'long', 'quick', 'deadline', 'urgent']
        if any(kw in text_lower for kw in timeline_keywords):
            return {"type": "timeline", "severity": 0.6}

        # Feature objections
        feature_keywords = ['feature', 'functionality', 'missing', 'need', 'require']
        if any(kw in text_lower for kw in feature_keywords):
            return {"type": "features", "severity": 0.5}

        # Competitor mentions
        competitor_keywords = ['competitor', 'alternative', 'other', 'versus']
        if any(kw in text_lower for kw in competitor_keywords):
            return {"type": "competitor", "severity": 0.7}

        return None

    def _sentiment_to_score(self, sentiment) -> float:
        """Convert sentiment to numeric score."""
        from ..entities import SentimentType

        score_map = {
            SentimentType.VERY_POSITIVE: 2.0,
            SentimentType.POSITIVE: 1.0,
            SentimentType.EXCITED: 1.5,
            SentimentType.NEUTRAL: 0.0,
            SentimentType.CONCERNED: -0.5,
            SentimentType.CONFUSED: -0.5,
            SentimentType.NEGATIVE: -1.0,
            SentimentType.VERY_NEGATIVE: -2.0,
        }
        return score_map.get(sentiment, 0.0)

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history.clear()
        self.sentiment_timeline.clear()
        self.start_time = datetime.now()
