"""Pyannote local speaker identification service."""
from typing import List, Optional
import io
import wave
import hashlib
from datetime import datetime
from pyannote.audio import Inference
import numpy as np

from ....core.interfaces import ISpeakerIdentificationService
from ....core.entities import AudioChunk, Speaker


class PyannoteSpeak erIdentificationService(ISpeakerIdentificationService):
    """Local speaker identification using pyannote.audio."""

    def __init__(self, model_name: str = "pyannote/embedding"):
        """Initialize pyannote speaker embedding model."""
        self.inference = Inference(model_name, device="cpu")
        self.threshold = 0.6  # Similarity threshold

    async def identify_speaker(
        self,
        audio_chunk: AudioChunk,
        known_speakers: List[Speaker]
    ) -> Speaker:
        """Identify speaker from audio chunk."""
        # Get embedding for the audio
        embedding = await self._get_embedding(audio_chunk)

        if not known_speakers:
            # No known speakers, create new one
            speaker_id = self._generate_speaker_id(embedding)
            return Speaker(
                speaker_id=speaker_id,
                confidence=1.0,
                embedding=embedding.tobytes()
            )

        # Compare with known speakers
        best_match = None
        best_similarity = 0.0

        for speaker in known_speakers:
            if speaker.embedding:
                known_embedding = np.frombuffer(speaker.embedding, dtype=np.float32)
                similarity = self._cosine_similarity(embedding, known_embedding)

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = speaker

        # If similarity is above threshold, return matched speaker
        if best_match and best_similarity >= self.threshold:
            return Speaker(
                speaker_id=best_match.speaker_id,
                name=best_match.name,
                language=best_match.language,
                confidence=best_similarity,
                embedding=best_match.embedding
            )

        # Otherwise, create new speaker
        speaker_id = self._generate_speaker_id(embedding)
        return Speaker(
            speaker_id=speaker_id,
            confidence=1.0 - best_similarity,  # Confidence it's a new speaker
            embedding=embedding.tobytes()
        )

    async def enroll_speaker(
        self,
        audio_chunks: List[AudioChunk],
        speaker_name: Optional[str] = None
    ) -> Speaker:
        """Enroll a new speaker."""
        # Combine audio chunks
        combined_audio = bytearray()
        sample_rate = audio_chunks[0].sample_rate

        for chunk in audio_chunks:
            combined_audio.extend(chunk.data)

        combined_chunk = AudioChunk(
            data=bytes(combined_audio),
            timestamp=datetime.now(),
            sample_rate=sample_rate,
            channels=audio_chunks[0].channels,
            duration_ms=len(combined_audio) / (sample_rate * 2) * 1000
        )

        # Get embedding
        embedding = await self._get_embedding(combined_chunk)

        # Generate speaker ID
        speaker_id = self._generate_speaker_id(embedding)

        return Speaker(
            speaker_id=speaker_id,
            name=speaker_name,
            confidence=1.0,
            embedding=embedding.tobytes()
        )

    async def _get_embedding(self, audio_chunk: AudioChunk) -> np.ndarray:
        """Extract speaker embedding from audio."""
        # Convert bytes to numpy array
        audio_array = np.frombuffer(audio_chunk.data, dtype=np.int16)
        audio_float = audio_array.astype(np.float32) / 32768.0

        # Get embedding
        embedding = self.inference(
            {"waveform": audio_float.reshape(1, -1), "sample_rate": audio_chunk.sample_rate}
        )

        return embedding

    def _cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Calculate cosine similarity between embeddings."""
        return float(np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2)))

    def _generate_speaker_id(self, embedding: np.ndarray) -> str:
        """Generate unique speaker ID from embedding."""
        hash_obj = hashlib.sha256(embedding.tobytes())
        return f"speaker_{hash_obj.hexdigest()[:8]}"
