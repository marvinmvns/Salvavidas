"""Core interfaces (ports)."""
from .services import (
    ISpeechToTextService,
    ITextToSpeechService,
    ISpeakerIdentificationService,
    ISpeakerManagementService,
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
    "ISpeakerManagementService",
    "ITranslationService",
    "ILanguageModelService",
    "ISentimentAnalysisService",
    "IArgumentationEngineService",
    "IMeetingSummaryService",
]
