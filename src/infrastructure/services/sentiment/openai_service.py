"""OpenAI sentiment analysis service implementation."""
from typing import List, Optional
from datetime import datetime
import json
import hashlib
from functools import lru_cache

from ....core.interfaces import ISentimentAnalysisService
from ....core.entities import SentimentAnalysis, SentimentType


class OpenAISentimentAnalysisService(ISentimentAnalysisService):
    """OpenAI-powered sentiment analysis for high accuracy."""

    def __init__(self, api_key: str, model: str = "gpt-4", cache_size: int = 128):
        """Initialize OpenAI sentiment analyzer with LRU cache."""
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=api_key)
            self.model = model
            # Simple LRU cache for repeated texts
            self._cache: dict = {}
            self._cache_order: list = []
            self._cache_size = cache_size
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai")

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text hash."""
        return hashlib.md5(text.encode()).hexdigest()

    def _get_cached(self, key: str) -> Optional[SentimentAnalysis]:
        """Get from cache and update LRU order."""
        if key in self._cache:
            # Move to end (most recently used)
            self._cache_order.remove(key)
            self._cache_order.append(key)
            return self._cache[key]
        return None

    def _set_cached(self, key: str, value: SentimentAnalysis):
        """Set in cache with LRU eviction."""
        if key in self._cache:
            # Already exists, move to end
            self._cache_order.remove(key)
        elif len(self._cache) >= self._cache_size:
            # Evict oldest
            oldest = self._cache_order.pop(0)
            del self._cache[oldest]

        self._cache[key] = value
        self._cache_order.append(key)

    async def analyze_sentiment(
        self,
        text: str,
        language: Optional[str] = None
    ) -> SentimentAnalysis:
        """Analyze sentiment using OpenAI GPT with LRU cache."""
        # Check cache first
        cache_key = self._get_cache_key(text)
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        prompt = f"""Analyze the sentiment of the following text and provide:
1. Overall sentiment (very_positive, positive, neutral, negative, very_negative, confused, concerned, excited)
2. Confidence score (0.0 to 1.0)
3. Emotion scores for: happy, sad, concerned, excited, confused, angry (each 0.0 to 1.0)

Text: "{text}"

Respond in JSON format:
{{
    "sentiment": "...",
    "confidence": 0.0,
    "emotions": {{"happy": 0.0, "sad": 0.0, "concerned": 0.0, "excited": 0.0, "confused": 0.0, "angry": 0.0}}
}}"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a sentiment analysis expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )

            result_text = response.choices[0].message.content.strip()

            # Parse JSON response
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()

            result = json.loads(result_text)

            # Map to SentimentType
            sentiment_map = {
                "very_positive": SentimentType.VERY_POSITIVE,
                "positive": SentimentType.POSITIVE,
                "neutral": SentimentType.NEUTRAL,
                "negative": SentimentType.NEGATIVE,
                "very_negative": SentimentType.VERY_NEGATIVE,
                "confused": SentimentType.CONFUSED,
                "concerned": SentimentType.CONCERNED,
                "excited": SentimentType.EXCITED,
            }

            sentiment = sentiment_map.get(
                result.get("sentiment", "neutral").lower(),
                SentimentType.NEUTRAL
            )

            analysis = SentimentAnalysis(
                sentiment=sentiment,
                confidence=float(result.get("confidence", 0.8)),
                emotion_scores=result.get("emotions", {}),
                text_analyzed=text,
                timestamp=datetime.now()
            )

            # Cache the result
            self._set_cached(cache_key, analysis)
            return analysis

        except Exception as e:
            print(f"OpenAI sentiment analysis error: {e}")
            # Fallback to neutral
            return SentimentAnalysis(
                sentiment=SentimentType.NEUTRAL,
                confidence=0.5,
                emotion_scores={},
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
