"""SpeechBrain embedding service implementation directly (no HF hub)."""
import os
import torch
import numpy as np
import torchaudio
from speechbrain.pretrained import SpeakerRecognition
from typing import List

class SpeechBrainEmbeddingService:
    """Speaker ID using SpeechBrain ECAPA-VoxCeleb."""

    def __init__(self, model_path: str = "/app/data/models/speechbrain", device: str = "cpu"):
        self.device = device
        
        # Load from local folder
        # 'source' can be a path. But we need to ensure it doesn't try to connect to HF.
        # SpeechBrain's `from_hparams` with `source` as a local path SHOULD work if files are present.
        print(f"[SpeechBrain] Loading model from {model_path}...")
        
        try:
            self.model = SpeakerRecognition.from_hparams(
                source=model_path,
                savedir=model_path,
                run_opts={"device": device}
            )
            print("[SpeechBrain] Model loaded successfully.")
        except Exception as e:
            print(f"[SpeechBrain] Error loading model: {e}")
            raise

    def generate_embedding(self, audio_samples: List[bytes], sample_rate: int = 16000) -> np.ndarray:
        """Generate embedding from audio byes."""
        try:
            # Join samples
            data = b"".join(audio_samples)
            
            # Convert to Tensor (normalized float32)
            # Input is 16-bit PCM
            audio_np = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            wavs = torch.from_numpy(audio_np).unsqueeze(0).to(self.device)
            
            # Create a dummy relative length tensor (all 1.0 since we have 1 batch)
            wav_lens = torch.tensor([1.0]).to(self.device)
            
            # Encode
            embedding = self.model.encode_batch(wavs, wav_lens)
            # embedding shape: [batch, 1, dim] -> [dim]
            return embedding.squeeze().cpu().numpy()
            
        except Exception as e:
            print(f"[SpeechBrain] Inference error: {e}")
            return np.zeros(192) # ECAPA-VoxCeleb is 192-dim

    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Cosine similarity."""
        # SpeechBrain embeddings are usually already normalized, but let's be safe
        score = torch.nn.functional.cosine_similarity(
            torch.tensor(embedding1).unsqueeze(0), 
            torch.tensor(embedding2).unsqueeze(0)
        )
        return float(score.item())

    def get_embedding_dimension(self) -> int:
        return 192
