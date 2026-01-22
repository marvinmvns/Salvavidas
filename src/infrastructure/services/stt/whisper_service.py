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
        """Initialize Whisper model (using faster-whisper)."""
        compute_type = "int8"
        
        # CTranslate2 usually supports 'cpu' and 'cuda'. 'xpu' might not be supported.
        if device not in ["cpu", "cuda", "auto"]:
            print(f"[WhisperSTT] Device '{device}' might not be supported by faster-whisper. Falling back to 'cpu'.")
            device = "cpu"
            
        if device == "cuda":
            compute_type = "float16"

        print(f"[WhisperSTT] Loading faster-whisper model '{model_size}' on {device} ({compute_type})...")
        try:
            self.model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type
            )
        except Exception as e:
            print(f"[WhisperSTT] Error loading on {device}: {e}. Falling back to CPU/int8.")
            self.model = WhisperModel(
                model_size,
                device="cpu",
                compute_type="int8"
            )
        
        self.model_size = model_size
        print(f"[WhisperSTT] Model loaded successfully.")

    async def transcribe(
        self,
        audio_chunk: AudioChunk,
        language: Optional[str] = None
    ) -> TranscriptionSegment:
        """Transcribe audio chunk using Whisper."""
        # Convert audio bytes to numpy array
        audio_array = np.frombuffer(audio_chunk.data, dtype=np.int16)
        audio_float = audio_array.astype(np.float32) / 32768.0

        # Transcribe - OPTIMIZED FOR SPEED with automatic language detection
        segments, info = self.model.transcribe(
            audio_float,
            language=language,  # None = auto-detect language
            beam_size=1,  # Fastest inference
            best_of=1,
            temperature=0.0,  # Greedy decoding (faster)
            condition_on_previous_text=False,  # Don't use context (faster)
            vad_filter=True,  # Voice Activity Detection
            vad_parameters=dict(
                min_silence_duration_ms=500,  # Reduced for faster response
                speech_pad_ms=200  # Less padding
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
        min_chunk_size = 96000  # 3 seconds of audio at 16kHz (16000 Hz * 2 bytes * 3s)
        print("DEBUG: STT stream started")

        async for audio_chunk in audio_stream:
            # print(f"DEBUG: Received chunk {len(audio_chunk.data)} bytes")
            if sample_rate is None:
                sample_rate = audio_chunk.sample_rate

            buffer.extend(audio_chunk.data)

            # Process when we have enough data (0.5s)
            if len(buffer) >= min_chunk_size:
                # Create temporary audio chunk
                temp_chunk = AudioChunk(
                    data=bytes(buffer),
                    timestamp=audio_chunk.timestamp,
                    sample_rate=sample_rate,
                    channels=audio_chunk.channels,
                    duration_ms=len(buffer) / (sample_rate * 2) * 1000
                )
                
                print(f"DEBUG: Transcribing buffer {len(buffer)} bytes")

                # Transcribe (force Portuguese)
                transcription = await self.transcribe(temp_chunk, language or "pt")

                if transcription.text:
                    print(f"DEBUG: Transcription result: {transcription.text}")
                    yield transcription
                else:
                    print("DEBUG: Transcription empty - VAD filter?")

                # Keep last 1 second for context
                overlap = 32000  # 1 second (16000 Hz * 2 bytes)
                buffer = buffer[-overlap:]
