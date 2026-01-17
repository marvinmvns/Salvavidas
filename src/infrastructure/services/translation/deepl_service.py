"""DeepL translation service implementation."""
from typing import Optional
from datetime import datetime
import deepl

from ....core.interfaces import ITranslationService
from ....core.entities import Translation


class DeepLTranslationService(ITranslationService):
    """DeepL API translation service."""

    def __init__(self, api_key: str):
        """Initialize DeepL client."""
        self.translator = deepl.Translator(api_key)

    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str
    ) -> Translation:
        """Translate text using DeepL."""
        try:
            # DeepL language codes (convert if needed)
            source_lang = self._convert_language_code(source_language)
            target_lang = self._convert_language_code(target_language)

            # Translate
            result = self.translator.translate_text(
                text,
                source_lang=source_lang if source_lang != "auto" else None,
                target_lang=target_lang
            )

            return Translation(
                original_text=text,
                translated_text=result.text,
                source_language=result.detected_source_lang.lower(),
                target_language=target_language,
                timestamp=datetime.now(),
                confidence=1.0,  # DeepL doesn't provide confidence
                service="deepl"
            )

        except Exception as e:
            raise RuntimeError(f"DeepL translation failed: {e}")

    def _convert_language_code(self, lang_code: str) -> str:
        """Convert language code to DeepL format."""
        # Map common codes to DeepL codes
        mapping = {
            "en": "EN-US",
            "pt": "PT-BR",
            "es": "ES",
            "fr": "FR",
            "de": "DE",
            "it": "IT",
            "ja": "JA",
            "zh": "ZH",
            "ru": "RU",
            "ko": "KO",
        }

        return mapping.get(lang_code.lower(), lang_code.upper())
