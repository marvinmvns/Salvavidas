"""Core interfaces (ports)."""
from .services import (
    ISpeechToTextService,
    ITextToSpeechService,
    ISpeakerIdentificationService,
    ITranslationService,
    ILanguageModelService,
)

__all__ = [
    "ISpeechToTextService",
    "ITextToSpeechService",
    "ISpeakerIdentificationService",
    "ITranslationService",
    "ILanguageModelService",
]
