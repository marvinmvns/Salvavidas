"""Pyannote.audio embedding service for production speaker recognition."""
import numpy as np
import torch
from typing import List, Optional
from pathlib import Path
import io
import wave

try:
    from pyannote.audio import Inference
    from pyannote.audio.pipelines.speaker_verification import PretrainedSpeakerEmbedding
    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False


class PyannoteEmbeddingService:
    """
    Production-ready speaker embedding service using Pyannote.audio.

    Provides high-quality speaker embeddings for accurate speaker identification.
    Supports multiple models and GPU acceleration.
    """

    def __init__(
        self,
        model_name: str = "pyannote/embedding",
        token: Optional[str] = None,
        device: Optional[str] = None
    ):
        """
        Initialize Pyannote embedding service.

        Args:
            model_name: Hugging Face model name (default: pyannote/embedding)
            token: Hugging Face token for gated models
            device: Device to use ('cuda', 'cpu', or None for auto)
        """
        if not PYANNOTE_AVAILABLE:
            raise ImportError(
                "pyannote.audio is not installed. "
                "Install with: pip install pyannote.audio"
            )

        self.model_name = model_name
        self.token = token

        # Determine device
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        # Initialize model
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the speaker embedding model."""
        try:
            # Try using PretrainedSpeakerEmbedding (recommended)
            self.model = PretrainedSpeakerEmbedding(
                self.model_name,
                token=self.token,
                device=self.device
            )
            print(f"[Pyannote] Model loaded: {self.model_name} on {self.device}")

        except Exception as e:
            # Fallback to Inference
            print(f"[Pyannote] Fallback to Inference API: {e}")
            self.model = Inference(
                self.model_name,
                token=self.token,
                device=self.device
            )

    def generate_embedding(
        self,
        audio_samples: List[bytes],
        sample_rate: int = 16000
    ) -> np.ndarray:
        """
        Generate speaker embedding from audio samples.

        Args:
            audio_samples: List of audio byte arrays (PCM 16-bit)
            sample_rate: Audio sample rate (default: 16000 Hz)

        Returns:
            Speaker embedding as numpy array (typically 512-dimensional)
        """
        # Combine all audio samples
        combined_audio = b''.join(audio_samples)

        # Convert bytes to numpy array
        audio_array = np.frombuffer(combined_audio, dtype=np.int16)

        # Normalize to [-1, 1] float32
        audio_float = audio_array.astype(np.float32) / 32768.0

        # Convert to tensor
        audio_tensor = torch.from_numpy(audio_float).float()

        # Generate embedding
        with torch.no_grad():
            if isinstance(self.model, PretrainedSpeakerEmbedding):
                # PretrainedSpeakerEmbedding expects dictionary
                embedding = self.model({
                    'waveform': audio_tensor.unsqueeze(0),
                    'sample_rate': sample_rate
                })
            else:
                # Inference API expects tensor directly
                embedding = self.model({
                    'waveform': audio_tensor.unsqueeze(0),
                    'sample_rate': sample_rate
                })

        # Convert to numpy
        if isinstance(embedding, torch.Tensor):
            embedding_np = embedding.cpu().numpy()
        else:
            embedding_np = np.array(embedding)

        # Ensure 1D array
        if embedding_np.ndim > 1:
            embedding_np = embedding_np.squeeze()

        # Normalize (L2 normalization)
        norm = np.linalg.norm(embedding_np)
        if norm > 0:
            embedding_np = embedding_np / norm

        return embedding_np

    def calculate_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First speaker embedding
            embedding2: Second speaker embedding

        Returns:
            Similarity score between 0 and 1 (higher = more similar)
        """
        # Cosine similarity
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)

        # Convert to 0-1 range (cosine similarity is -1 to 1)
        similarity = (similarity + 1) / 2

        return float(similarity)

    def get_embedding_dimension(self) -> int:
        """Get the dimensionality of embeddings produced by this model."""
        # Most Pyannote models produce 512-dimensional embeddings
        # Some older models produce 256 or 128
        return 512  # Default for pyannote/embedding


class FallbackEmbeddingService:
    """
    Fallback embedding service when Pyannote is not available.

    Uses the original hash-based approach for demo/testing.
    """

    def __init__(self):
        """Initialize fallback service."""
        print("[Embedding] Using fallback hash-based embeddings (demo mode)")
        print("[Embedding] For production, install: pip install pyannote.audio")

    def generate_embedding(
        self,
        audio_samples: List[bytes],
        sample_rate: int = 16000
    ) -> np.ndarray:
        """Generate hash-based embedding (demo only)."""
        combined_audio = b''.join(audio_samples)

        # Generate 128-dimensional embedding
        embedding_size = 128
        embedding = np.zeros(embedding_size)

        # Simple hash-based features (just for demonstration)
        for i in range(embedding_size):
            chunk_size = len(combined_audio) // embedding_size
            start = i * chunk_size
            end = start + chunk_size

            if end <= len(combined_audio):
                chunk = combined_audio[start:end]
                hash_val = hash(chunk) % 1000000
                embedding[i] = hash_val / 1000000.0

        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    def calculate_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """Calculate cosine similarity."""
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)
        similarity = (similarity + 1) / 2

        return float(similarity)

    def get_embedding_dimension(self) -> int:
        """Get embedding dimension."""
        return 128


def create_embedding_service(
    model_name: str = "pyannote/embedding",
    token: Optional[str] = None,
    device: Optional[str] = None,
    fallback_on_error: bool = True
) -> 'PyannoteEmbeddingService | FallbackEmbeddingService':
    """
    Factory function to create the best available embedding service.

    Args:
        model_name: Pyannote model name
        token: Hugging Face token
        device: Device to use
        fallback_on_error: Use fallback if Pyannote fails

    Returns:
        PyannoteEmbeddingService or FallbackEmbeddingService
    """
    if not PYANNOTE_AVAILABLE:
        if fallback_on_error:
            return FallbackEmbeddingService()
        else:
            raise ImportError("pyannote.audio not available and fallback disabled")

    try:
        return PyannoteEmbeddingService(
            model_name=model_name,
            token=token,
            device=device
        )
    except Exception as e:
        print(f"[Embedding] Failed to initialize Pyannote: {e}")
        if fallback_on_error:
            return FallbackEmbeddingService()
        else:
            raise
