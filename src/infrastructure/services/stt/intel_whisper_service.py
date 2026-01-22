"""Intel Optimized Whisper STT Service using IPEX and Transformers."""
import torch
import numpy as np
from typing import AsyncIterator, Optional, List
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from ....core.interfaces import ISpeechToTextService
from ....core.entities import AudioChunk, TranscriptionSegment, Speaker

class IntelWhisperSTTService(ISpeechToTextService):
    """
    Whisper STT service optimized for Intel Hardware (GPU/CPU) using IPEX.
    Uses Hugging Face Transformers + Intel Extension for PyTorch.
    """

    def __init__(self, model_size: str = "base", device: str = "xpu"):
        """
        Initialize Intel Optimized Whisper.
        
        Args:
            model_size: Size of the model (base, small, medium, large-v3)
            device: 'xpu' for Intel GPU or 'cpu'
        """
        self.device = device
        self.model_id = f"openai/whisper-{model_size}"
        
        print(f"[IntelWhisper] Initializing {self.model_id} on {self.device}...")
        
        try:
            import intel_extension_for_pytorch as ipex
            self.ipex = ipex
        except ImportError:
            print("[IntelWhisper] IPEX not found! Falling back to standard PyTorch.")
            self.ipex = None
            self.device = "cpu"

        # Load Processor and Model
        try:
            self.processor = WhisperProcessor.from_pretrained(self.model_id)
            self.model = WhisperForConditionalGeneration.from_pretrained(self.model_id)
            
            # Move to device
            if self.device == "xpu":
                try:
                    self.model = self.model.to("xpu")
                    print("[IntelWhisper] Model moved to XPU (Intel GPU)")
                except Exception as e:
                    print(f"[IntelWhisper] Failed to move to XPU: {e}. using CPU.")
                    self.device = "cpu"
            
            # Optimize with IPEX
            if self.ipex:
                dtype = torch.float16 if self.device == "xpu" else torch.float32
                print(f"[IntelWhisper] Optimizing model with IPEX (dtype={dtype})...")
                self.model = self.ipex.optimize(self.model, dtype=dtype)
                
            self.model.eval()
            print("[IntelWhisper] Model initialized successfully.")
            
        except Exception as e:
            print(f"[IntelWhisper] Critical error initializing model: {e}")
            raise e

    async def transcribe(
        self,
        audio_chunk: AudioChunk,
        language: Optional[str] = None
    ) -> TranscriptionSegment:
        """Transcribe audio chunk."""
        # Prepare audio
        audio_array = np.frombuffer(audio_chunk.data, dtype=np.int16)
        audio_float = audio_array.astype(np.float32) / 32768.0
        
        # Determine language/task tokens
        forced_decoder_ids = None
        if language:
             forced_decoder_ids = self.processor.get_decoder_prompt_ids(language=language, task="transcribe")

        # Process input
        input_features = self.processor(
            audio_float, 
            sampling_rate=16000, 
            return_tensors="pt"
        ).input_features
        
        # Move inputs to device
        if self.device == "xpu":
            input_features = input_features.to("xpu")
            if hasattr(input_features, "half"): # if fp16
                 input_features = input_features.half()

        # Generate
        with torch.no_grad():
            # Use inference context if available for xpu
            if self.device == "xpu" and self.ipex:
                with torch.xpu.amp.autocast(enabled=True, dtype=torch.float16):
                    predicted_ids = self.model.generate(
                        input_features, 
                        forced_decoder_ids=forced_decoder_ids,
                        max_new_tokens=256
                    )
            else:
                 predicted_ids = self.model.generate(
                    input_features, 
                    forced_decoder_ids=forced_decoder_ids,
                    max_new_tokens=256
                )

        # Decode
        transcription_text = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
        
        # Return result
        # Note: Transformers doesn't return detailed timestamps/confidence easily like Faster-Whisper
        # Using placeholder values for now
        return TranscriptionSegment(
            text=transcription_text.strip(),
            speaker=Speaker(speaker_id="unknown"),
            language=language or "auto",
            timestamp=audio_chunk.timestamp,
            confidence=1.0, # Placeholder
            start_time=0.0,
            end_time=0.0
        )

    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[AudioChunk],
        language: Optional[str] = None
    ) -> AsyncIterator[TranscriptionSegment]:
        """Stream transcription (simple wrapper)."""
        buffer = bytearray()
        min_size = 32000 # 1s
        
        async for chunk in audio_stream:
            buffer.extend(chunk.data)
            if len(buffer) >= min_size:
                temp_chunk = AudioChunk(
                    data=bytes(buffer),
                    timestamp=chunk.timestamp,
                    sample_rate=chunk.sample_rate,
                    channels=chunk.channels,
                    duration_ms=0
                )
                segment = await self.transcribe(temp_chunk, language)
                if segment.text:
                    yield segment
                buffer = bytearray()
