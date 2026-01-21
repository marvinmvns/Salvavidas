"""Configuration settings for the voice translation app."""
from enum import Enum
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class ProcessingMode(str, Enum):
    """Processing mode options."""
    LOCAL = "local"
    API_FAST = "api_fast"
    API_PREMIUM = "api_premium"


class LatencyPriority(str, Enum):
    """Latency priority options."""
    REALTIME = "realtime"
    BALANCED = "balanced"
    QUALITY = "quality"


class Settings(BaseSettings):
    """Application settings."""

    # Processing configuration
    processing_mode: ProcessingMode = Field(default=ProcessingMode.LOCAL)
    latency_priority: LatencyPriority = Field(default=LatencyPriority.REALTIME)

    # Language settings
    target_language: str = Field(default="en")
    source_language: Optional[str] = Field(default=None)

    # Feature flags
    enable_speaker_id: bool = Field(default=True)
    enable_suggestions: bool = Field(default=True)
    enable_streaming: bool = Field(default=True)

    # Audio settings
    sample_rate: int = Field(default=16000)
    chunk_size: int = Field(default=1024)
    channels: int = Field(default=1)
    stream_chunk_ms: int = Field(default=100)

    # API Keys - STT
    deepgram_api_key: Optional[str] = Field(default=None)
    assemblyai_api_key: Optional[str] = Field(default=None)
    google_cloud_credentials_path: Optional[str] = Field(default=None)
    azure_speech_key: Optional[str] = Field(default=None)
    azure_speech_region: Optional[str] = Field(default=None)

    # API Keys - Translation
    deepl_api_key: Optional[str] = Field(default=None)

    # API Keys - LLM
    openai_api_key: Optional[str] = Field(default=None)
    anthropic_api_key: Optional[str] = Field(default=None)

    # API Keys - TTS
    elevenlabs_api_key: Optional[str] = Field(default=None)
    aws_access_key_id: Optional[str] = Field(default=None)
    aws_secret_access_key: Optional[str] = Field(default=None)
    aws_region: Optional[str] = Field(default="us-east-1")

    # Local model paths
    whisper_model: str = Field(default="base")
    llama_model_path: str = Field(default="/app/data/models/llama-7b-chat.gguf")
    translation_model: str = Field(default="Helsinki-NLP/opus-mt-en-pt")

    # System settings
    use_intel_gpu: bool = Field(default=True)
    tz: str = Field(default="America/Sao_Paulo")
    log_level: str = Field(default="INFO")

    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields from .env or config DB


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
