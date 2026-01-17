"""Translation service implementations."""
from .deepl_service import DeepLTranslationService
from .local_service import LocalTranslationService

__all__ = ["DeepLTranslationService", "LocalTranslationService"]
