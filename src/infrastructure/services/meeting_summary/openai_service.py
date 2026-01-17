"""OpenAI meeting summary service implementation."""
from typing import List
from datetime import datetime
import json

from ....core.interfaces import IMeetingSummaryService
from ....core.entities import MeetingSummary, SentimentAnalysis, SentimentType


class OpenAIMeetingSummaryService(IMeetingSummaryService):
    """OpenAI-powered meeting summary for comprehensive analysis."""

    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        """Initialize OpenAI meeting summary service."""
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=api_key)
            self.model = model
        except ImportError:
            raise RuntimeError("openai package not installed")

    async def generate_summary(
        self,
        meeting_id: str,
        conversation_history: List[str],
        sentiment_timeline: List[SentimentAnalysis]
    ) -> MeetingSummary:
        """Generate comprehensive meeting summary using GPT."""

        history_text = "\n".join([f"{i+1}. {msg}" for i, msg in enumerate(conversation_history)])

        prompt = f"""Analyze this meeting conversation and provide a comprehensive summary.

Conversation:
{history_text}

Provide:
1. List of key topics discussed (max 5)
2. Decisions made during the meeting
3. Action items extracted (who needs to do what)
4. Most discussed topics (top 3)
5. Overall summary (2-3 sentences)

Respond in JSON:
{{
    "key_topics": ["topic1", "topic2", ...],
    "decisions": ["decision1", ...],
    "action_items": ["action1", ...],
    "most_discussed": ["topic1", "topic2", "topic3"],
    "summary": "Overall meeting summary text"
}}"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert meeting analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )

            result_text = response.choices[0].message.content.strip()

            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()

            result = json.loads(result_text)

            # Calculate overall sentiment
            overall_sentiment = self._calculate_overall_sentiment(sentiment_timeline)

            return MeetingSummary(
                meeting_id=meeting_id,
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration_seconds=len(conversation_history) * 5,
                total_messages=len(conversation_history),
                speakers_count=2,
                key_topics=result.get("key_topics", []),
                decisions_made=result.get("decisions", []),
                action_items=result.get("action_items", []),
                overall_sentiment=overall_sentiment,
                sentiment_timeline=sentiment_timeline,
                most_discussed_topics=result.get("most_discussed", []),
                summary_text=result.get("summary", "")
            )

        except Exception as e:
            print(f"OpenAI summary error: {e}")
            # Fallback to basic summary
            return MeetingSummary(
                meeting_id=meeting_id,
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration_seconds=len(conversation_history) * 5,
                total_messages=len(conversation_history),
                speakers_count=2,
                key_topics=[],
                decisions_made=[],
                action_items=[],
                overall_sentiment=SentimentType.NEUTRAL,
                sentiment_timeline=sentiment_timeline,
                most_discussed_topics=[],
                summary_text=f"Meeting with {len(conversation_history)} messages."
            )

    async def extract_action_items(
        self,
        conversation_history: List[str]
    ) -> List[str]:
        """Extract action items using GPT."""
        history_text = "\n".join(conversation_history)

        prompt = f"""Extract all action items from this conversation.

Conversation:
{history_text}

List all tasks, to-dos, and commitments mentioned. Format as JSON array:
["action 1", "action 2", ...]"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You extract action items from conversations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=400
            )

            result_text = response.choices[0].message.content.strip()

            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()

            return json.loads(result_text)

        except Exception as e:
            print(f"OpenAI action items error: {e}")
            return []

    async def extract_key_topics(
        self,
        conversation_history: List[str]
    ) -> List[str]:
        """Extract key topics using GPT."""
        history_text = "\n".join(conversation_history)

        prompt = f"""Identify the key topics discussed in this conversation.

Conversation:
{history_text}

List the main topics as JSON array:
["topic1", "topic2", ...]"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You identify main topics in conversations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )

            result_text = response.choices[0].message.content.strip()

            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()

            return json.loads(result_text)

        except Exception as e:
            print(f"OpenAI topics error: {e}")
            return []

    def _calculate_overall_sentiment(
        self,
        sentiment_timeline: List[SentimentAnalysis]
    ) -> SentimentType:
        """Calculate overall sentiment."""
        if not sentiment_timeline:
            return SentimentType.NEUTRAL

        # Use most recent sentiment with highest confidence
        latest = max(sentiment_timeline, key=lambda x: x.confidence)
        return latest.sentiment
