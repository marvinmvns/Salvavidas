"""Piper local TTS service implementation."""
from typing import AsyncIterator, Optional
from datetime import datetime
import subprocess
import tempfile
import os

from ....core.interfaces import ITextToSpeechService
from ....core.entities import AudioChunk


class PiperTTSService(ITextToSpeechService):
    """Local Piper TTS service for fast synthesis."""

    def __init__(self, model_path: str = "en_US-lessac-medium"):
        """Initialize Piper TTS."""
        self.model_path = model_path

    async def synthesize(
        self,
        text: str,
        language: str,
        speaker_id: Optional[str] = None
    ) -> AudioChunk:
        """Synthesize text to speech using Piper."""
        # Create temporary file for output
        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False
        ) as tmp_file:
            output_path = tmp_file.name

        try:
            # Run piper
            cmd = [
                "piper",
                "--model", self.model_path,
                "--output_file", output_path
            ]

            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            stdout, stderr = process.communicate(input=text.encode())

            if process.returncode != 0:
                raise RuntimeError(f"Piper TTS failed: {stderr.decode()}")

            # Read audio data
            with open(output_path, "rb") as f:
                audio_data = f.read()

            return AudioChunk(
                data=audio_data,
                timestamp=datetime.now(),
                sample_rate=22050,
                channels=1,
                duration_ms=len(audio_data) / (22050 * 2) * 1000
            )

        finally:
            # Clean up
            if os.path.exists(output_path):
                os.remove(output_path)

    async def synthesize_stream(
        self,
        text: str,
        language: str,
        speaker_id: Optional[str] = None
    ) -> AsyncIterator[AudioChunk]:
        """Synthesize with streaming (not truly streaming for Piper)."""
        chunk = await self.synthesize(text, language, speaker_id)
        yield chunk
