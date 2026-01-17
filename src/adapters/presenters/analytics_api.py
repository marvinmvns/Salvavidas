"""
Analytics API endpoints using FastAPI.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from ...core.interfaces.services import IAnalyticsService
from ...core.entities.analytics import TimeRange, ExportRequest


# Request/Response models
class MeetingStartRequest(BaseModel):
    """Request to start tracking a meeting."""
    meeting_id: str
    meeting_type: str = "other"  # "sales", "support", "internal", "other"
    platform: str = "web"  # "meet", "zoom", "teams", "desktop", "web"
    processing_mode: str = "local"  # "local", "fast", "premium"


class MeetingEndRequest(BaseModel):
    """Request to end meeting tracking."""
    meeting_id: str


class ExportRequestModel(BaseModel):
    """Request to export analytics."""
    format: str = "json"  # "csv", "json", "pdf", "excel"
    time_range: TimeRange = TimeRange.LAST_WEEK
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_detailed_transcripts: bool = False
    include_speaker_breakdown: bool = True
    include_sentiment_analysis: bool = True
    include_charts: bool = False


def create_analytics_router(analytics_service: IAnalyticsService) -> APIRouter:
    """
    Create FastAPI router for analytics endpoints.

    Args:
        analytics_service: Analytics service instance

    Returns:
        Configured APIRouter
    """
    router = APIRouter(prefix="/api/analytics", tags=["analytics"])

    @router.post("/meetings/start")
    async def start_meeting(request: MeetingStartRequest):
        """Start tracking a new meeting."""
        try:
            await analytics_service.record_meeting_start(
                meeting_id=request.meeting_id,
                meeting_type=request.meeting_type,
                platform=request.platform,
                processing_mode=request.processing_mode
            )
            return {"status": "success", "meeting_id": request.meeting_id}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/meetings/end")
    async def end_meeting(request: MeetingEndRequest):
        """End meeting tracking and get analytics."""
        try:
            analytics = await analytics_service.record_meeting_end(request.meeting_id)
            return {
                "status": "success",
                "analytics": {
                    "meeting_id": analytics.meeting_id,
                    "duration_seconds": analytics.duration_seconds,
                    "total_speakers": analytics.total_speakers,
                    "total_transcriptions": analytics.total_transcriptions,
                    "average_sentiment_score": analytics.average_sentiment_score,
                    "sentiment_distribution": analytics.sentiment_distribution,
                    "most_active_speaker": analytics.most_active_speaker,
                    "questions_asked": analytics.questions_asked,
                    "objections_raised": analytics.objections_raised,
                    "positive_moments": analytics.positive_moments,
                    "negative_moments": analytics.negative_moments,
                }
            }
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/meetings/{meeting_id}")
    async def get_meeting_analytics(meeting_id: str):
        """Get analytics for a specific meeting."""
        try:
            analytics = await analytics_service.get_meeting_analytics(meeting_id)
            if not analytics:
                raise HTTPException(status_code=404, detail="Meeting not found")

            return {
                "meeting_id": analytics.meeting_id,
                "start_time": analytics.start_time.isoformat(),
                "end_time": analytics.end_time.isoformat() if analytics.end_time else None,
                "duration_seconds": analytics.duration_seconds,
                "total_speakers": analytics.total_speakers,
                "total_transcriptions": analytics.total_transcriptions,
                "total_translations": analytics.total_translations,
                "total_suggestions": analytics.total_suggestions,
                "average_sentiment_score": analytics.average_sentiment_score,
                "sentiment_distribution": analytics.sentiment_distribution,
                "speaker_talk_time": analytics.speaker_talk_time,
                "most_active_speaker": analytics.most_active_speaker,
                "languages_detected": analytics.languages_detected,
                "primary_language": analytics.primary_language,
                "questions_asked": analytics.questions_asked,
                "objections_raised": analytics.objections_raised,
                "positive_moments": analytics.positive_moments,
                "negative_moments": analytics.negative_moments,
                "meeting_type": analytics.meeting_type,
                "meeting_platform": analytics.meeting_platform,
                "processing_mode": analytics.processing_mode,
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/summary")
    async def get_summary(
        time_range: TimeRange = Query(TimeRange.LAST_WEEK),
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ):
        """Get analytics summary for a time range."""
        try:
            summary = await analytics_service.get_summary(time_range, start_date, end_date)

            return {
                "time_range": summary.time_range.value,
                "start_date": summary.start_date.isoformat(),
                "end_date": summary.end_date.isoformat(),
                "total_meetings": summary.total_meetings,
                "total_duration_seconds": summary.total_duration_seconds,
                "average_meeting_duration_seconds": summary.average_meeting_duration_seconds,
                "unique_speakers": summary.unique_speakers,
                "total_transcriptions": summary.total_transcriptions,
                "total_words_transcribed": summary.total_words_transcribed,
                "overall_sentiment_score": summary.overall_sentiment_score,
                "sentiment_trend": summary.sentiment_trend,
                "sentiment_distribution": summary.sentiment_distribution,
                "total_suggestions_generated": summary.total_suggestions_generated,
                "total_objections_handled": summary.total_objections_handled,
                "total_questions_asked": summary.total_questions_asked,
                "most_used_platform": summary.most_used_platform,
                "most_used_processing_mode": summary.most_used_processing_mode,
                "most_active_day": summary.most_active_day,
                "most_active_hour": summary.most_active_hour,
                "languages_used": summary.languages_used,
                "most_common_language": summary.most_common_language,
                "daily_breakdown": [
                    {
                        "date": day.date.isoformat(),
                        "total_meetings": day.total_meetings,
                        "total_duration_seconds": day.total_duration_seconds,
                        "total_speakers": day.total_speakers,
                        "total_transcriptions": day.total_transcriptions,
                        "average_sentiment_score": day.average_sentiment_score,
                        "peak_hour": day.peak_hour,
                        "peak_hour_meetings": day.peak_hour_meetings,
                        "platform_usage": day.platform_usage,
                        "processing_mode_usage": day.processing_mode_usage,
                    }
                    for day in summary.daily_breakdown
                ],
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/sentiment/timeline")
    async def get_sentiment_timeline(
        time_range: TimeRange = Query(TimeRange.LAST_WEEK),
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        granularity: str = Query("hour", regex="^(minute|hour|day)$")
    ):
        """Get sentiment data over time for charting."""
        try:
            timeline = await analytics_service.get_sentiment_timeline(
                time_range, start_date, end_date, granularity
            )
            return {"timeline": timeline}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/speakers/rankings")
    async def get_speaker_rankings(
        time_range: TimeRange = Query(TimeRange.LAST_WEEK),
        limit: int = Query(10, ge=1, le=100)
    ):
        """Get top speakers by talk time."""
        try:
            rankings = await analytics_service.get_speaker_rankings(time_range, limit)

            return {
                "rankings": [
                    {
                        "speaker_id": speaker.speaker_id,
                        "speaker_name": speaker.speaker_name,
                        "total_meetings": speaker.total_meetings,
                        "total_talk_time_seconds": speaker.total_talk_time_seconds,
                        "average_sentiment_score": speaker.average_sentiment_score,
                        "average_words_per_minute": speaker.average_words_per_minute,
                        "most_frequent_emotion": speaker.most_frequent_emotion,
                        "questions_asked": speaker.questions_asked,
                        "objections_raised": speaker.objections_raised,
                    }
                    for speaker in rankings
                ]
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/speakers/{speaker_id}")
    async def get_speaker_analytics(
        speaker_id: str,
        time_range: TimeRange = Query(TimeRange.ALL_TIME)
    ):
        """Get detailed analytics for a specific speaker."""
        try:
            analytics = await analytics_service.get_speaker_analytics(speaker_id, time_range)
            if not analytics:
                raise HTTPException(status_code=404, detail="Speaker not found")

            return {
                "speaker_id": analytics.speaker_id,
                "speaker_name": analytics.speaker_name,
                "total_meetings": analytics.total_meetings,
                "total_talk_time_seconds": analytics.total_talk_time_seconds,
                "average_sentiment_score": analytics.average_sentiment_score,
                "average_words_per_minute": analytics.average_words_per_minute,
                "most_common_topics": analytics.most_common_topics,
                "emotional_range": analytics.emotional_range,
                "most_frequent_emotion": analytics.most_frequent_emotion,
                "questions_asked": analytics.questions_asked,
                "objections_raised": analytics.objections_raised,
                "first_seen": analytics.first_seen.isoformat(),
                "last_seen": analytics.last_seen.isoformat(),
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/export")
    async def export_analytics(request: ExportRequestModel):
        """Export analytics data to file."""
        try:
            export_req = ExportRequest(
                format=request.format,
                time_range=request.time_range,
                start_date=request.start_date,
                end_date=request.end_date,
                include_detailed_transcripts=request.include_detailed_transcripts,
                include_speaker_breakdown=request.include_speaker_breakdown,
                include_sentiment_analysis=request.include_sentiment_analysis,
                include_charts=request.include_charts,
            )

            result = await analytics_service.export_analytics(export_req)

            return {
                "export_id": result.export_id,
                "format": result.format,
                "file_path": result.file_path,
                "file_size_bytes": result.file_size_bytes,
                "rows_exported": result.rows_exported,
                "created_at": result.created_at.isoformat(),
                "expires_at": result.expires_at.isoformat() if result.expires_at else None,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "analytics"}

    return router
