"""Local sentiment analysis service implementation."""
from typing import List, Dict, Optional
from datetime import datetime
import re

from ....core.interfaces import ISentimentAnalysisService
from ....core.entities import SentimentAnalysis, SentimentType


class LocalSentimentAnalysisService(ISentimentAnalysisService):
    """Local sentiment analysis using pattern matching and heuristics."""

    def __init__(self):
        """Initialize local sentiment analyzer."""
        # Sentiment keyword dictionaries
        self.positive_words = {
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
            'love', 'perfect', 'awesome', 'brilliant', 'outstanding', 'yes',
            'agree', 'definitely', 'absolutely', 'sure', 'happy', 'glad',
            'excited', 'interested', 'impressed', 'satisfied'
        }

        self.negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'poor', 'disappointing',
            'hate', 'no', 'never', 'disagree', 'wrong', 'issue', 'problem',
            'concern', 'worried', 'expensive', 'costly', 'difficult', 'hard',
            'impossible', 'unfortunately', 'sadly', 'angry', 'frustrated'
        }

        self.concern_words = {
            'but', 'however', 'although', 'concerned', 'worry', 'unsure',
            'hesitant', 'doubt', 'uncertain', 'question', 'wondering'
        }

        self.excited_words = {
            'wow', 'incredible', 'unbelievable', 'cant wait', "can't wait",
            'amazing', 'fantastic', 'thrilled', 'enthusiastic'
        }

        self.confused_words = {
            'confused', 'unclear', 'dont understand', "don't understand",
            'what', 'how', 'explain', 'clarify', 'not sure'
        }

    async def analyze_sentiment(
        self,
        text: str,
        language: Optional[str] = None
    ) -> SentimentAnalysis:
        """Analyze sentiment using keyword matching and patterns."""
        text_lower = text.lower()
        words = set(re.findall(r'\b\w+\b', text_lower))

        # Count matches
        positive_count = len(words & self.positive_words)
        negative_count = len(words & self.negative_words)
        concern_count = len(words & self.concern_words)
        excited_count = len(words & self.excited_words)
        confused_count = len(words & self.confused_words)

        # Emotion scores
        total_matches = max(1, positive_count + negative_count + concern_count +
                           excited_count + confused_count)

        emotion_scores = {
            "happy": positive_count / total_matches,
            "sad": negative_count / total_matches,
            "concerned": concern_count / total_matches,
            "excited": excited_count / total_matches,
            "confused": confused_count / total_matches,
        }

        # Determine sentiment
        if excited_count > 0:
            sentiment = SentimentType.EXCITED
            confidence = min(0.9, excited_count / 5)
        elif confused_count > 0:
            sentiment = SentimentType.CONFUSED
            confidence = min(0.85, confused_count / 5)
        elif concern_count > 1:
            sentiment = SentimentType.CONCERNED
            confidence = min(0.8, concern_count / 5)
        elif positive_count > negative_count * 1.5:
            if positive_count > 3:
                sentiment = SentimentType.VERY_POSITIVE
            else:
                sentiment = SentimentType.POSITIVE
            confidence = min(0.9, positive_count / 5)
        elif negative_count > positive_count * 1.5:
            if negative_count > 3:
                sentiment = SentimentType.VERY_NEGATIVE
            else:
                sentiment = SentimentType.NEGATIVE
            confidence = min(0.9, negative_count / 5)
        else:
            sentiment = SentimentType.NEUTRAL
            confidence = 0.6

        # Check for punctuation-based sentiment
        if '!' in text:
            if sentiment in [SentimentType.POSITIVE, SentimentType.VERY_POSITIVE]:
                confidence = min(1.0, confidence + 0.1)
            elif sentiment in [SentimentType.NEGATIVE, SentimentType.VERY_NEGATIVE]:
                sentiment = SentimentType.VERY_NEGATIVE
                confidence = min(1.0, confidence + 0.15)

        if '?' in text and '??' in text:
            sentiment = SentimentType.CONFUSED
            confidence = min(0.9, confidence + 0.1)

        return SentimentAnalysis(
            sentiment=sentiment,
            confidence=confidence,
            emotion_scores=emotion_scores,
            text_analyzed=text,
            timestamp=datetime.now()
        )

    async def analyze_conversation_sentiment(
        self,
        conversation_history: List[str]
    ) -> List[SentimentAnalysis]:
        """Analyze sentiment for each message in conversation."""
        results = []
        for text in conversation_history:
            if text.strip():
                analysis = await self.analyze_sentiment(text)
                results.append(analysis)
        return results
