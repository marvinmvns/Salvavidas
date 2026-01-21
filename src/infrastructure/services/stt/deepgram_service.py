"""Deepgram API STT service implementation - Ultra low latency."""
from typing import AsyncIterator, Optional
from datetime import datetime
import asyncio
import warnings

try:
    from deepgram import DeepgramClient
    DEEPGRAM_AVAILABLE = True
except ImportError:
    DEEPGRAM_AVAILABLE = False
    warnings.warn("Deepgram SDK not found. Deepgram services will be disabled.")

from ....core.interfaces import ISpeechToTextService
from ....core.entities import AudioChunk, TranscriptionSegment, Speaker


class DeepgramSTTService(ISpeechToTextService):
    """Deepgram API STT service for realtime transcription."""

    def __init__(self, api_key: str, model: str = "nova-2"):
        """Initialize Deepgram client."""
        if not DEEPGRAM_AVAILABLE:
            raise RuntimeError("Deepgram SDK is not available")
            
        self.client = DeepgramClient(api_key)
        self.model = model

    async def transcribe(
        self,
        audio_chunk: AudioChunk,
        language: Optional[str] = None
    ) -> TranscriptionSegment:
        """Transcribe audio chunk using Deepgram."""
        options = {
            "model": self.model,
            "language": language or "en",
            "smart_format": True,
            "punctuate": True,
            "diarize": True,
            "utterances": True,
        }

        try:
            response = await asyncio.to_thread(
                self.client.listen.rest.v("1").transcribe_file,
                {"buffer": audio_chunk.data},
                options
            )

            results = response.results
            if not results or not results.channels:
                return TranscriptionSegment(
                    text="",
                    speaker=Speaker(speaker_id="unknown"),
                    language=language or "en",
                    timestamp=audio_chunk.timestamp,
                    confidence=0.0,
                    start_time=0.0,
                    end_time=0.0
                )

            # Get first alternative
            channel = results.channels[0]
            alternative = channel.alternatives[0]

            # Get speaker info if available
            speaker_id = "speaker_0"
            if alternative.words and len(alternative.words) > 0:
                speaker_id = f"speaker_{getattr(alternative.words[0], 'speaker', 0) or 0}"

            return TranscriptionSegment(
                text=alternative.transcript,
                speaker=Speaker(speaker_id=speaker_id),
                language=getattr(channel, 'detected_language', None) or language or "en",
                timestamp=audio_chunk.timestamp,
                confidence=alternative.confidence,
                start_time=alternative.words[0].start if alternative.words else 0.0,
                end_time=alternative.words[-1].end if alternative.words else 0.0
            )

        except Exception as e:
            raise RuntimeError(f"Deepgram transcription failed: {e}")

    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[AudioChunk],
        language: Optional[str] = None
    ) -> AsyncIterator[TranscriptionSegment]:
        """Transcribe audio stream using Deepgram Live API."""
        options = {
            "model": self.model,
            "language": language or "en",
            "smart_format": True,
            "punctuate": True,
            "interim_results": False,
            "utterance_end_ms": 1000,
            "vad_events": True,
        }

        connection = self.client.listen.live.v("1")
        transcription_queue = asyncio.Queue()

        # Setup event handlers
        def on_message(self, result, **kwargs):
            if result.is_final:
                transcript = result.channel.alternatives[0].transcript
                if transcript.strip():
                    transcription_queue.put_nowait({
                        "text": transcript,
                        "confidence": result.channel.alternatives[0].confidence,
                        "timestamp": datetime.now()
                    })

        def on_error(self, error, **kwargs):
            print(f"Deepgram error: {error}")

        connection.on("transcript_received", on_message)
        connection.on("error", on_error)

        # Start connection
        if not await connection.start(options):
            raise RuntimeError("Failed to start Deepgram connection")

        # Stream audio and yield transcriptions
        async def stream_audio():
            async for audio_chunk in audio_stream:
                connection.send(audio_chunk.data)

        # Start streaming task
        stream_task = asyncio.create_task(stream_audio())

        try:
            while True:
                try:
                    result = await asyncio.wait_for(
                        transcription_queue.get(),
                        timeout=5.0
                    )

                    yield TranscriptionSegment(
                        text=result["text"],
                        speaker=Speaker(speaker_id="speaker_0"),
                        language=language or "en",
                        timestamp=result["timestamp"],
                        confidence=result["confidence"],
                        start_time=0.0,
                        end_time=0.0
                    )

                except asyncio.TimeoutError:
                    if stream_task.done():
                        break

        finally:
            await connection.finish()
            stream_task.cancel()
