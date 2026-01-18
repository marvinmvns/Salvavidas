"""Whisper local STT service implementation."""
import io
import wave
from typing import AsyncIterator, Optional
from datetime import datetime
from faster_whisper import WhisperModel
import numpy as np

from ....core.interfaces import ISpeechToTextService
from ....core.entities import AudioChunk, TranscriptionSegment, Speaker


class WhisperSTTService(ISpeechToTextService):
    """Local Whisper STT service for low-latency transcription."""

    def __init__(self, model_size: str = "large-v3", device: str = "cpu"):
        """Initialize Whisper model (using v3-turbo by default)."""
        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type="int8" if device == "cpu" else "float16"
        )
        self.model_size = model_size

    async def transcribe(
        self,
        audio_chunk: AudioChunk,
        language: Optional[str] = None
    ) -> TranscriptionSegment:
        """Transcribe audio chunk using Whisper."""
        # Convert audio bytes to numpy array
        audio_array = np.frombuffer(audio_chunk.data, dtype=np.int16)
        audio_float = audio_array.astype(np.float32) / 32768.0

        # Transcribe
        segments, info = self.model.transcribe(
            audio_float,
            language=language,
            beam_size=1,  # Faster inference
            best_of=1,
            vad_filter=True,  # Voice Activity Detection
            vad_parameters=dict(
                min_silence_duration_ms=500,
                speech_pad_ms=200
            )
        )

        # Get first segment (optimize: don't materialize entire list)
        first_segment = next(segments, None)
        if first_segment is None:
            return TranscriptionSegment(
                text="",
                speaker=Speaker(speaker_id="unknown"),
                language=info.language,
                timestamp=audio_chunk.timestamp,
                confidence=0.0,
                start_time=0.0,
                end_time=0.0
            )

        return TranscriptionSegment(
            text=first_segment.text.strip(),
            speaker=Speaker(speaker_id="unknown"),
            language=info.language,
            timestamp=audio_chunk.timestamp,
            confidence=first_segment.avg_logprob,
            start_time=first_segment.start,
            end_time=first_segment.end
        )

    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[AudioChunk],
        language: Optional[str] = None
    ) -> AsyncIterator[TranscriptionSegment]:
        """Transcribe audio stream in realtime."""
        buffer = bytearray()
        sample_rate = None
        min_chunk_size = 16000 * 2  # 1 second of audio at 16kHz

        async for audio_chunk in audio_stream:
            if sample_rate is None:
                sample_rate = audio_chunk.sample_rate

            buffer.extend(audio_chunk.data)

            # Process when we have enough data
            if len(buffer) >= min_chunk_size:
                # Create temporary audio chunk
                temp_chunk = AudioChunk(
                    data=bytes(buffer),
                    timestamp=audio_chunk.timestamp,
                    sample_rate=sample_rate,
                    channels=audio_chunk.channels,
                    duration_ms=len(buffer) / (sample_rate * 2) * 1000
                )

                # Transcribe
                transcription = await self.transcribe(temp_chunk, language)

                if transcription.text:
                    yield transcription

                # Keep last 0.5 seconds for context
                overlap = 16000  # 0.5 seconds
                buffer = buffer[-overlap:]
