"""Service factory for creating service instances based on configuration."""
from typing import Optional
from config.settings import Settings, ProcessingMode
from .services.stt import WhisperSTTService, DeepgramSTTService
from .services.tts import PiperTTSService, ElevenLabsTTSService
from .services.speaker_management import SpeakerManagementService
from .services.translation import LocalTranslationService, DeepLTranslationService
from .services.llm import LocalLLMService, OpenAILLMService, _HAS_LOCAL_LLM
from ..core.interfaces import (
    ISpeechToTextService,
    ITextToSpeechService,
    ISpeakerManagementService,
    ITranslationService,
    ILanguageModelService,
)


class ServiceFactory:
    """Factory for creating service instances."""

    def __init__(self, settings: Settings, use_intel_gpu: bool = False):
        """Initialize service factory."""
        self.settings = settings
        self.use_intel_gpu = use_intel_gpu

    def create_stt_service(self) -> ISpeechToTextService:
        """Create STT service based on configuration."""
        mode = self.settings.processing_mode

        if mode == ProcessingMode.LOCAL:
            # Use Intel GPU acceleration if available
            if self.use_intel_gpu:
                try:
                    from .services.stt.intel_whisper_service import IntelWhisperSTTService
                    return IntelWhisperSTTService(
                        model_size=self.settings.whisper_model,
                        device="xpu"
                    )
                except Exception as e:
                    print(f"[ServiceFactory] Failed to initialize Intel Whisper: {e}. Falling back to standard Whisper.")
                    # Fallback to standard
            
            # Standard Faster-Whisper (CPU optimized)
            return WhisperSTTService(
                model_size=self.settings.whisper_model,
                device="cpu"
            )

        elif mode in [ProcessingMode.API_FAST, ProcessingMode.API_PREMIUM]:
            if not self.settings.deepgram_api_key:
                raise ValueError("Deepgram API key required for API mode")

            model = "nova-2" if mode == ProcessingMode.API_PREMIUM else "nova"
            return DeepgramSTTService(
                api_key=self.settings.deepgram_api_key,
                model=model
            )

        raise ValueError(f"Unknown processing mode: {mode}")

    def create_tts_service(self) -> ITextToSpeechService:
        """Create TTS service based on configuration."""
        mode = self.settings.processing_mode

        if mode == ProcessingMode.LOCAL:
            return PiperTTSService()

        elif mode in [ProcessingMode.API_FAST, ProcessingMode.API_PREMIUM]:
            if not self.settings.elevenlabs_api_key:
                raise ValueError("ElevenLabs API key required for API mode")

            model = "eleven_turbo_v2" if mode == ProcessingMode.API_PREMIUM else "eleven_monolingual_v1"
            return ElevenLabsTTSService(
                api_key=self.settings.elevenlabs_api_key,
                model=model
            )

        raise ValueError(f"Unknown processing mode: {mode}")

    def create_speaker_id_service(self) -> ISpeakerManagementService:
        """Create Speaker ID service (using modern SpeakerManagementService)."""
        # Use SpeechBrain-based speaker management with proper embeddings + Intel GPU
        return SpeakerManagementService(use_intel_gpu=self.use_intel_gpu)

    def create_translation_service(self) -> ITranslationService:
        """Create Translation service based on configuration."""
        mode = self.settings.processing_mode

        if mode == ProcessingMode.LOCAL:
            return LocalTranslationService()

        elif mode in [ProcessingMode.API_FAST, ProcessingMode.API_PREMIUM]:
            if not self.settings.deepl_api_key:
                # Fallback to local if no API key
                return LocalTranslationService()

            return DeepLTranslationService(
                api_key=self.settings.deepl_api_key
            )

        raise ValueError(f"Unknown processing mode: {mode}")

    def create_llm_service(self) -> Optional[ILanguageModelService]:
        """Create LLM service based on configuration."""
        mode = self.settings.processing_mode

        if mode == ProcessingMode.LOCAL:
            if not _HAS_LOCAL_LLM:
                import warnings
                warnings.warn("Local LLM service unavailable (llama-cpp-python not installed). LLM features disabled.")
                return None
            return LocalLLMService(
                model_path=self.settings.llama_model_path,
                use_intel_gpu=self.use_intel_gpu
            )

        elif mode in [ProcessingMode.API_FAST, ProcessingMode.API_PREMIUM]:
            if not self.settings.openai_api_key:
                # Fallback to local if available
                if _HAS_LOCAL_LLM:
                    return LocalLLMService(
                        model_path=self.settings.llama_model_path,
                        use_intel_gpu=self.use_intel_gpu
                    )
                return None

            model = "gpt-4-turbo-preview" if mode == ProcessingMode.API_PREMIUM else "gpt-3.5-turbo"
            return OpenAILLMService(
                api_key=self.settings.openai_api_key,
                model=model
            )

        raise ValueError(f"Unknown processing mode: {mode}")
