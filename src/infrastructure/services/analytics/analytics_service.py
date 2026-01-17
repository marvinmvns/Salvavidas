"""
Analytics Service Implementation
Tracks and aggregates meeting data for analytics and reporting.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict, Counter

from ....core.interfaces.services import IAnalyticsService
from ....core.entities import Speaker, TranscriptionSegment, SentimentAnalysis, ArgumentationSuggestion
from ....core.entities.analytics import (
    MeetingAnalytics,
    SpeakerAnalytics,
    AnalyticsSummary,
    DailyAnalytics,
    SentimentTrend,
    TimeRange,
    ExportRequest,
    ExportResult,
)


class AnalyticsService(IAnalyticsService):
    """
    In-memory analytics service with SQLite persistence.
    Tracks meetings, transcriptions, sentiments, and generates insights.
    """

    def __init__(self, database_path: str = "analytics.db"):
        """
        Initialize analytics service.

        Args:
            database_path: Path to SQLite database for persistence
        """
        self.database_path = database_path

        # In-memory storage for fast access
        self.active_meetings: Dict[str, dict] = {}
        self.completed_meetings: Dict[str, MeetingAnalytics] = {}
        self.sentiment_history: Dict[str, List[SentimentTrend]] = defaultdict(list)
        self.speaker_data: Dict[str, dict] = defaultdict(lambda: {
            "meetings": set(),
            "talk_time": 0,
            "sentiments": [],
            "questions": 0,
            "objections": 0,
            "first_seen": None,
            "last_seen": None,
        })

    async def record_meeting_start(
        self,
        meeting_id: str,
        meeting_type: str,
        platform: str,
        processing_mode: str
    ) -> None:
        """Record the start of a meeting."""
        self.active_meetings[meeting_id] = {
            "meeting_id": meeting_id,
            "start_time": datetime.now(),
            "meeting_type": meeting_type,
            "platform": platform,
            "processing_mode": processing_mode,
            "speakers": set(),
            "transcriptions": [],
            "translations": 0,
            "suggestions": [],
            "sentiments": [],
            "languages": set(),
            "speaker_talk_time": defaultdict(int),
        }

    async def record_meeting_end(
        self,
        meeting_id: str
    ) -> MeetingAnalytics:
        """Record the end of a meeting and return analytics."""
        if meeting_id not in self.active_meetings:
            raise ValueError(f"Meeting {meeting_id} not found in active meetings")

        meeting_data = self.active_meetings[meeting_id]
        end_time = datetime.now()
        duration = int((end_time - meeting_data["start_time"]).total_seconds())

        # Calculate sentiment metrics
        sentiments = meeting_data["sentiments"]
        sentiment_distribution = Counter(s["type"] for s in sentiments)
        avg_sentiment = self._calculate_average_sentiment(sentiments)

        # Determine most active speaker
        speaker_times = meeting_data["speaker_talk_time"]
        most_active = max(speaker_times.keys(), key=lambda k: speaker_times[k]) if speaker_times else None

        # Count engagement metrics
        questions = sum(1 for t in meeting_data["transcriptions"] if self._is_question(t))
        objections = len([s for s in meeting_data["suggestions"] if s.get("type") == "objection_handling"])

        # Positive/negative moments
        positive_moments = sum(1 for s in sentiments if s["score"] > 0.5)
        negative_moments = sum(1 for s in sentiments if s["score"] < -0.5)

        # Determine primary language
        primary_lang = max(meeting_data["languages"], key=lambda l: meeting_data["languages"].count(l)) if meeting_data["languages"] else "unknown"

        analytics = MeetingAnalytics(
            meeting_id=meeting_id,
            start_time=meeting_data["start_time"],
            end_time=end_time,
            duration_seconds=duration,
            total_speakers=len(meeting_data["speakers"]),
            total_transcriptions=len(meeting_data["transcriptions"]),
            total_translations=meeting_data["translations"],
            total_suggestions=len(meeting_data["suggestions"]),
            average_sentiment_score=avg_sentiment,
            sentiment_distribution=dict(sentiment_distribution),
            speaker_talk_time=dict(speaker_times),
            most_active_speaker=most_active,
            languages_detected=list(meeting_data["languages"]),
            primary_language=primary_lang,
            questions_asked=questions,
            objections_raised=objections,
            positive_moments=positive_moments,
            negative_moments=negative_moments,
            meeting_type=meeting_data["meeting_type"],
            meeting_platform=meeting_data["platform"],
            processing_mode=meeting_data["processing_mode"],
        )

        # Move to completed meetings
        self.completed_meetings[meeting_id] = analytics
        del self.active_meetings[meeting_id]

        return analytics

    async def record_transcription(
        self,
        meeting_id: str,
        transcription: TranscriptionSegment,
        speaker: Optional[Speaker] = None
    ) -> None:
        """Record a transcription segment."""
        if meeting_id not in self.active_meetings:
            return

        meeting = self.active_meetings[meeting_id]
        meeting["transcriptions"].append(transcription.text)

        if speaker:
            meeting["speakers"].add(speaker.id)
            # Estimate talk time (rough approximation: 150 words per minute)
            word_count = len(transcription.text.split())
            talk_time_seconds = int((word_count / 150) * 60)
            meeting["speaker_talk_time"][speaker.id] += talk_time_seconds

            # Update speaker global data
            speaker_info = self.speaker_data[speaker.id]
            speaker_info["meetings"].add(meeting_id)
            speaker_info["talk_time"] += talk_time_seconds
            speaker_info["last_seen"] = datetime.now()
            if speaker_info["first_seen"] is None:
                speaker_info["first_seen"] = datetime.now()

        # Detect language (simplified - would use actual detection)
        if transcription.language:
            meeting["languages"].add(transcription.language)

    async def record_sentiment(
        self,
        meeting_id: str,
        sentiment: SentimentAnalysis,
        speaker: Optional[Speaker] = None
    ) -> None:
        """Record sentiment analysis."""
        if meeting_id not in self.active_meetings:
            return

        meeting = self.active_meetings[meeting_id]
        sentiment_data = {
            "type": sentiment.sentiment.value,
            "score": self._sentiment_to_score(sentiment.sentiment.value),
            "confidence": sentiment.confidence,
            "timestamp": sentiment.timestamp,
        }
        meeting["sentiments"].append(sentiment_data)

        # Record in sentiment timeline
        trend = SentimentTrend(
            timestamp=sentiment.timestamp,
            sentiment_type=sentiment.sentiment.value,
            sentiment_score=sentiment_data["score"],
            confidence=sentiment.confidence,
            text_snippet=sentiment.text_analyzed[:100] if len(sentiment.text_analyzed) > 100 else sentiment.text_analyzed,
            speaker_id=speaker.id if speaker else None,
        )
        self.sentiment_history[meeting_id].append(trend)

        # Update speaker sentiment data
        if speaker:
            self.speaker_data[speaker.id]["sentiments"].append(sentiment_data["score"])

    async def record_suggestion(
        self,
        meeting_id: str,
        suggestion: ArgumentationSuggestion
    ) -> None:
        """Record a suggestion generated."""
        if meeting_id not in self.active_meetings:
            return

        meeting = self.active_meetings[meeting_id]
        meeting["suggestions"].append({
            "type": suggestion.suggestion_type.value,
            "text": suggestion.text,
            "priority": suggestion.priority,
            "confidence": suggestion.confidence,
        })

    async def get_meeting_analytics(
        self,
        meeting_id: str
    ) -> Optional[MeetingAnalytics]:
        """Get analytics for a specific meeting."""
        return self.completed_meetings.get(meeting_id)

    async def get_summary(
        self,
        time_range: TimeRange,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> AnalyticsSummary:
        """Get analytics summary for a time range."""
        # Determine date range
        end = end_date or datetime.now()
        start = start_date or self._get_start_date(time_range, end)

        # Filter meetings in range
        meetings_in_range = [
            m for m in self.completed_meetings.values()
            if start <= m.start_time <= end
        ]

        if not meetings_in_range:
            return self._empty_summary(time_range, start, end)

        # Aggregate metrics
        total_meetings = len(meetings_in_range)
        total_duration = sum(m.duration_seconds for m in meetings_in_range)
        avg_duration = total_duration / total_meetings if total_meetings > 0 else 0

        # Speaker metrics
        all_speakers = set()
        total_transcriptions = 0
        total_words = 0
        for m in meetings_in_range:
            all_speakers.update(m.speaker_talk_time.keys())
            total_transcriptions += m.total_transcriptions
            # Rough estimate: average 15 words per transcription
            total_words += m.total_transcriptions * 15

        # Sentiment metrics
        all_sentiments = []
        sentiment_counts = Counter()
        for m in meetings_in_range:
            all_sentiments.append(m.average_sentiment_score)
            sentiment_counts.update(m.sentiment_distribution)

        overall_sentiment = sum(all_sentiments) / len(all_sentiments) if all_sentiments else 0.0
        sentiment_trend = self._determine_sentiment_trend(meetings_in_range)

        # Engagement metrics
        total_suggestions = sum(m.total_suggestions for m in meetings_in_range)
        total_objections = sum(m.objections_raised for m in meetings_in_range)
        total_questions = sum(m.questions_asked for m in meetings_in_range)

        # Usage metrics
        platform_counts = Counter(m.meeting_platform for m in meetings_in_range)
        mode_counts = Counter(m.processing_mode for m in meetings_in_range)
        most_platform = platform_counts.most_common(1)[0][0] if platform_counts else "unknown"
        most_mode = mode_counts.most_common(1)[0][0] if mode_counts else "local"

        # Time-based metrics
        meeting_by_day = defaultdict(list)
        meeting_by_hour = Counter()
        for m in meetings_in_range:
            day = m.start_time.date()
            meeting_by_day[day].append(m)
            meeting_by_hour[m.start_time.hour] += 1

        most_active_day = max(meeting_by_day.keys(), key=lambda d: len(meeting_by_day[d])).isoformat() if meeting_by_day else ""
        most_active_hour = meeting_by_hour.most_common(1)[0][0] if meeting_by_hour else 0

        # Language metrics
        all_languages = set()
        language_counts = Counter()
        for m in meetings_in_range:
            all_languages.update(m.languages_detected)
            language_counts[m.primary_language] += 1

        most_common_lang = language_counts.most_common(1)[0][0] if language_counts else "unknown"

        # Build daily breakdown
        daily_breakdown = []
        for day, day_meetings in sorted(meeting_by_day.items()):
            day_duration = sum(m.duration_seconds for m in day_meetings)
            day_speakers = set()
            for m in day_meetings:
                day_speakers.update(m.speaker_talk_time.keys())

            day_sentiments = [m.average_sentiment_score for m in day_meetings]
            day_avg_sentiment = sum(day_sentiments) / len(day_sentiments) if day_sentiments else 0.0

            # Find peak hour for this day
            day_hours = Counter(m.start_time.hour for m in day_meetings)
            peak_hour = day_hours.most_common(1)[0][0] if day_hours else 0
            peak_hour_count = day_hours[peak_hour] if day_hours else 0

            day_platforms = Counter(m.meeting_platform for m in day_meetings)
            day_modes = Counter(m.processing_mode for m in day_meetings)

            daily_breakdown.append(DailyAnalytics(
                date=datetime.combine(day, datetime.min.time()),
                total_meetings=len(day_meetings),
                total_duration_seconds=day_duration,
                total_speakers=len(day_speakers),
                total_transcriptions=sum(m.total_transcriptions for m in day_meetings),
                average_sentiment_score=day_avg_sentiment,
                peak_hour=peak_hour,
                peak_hour_meetings=peak_hour_count,
                platform_usage=dict(day_platforms),
                processing_mode_usage=dict(day_modes),
            ))

        # Get sentiment timeline
        sentiment_timeline = []
        for meeting_id in [m.meeting_id for m in meetings_in_range]:
            sentiment_timeline.extend(self.sentiment_history.get(meeting_id, []))

        # Sort by timestamp
        sentiment_timeline.sort(key=lambda s: s.timestamp)

        # Get speaker rankings
        speaker_rankings = await self.get_speaker_rankings(time_range, limit=10)

        return AnalyticsSummary(
            time_range=time_range,
            start_date=start,
            end_date=end,
            total_meetings=total_meetings,
            total_duration_seconds=total_duration,
            average_meeting_duration_seconds=avg_duration,
            unique_speakers=len(all_speakers),
            total_transcriptions=total_transcriptions,
            total_words_transcribed=total_words,
            overall_sentiment_score=overall_sentiment,
            sentiment_trend=sentiment_trend,
            sentiment_distribution=dict(sentiment_counts),
            total_suggestions_generated=total_suggestions,
            total_objections_handled=total_objections,
            total_questions_asked=total_questions,
            most_used_platform=most_platform,
            most_used_processing_mode=most_mode,
            most_active_day=most_active_day,
            most_active_hour=most_active_hour,
            languages_used=list(all_languages),
            most_common_language=most_common_lang,
            daily_breakdown=daily_breakdown,
            sentiment_timeline=sentiment_timeline,
            speaker_rankings=speaker_rankings,
        )

    async def get_speaker_analytics(
        self,
        speaker_id: str,
        time_range: TimeRange = TimeRange.ALL_TIME
    ) -> Optional[SpeakerAnalytics]:
        """Get analytics for a specific speaker."""
        if speaker_id not in self.speaker_data:
            return None

        speaker = self.speaker_data[speaker_id]
        sentiments = speaker["sentiments"]

        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0

        # Estimate words per minute (simplified)
        total_minutes = speaker["talk_time"] / 60 if speaker["talk_time"] > 0 else 1
        words_per_minute = 150.0  # Rough average

        # Emotional range (simplified)
        emotion_counts = Counter()
        for score in sentiments:
            emotion_counts[self._score_to_emotion(score)] += 1

        total_emotions = sum(emotion_counts.values())
        emotional_range = {
            emotion: count / total_emotions
            for emotion, count in emotion_counts.items()
        } if total_emotions > 0 else {}

        most_frequent = emotion_counts.most_common(1)[0][0] if emotion_counts else "neutral"

        return SpeakerAnalytics(
            speaker_id=speaker_id,
            speaker_name=f"Speaker {speaker_id}",  # Would fetch from database
            total_meetings=len(speaker["meetings"]),
            total_talk_time_seconds=speaker["talk_time"],
            average_sentiment_score=avg_sentiment,
            average_words_per_minute=words_per_minute,
            most_common_topics=[],  # Would require NLP analysis
            emotional_range=emotional_range,
            most_frequent_emotion=most_frequent,
            questions_asked=speaker["questions"],
            objections_raised=speaker["objections"],
            first_seen=speaker["first_seen"] or datetime.now(),
            last_seen=speaker["last_seen"] or datetime.now(),
        )

    async def export_analytics(
        self,
        export_request: ExportRequest
    ) -> ExportResult:
        """Export analytics data to file."""
        summary = await self.get_summary(
            export_request.time_range,
            export_request.start_date,
            export_request.end_date
        )

        export_id = str(uuid.uuid4())
        file_path = f"/tmp/analytics_{export_id}.{export_request.format}"

        # Export based on format
        if export_request.format == "json":
            data = self._summary_to_dict(summary)
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)

        elif export_request.format == "csv":
            # Simplified CSV export (daily breakdown)
            import csv
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Meetings", "Duration (min)", "Speakers", "Avg Sentiment"])
                for day in summary.daily_breakdown:
                    writer.writerow([
                        day.date.date(),
                        day.total_meetings,
                        day.total_duration_seconds // 60,
                        day.total_speakers,
                        f"{day.average_sentiment_score:.2f}"
                    ])

        # Get file size
        import os
        file_size = os.path.getsize(file_path)

        return ExportResult(
            export_id=export_id,
            format=export_request.format,
            file_path=file_path,
            file_size_bytes=file_size,
            rows_exported=len(summary.daily_breakdown),
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=7),
        )

    async def get_sentiment_timeline(
        self,
        time_range: TimeRange,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        granularity: str = "hour"
    ) -> List[dict]:
        """Get sentiment data over time for charting."""
        end = end_date or datetime.now()
        start = start_date or self._get_start_date(time_range, end)

        # Collect all sentiment trends in range
        all_trends = []
        for trends in self.sentiment_history.values():
            all_trends.extend([t for t in trends if start <= t.timestamp <= end])

        # Group by time bucket
        timeline = defaultdict(list)
        for trend in all_trends:
            bucket = self._get_time_bucket(trend.timestamp, granularity)
            timeline[bucket].append(trend.sentiment_score)

        # Calculate averages per bucket
        result = []
        for timestamp in sorted(timeline.keys()):
            scores = timeline[timestamp]
            result.append({
                "timestamp": timestamp.isoformat(),
                "average_score": sum(scores) / len(scores),
                "count": len(scores),
                "min_score": min(scores),
                "max_score": max(scores),
            })

        return result

    async def get_speaker_rankings(
        self,
        time_range: TimeRange,
        limit: int = 10
    ) -> List[SpeakerAnalytics]:
        """Get top speakers by talk time."""
        rankings = []
        for speaker_id in self.speaker_data.keys():
            analytics = await self.get_speaker_analytics(speaker_id, time_range)
            if analytics:
                rankings.append(analytics)

        # Sort by talk time
        rankings.sort(key=lambda s: s.total_talk_time_seconds, reverse=True)
        return rankings[:limit]

    # Helper methods

    def _calculate_average_sentiment(self, sentiments: List[dict]) -> float:
        """Calculate average sentiment score."""
        if not sentiments:
            return 0.0
        return sum(s["score"] for s in sentiments) / len(sentiments)

    def _sentiment_to_score(self, sentiment_type: str) -> float:
        """Convert sentiment type to numeric score (-1 to 1)."""
        mapping = {
            "very_positive": 1.0,
            "positive": 0.6,
            "excited": 0.8,
            "neutral": 0.0,
            "confused": -0.2,
            "concerned": -0.4,
            "negative": -0.6,
            "very_negative": -1.0,
        }
        return mapping.get(sentiment_type, 0.0)

    def _score_to_emotion(self, score: float) -> str:
        """Convert sentiment score to emotion."""
        if score >= 0.8:
            return "very_positive"
        elif score >= 0.4:
            return "positive"
        elif score >= -0.2:
            return "neutral"
        elif score >= -0.6:
            return "negative"
        else:
            return "very_negative"

    def _is_question(self, text: str) -> bool:
        """Simple question detection."""
        return text.strip().endswith("?")

    def _get_start_date(self, time_range: TimeRange, end_date: datetime) -> datetime:
        """Calculate start date from time range."""
        if time_range == TimeRange.LAST_HOUR:
            return end_date - timedelta(hours=1)
        elif time_range == TimeRange.LAST_DAY:
            return end_date - timedelta(days=1)
        elif time_range == TimeRange.LAST_WEEK:
            return end_date - timedelta(weeks=1)
        elif time_range == TimeRange.LAST_MONTH:
            return end_date - timedelta(days=30)
        elif time_range == TimeRange.LAST_YEAR:
            return end_date - timedelta(days=365)
        else:  # ALL_TIME
            return datetime.min

    def _determine_sentiment_trend(self, meetings: List[MeetingAnalytics]) -> str:
        """Determine if sentiment is improving, declining, or stable."""
        if len(meetings) < 2:
            return "stable"

        # Sort by time
        sorted_meetings = sorted(meetings, key=lambda m: m.start_time)

        # Compare first half vs second half
        mid = len(sorted_meetings) // 2
        first_half_avg = sum(m.average_sentiment_score for m in sorted_meetings[:mid]) / mid
        second_half_avg = sum(m.average_sentiment_score for m in sorted_meetings[mid:]) / (len(sorted_meetings) - mid)

        diff = second_half_avg - first_half_avg

        if diff > 0.1:
            return "improving"
        elif diff < -0.1:
            return "declining"
        else:
            return "stable"

    def _empty_summary(self, time_range: TimeRange, start: datetime, end: datetime) -> AnalyticsSummary:
        """Return empty analytics summary."""
        return AnalyticsSummary(
            time_range=time_range,
            start_date=start,
            end_date=end,
            total_meetings=0,
            total_duration_seconds=0,
            average_meeting_duration_seconds=0,
            unique_speakers=0,
            total_transcriptions=0,
            total_words_transcribed=0,
            overall_sentiment_score=0.0,
            sentiment_trend="stable",
            sentiment_distribution={},
            total_suggestions_generated=0,
            total_objections_handled=0,
            total_questions_asked=0,
            most_used_platform="unknown",
            most_used_processing_mode="local",
            most_active_day="",
            most_active_hour=0,
            languages_used=[],
            most_common_language="unknown",
        )

    def _get_time_bucket(self, timestamp: datetime, granularity: str) -> datetime:
        """Round timestamp to granularity bucket."""
        if granularity == "minute":
            return timestamp.replace(second=0, microsecond=0)
        elif granularity == "hour":
            return timestamp.replace(minute=0, second=0, microsecond=0)
        elif granularity == "day":
            return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            return timestamp

    def _summary_to_dict(self, summary: AnalyticsSummary) -> dict:
        """Convert analytics summary to dictionary for JSON export."""
        return {
            "time_range": summary.time_range.value,
            "start_date": summary.start_date.isoformat(),
            "end_date": summary.end_date.isoformat(),
            "total_meetings": summary.total_meetings,
            "total_duration_seconds": summary.total_duration_seconds,
            "average_meeting_duration_seconds": summary.average_meeting_duration_seconds,
            "unique_speakers": summary.unique_speakers,
            "total_transcriptions": summary.total_transcriptions,
            "overall_sentiment_score": summary.overall_sentiment_score,
            "sentiment_trend": summary.sentiment_trend,
            "sentiment_distribution": summary.sentiment_distribution,
            "most_used_platform": summary.most_used_platform,
            "most_active_day": summary.most_active_day,
            "daily_breakdown": [
                {
                    "date": day.date.isoformat(),
                    "meetings": day.total_meetings,
                    "duration_seconds": day.total_duration_seconds,
                    "speakers": day.total_speakers,
                    "sentiment": day.average_sentiment_score,
                }
                for day in summary.daily_breakdown
            ],
        }
