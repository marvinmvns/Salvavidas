"""Local meeting summary service implementation."""
from typing import List
from datetime import datetime
from collections import Counter
import re

from ....core.interfaces import IMeetingSummaryService
from ....core.entities import MeetingSummary, SentimentAnalysis, SentimentType


class LocalMeetingSummaryService(IMeetingSummaryService):
    """Local meeting summary using text processing and heuristics."""

    def __init__(self):
        """Initialize local meeting summary service."""
        # Keywords for action items
        self.action_keywords = [
            'will', 'should', 'need to', 'must', 'have to', 'going to',
            'plan to', 'schedule', 'follow up', 'send', 'provide', 'create',
            'review', 'check', 'update', 'prepare', 'arrange', 'contact'
        ]

        # Stop words for topic extraction
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might',
            'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it',
            'we', 'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how'
        }

    async def generate_summary(
        self,
        meeting_id: str,
        conversation_history: List[str],
        sentiment_timeline: List[SentimentAnalysis]
    ) -> MeetingSummary:
        """Generate comprehensive meeting summary."""

        if not conversation_history:
            return MeetingSummary(
                meeting_id=meeting_id,
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration_seconds=0,
                total_messages=0,
                speakers_count=0,
                key_topics=[],
                decisions_made=[],
                action_items=[],
                overall_sentiment=SentimentType.NEUTRAL,
                sentiment_timeline=[],
                most_discussed_topics=[],
                summary_text="No conversation data available."
            )

        # Extract topics
        topics = await self.extract_key_topics(conversation_history)

        # Extract action items
        actions = await self.extract_action_items(conversation_history)

        # Extract decisions (sentences with decision keywords)
        decisions = self._extract_decisions(conversation_history)

        # Calculate overall sentiment
        overall_sentiment = self._calculate_overall_sentiment(sentiment_timeline)

        # Generate summary text
        summary_text = self._generate_summary_text(
            conversation_history,
            topics,
            actions,
            decisions
        )

        # Estimate duration (1 message ≈ 5 seconds)
        duration_seconds = len(conversation_history) * 5

        return MeetingSummary(
            meeting_id=meeting_id,
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration_seconds=duration_seconds,
            total_messages=len(conversation_history),
            speakers_count=2,  # Simplified estimate
            key_topics=topics[:5],
            decisions_made=decisions,
            action_items=actions,
            overall_sentiment=overall_sentiment,
            sentiment_timeline=sentiment_timeline,
            most_discussed_topics=topics[:3],
            summary_text=summary_text
        )

    async def extract_action_items(
        self,
        conversation_history: List[str]
    ) -> List[str]:
        """Extract action items from conversation."""
        action_items = []

        for text in conversation_history:
            text_lower = text.lower()

            # Check for action keywords
            for keyword in self.action_keywords:
                if keyword in text_lower:
                    # Extract sentence containing action
                    sentences = text.split('.')
                    for sentence in sentences:
                        if keyword in sentence.lower() and len(sentence.strip()) > 10:
                            action_items.append(sentence.strip())
                            break

        # Remove duplicates and limit
        return list(dict.fromkeys(action_items))[:10]

    async def extract_key_topics(
        self,
        conversation_history: List[str]
    ) -> List[str]:
        """Extract key topics discussed."""
        # Combine all text
        full_text = " ".join(conversation_history).lower()

        # Extract words
        words = re.findall(r'\b\w+\b', full_text)

        # Filter stop words and short words
        significant_words = [
            word for word in words
            if word not in self.stop_words and len(word) > 3
        ]

        # Count frequency
        word_freq = Counter(significant_words)

        # Get top words as topics
        top_words = [word for word, count in word_freq.most_common(10)]

        # Also extract noun phrases (simplified: capitalized words)
        noun_phrases = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', " ".join(conversation_history))

        # Combine and deduplicate
        all_topics = list(dict.fromkeys(top_words + noun_phrases))

        return all_topics[:10]

    def _extract_decisions(self, conversation_history: List[str]) -> List[str]:
        """Extract decisions made during conversation."""
        decisions = []
        decision_keywords = [
            'decided', 'agreed', 'confirm', 'finalize', 'approve',
            'accept', 'go ahead', "let's do", 'settled'
        ]

        for text in conversation_history:
            text_lower = text.lower()
            for keyword in decision_keywords:
                if keyword in text_lower:
                    # Extract the sentence
                    sentences = text.split('.')
                    for sentence in sentences:
                        if keyword in sentence.lower() and len(sentence.strip()) > 10:
                            decisions.append(sentence.strip())
                            break

        return list(dict.fromkeys(decisions))[:5]

    def _calculate_overall_sentiment(
        self,
        sentiment_timeline: List[SentimentAnalysis]
    ) -> SentimentType:
        """Calculate overall sentiment from timeline."""
        if not sentiment_timeline:
            return SentimentType.NEUTRAL

        # Weight recent sentiments more heavily
        total_score = 0
        total_weight = 0

        for i, analysis in enumerate(sentiment_timeline):
            weight = i + 1  # Later messages have more weight

            # Convert sentiment to score
            score_map = {
                SentimentType.VERY_POSITIVE: 2,
                SentimentType.POSITIVE: 1,
                SentimentType.EXCITED: 2,
                SentimentType.NEUTRAL: 0,
                SentimentType.CONCERNED: -0.5,
                SentimentType.CONFUSED: -0.5,
                SentimentType.NEGATIVE: -1,
                SentimentType.VERY_NEGATIVE: -2,
            }

            score = score_map.get(analysis.sentiment, 0)
            total_score += score * weight
            total_weight += weight

        avg_score = total_score / total_weight if total_weight > 0 else 0

        # Map back to sentiment
        if avg_score > 1.5:
            return SentimentType.VERY_POSITIVE
        elif avg_score > 0.5:
            return SentimentType.POSITIVE
        elif avg_score > -0.5:
            return SentimentType.NEUTRAL
        elif avg_score > -1.5:
            return SentimentType.NEGATIVE
        else:
            return SentimentType.VERY_NEGATIVE

    def _generate_summary_text(
        self,
        conversation_history: List[str],
        topics: List[str],
        actions: List[str],
        decisions: List[str]
    ) -> str:
        """Generate human-readable summary text."""
        parts = []

        # Overview
        parts.append(f"Meeting with {len(conversation_history)} exchanges.")

        # Topics
        if topics:
            topics_str = ", ".join(topics[:5])
            parts.append(f"Main topics discussed: {topics_str}.")

        # Decisions
        if decisions:
            parts.append(f"{len(decisions)} decision(s) made.")

        # Actions
        if actions:
            parts.append(f"{len(actions)} action item(s) identified.")

        return " ".join(parts)
