"""ElevenLabs API TTS service - Ultra low latency."""
from typing import AsyncIterator, Optional
from datetime import datetime
from elevenlabs import ElevenLabs
from elevenlabs.client import AsyncElevenLabs
import asyncio

from ....core.interfaces import ITextToSpeechService
from ....core.entities import AudioChunk


class ElevenLabsTTSService(ITextToSpeechService):
    """ElevenLabs API TTS service for realtime synthesis."""

    def __init__(
        self,
        api_key: str,
        model: str = "eleven_turbo_v2",
        voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    ):
        """Initialize ElevenLabs client."""
        self.client = AsyncElevenLabs(api_key=api_key)
        self.model = model
        self.voice_id = voice_id

    async def synthesize(
        self,
        text: str,
        language: str,
        speaker_id: Optional[str] = None
    ) -> AudioChunk:
        """Synthesize text to speech using ElevenLabs."""
        try:
            # Generate audio
            audio_generator = await self.client.generate(
                text=text,
                voice=speaker_id or self.voice_id,
                model=self.model
            )

            # Collect all chunks
            audio_data = bytearray()
            async for chunk in audio_generator:
                audio_data.extend(chunk)

            return AudioChunk(
                data=bytes(audio_data),
                timestamp=datetime.now(),
                sample_rate=44100,
                channels=1,
                duration_ms=len(audio_data) / (44100 * 2) * 1000
            )

        except Exception as e:
            raise RuntimeError(f"ElevenLabs TTS failed: {e}")

    async def synthesize_stream(
        self,
        text: str,
        language: str,
        speaker_id: Optional[str] = None
    ) -> AsyncIterator[AudioChunk]:
        """Synthesize with true streaming."""
        try:
            audio_generator = await self.client.generate(
                text=text,
                voice=speaker_id or self.voice_id,
                model=self.model,
                stream=True
            )

            async for chunk in audio_generator:
                yield AudioChunk(
                    data=chunk,
                    timestamp=datetime.now(),
                    sample_rate=44100,
                    channels=1,
                    duration_ms=len(chunk) / (44100 * 2) * 1000
                )

        except Exception as e:
            raise RuntimeError(f"ElevenLabs streaming TTS failed: {e}")
