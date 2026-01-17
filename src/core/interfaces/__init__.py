"""Core interfaces (ports)."""
from .services import (
    ISpeechToTextService,
    ITextToSpeechService,
    ISpeakerIdentificationService,
    ITranslationService,
    ILanguageModelService,
    ISentimentAnalysisService,
    IArgumentationEngineService,
    IMeetingSummaryService,
)

__all__ = [
    "ISpeechToTextService",
    "ITextToSpeechService",
    "ISpeakerIdentificationService",
    "ITranslationService",
    "ILanguageModelService",
    "ISentimentAnalysisService",
    "IArgumentationEngineService",
    "IMeetingSummaryService",
]
