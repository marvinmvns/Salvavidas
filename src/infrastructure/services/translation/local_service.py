"""Local translation service using HuggingFace transformers."""
from typing import Optional, Dict
from datetime import datetime
from transformers import MarianMTModel, MarianTokenizer
import torch

from ....core.interfaces import ITranslationService
from ....core.entities import Translation


class LocalTranslationService(ITranslationService):
    """Local translation using Helsinki-NLP models."""

    def __init__(self):
        """Initialize translation service."""
        self.models: Dict[str, tuple] = {}  # Cache models
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str
    ) -> Translation:
        """Translate text using local model."""
        try:
            # Get or load model
            model, tokenizer = await self._get_model(source_language, target_language)

            # Tokenize
            inputs = tokenizer(text, return_tensors="pt", padding=True).to(self.device)

            # Translate
            with torch.no_grad():
                outputs = model.generate(**inputs, max_length=512)

            # Decode
            translated = tokenizer.decode(outputs[0], skip_special_tokens=True)

            return Translation(
                original_text=text,
                translated_text=translated,
                source_language=source_language,
                target_language=target_language,
                timestamp=datetime.now(),
                confidence=0.95,  # Approximate
                service="local-helsinki"
            )

        except Exception as e:
            raise RuntimeError(f"Local translation failed: {e}")

    async def _get_model(
        self,
        source_lang: str,
        target_lang: str
    ) -> tuple:
        """Get or load translation model."""
        key = f"{source_lang}-{target_lang}"

        if key not in self.models:
            # Load model
            model_name = f"Helsinki-NLP/opus-mt-{source_lang}-{target_lang}"

            try:
                tokenizer = MarianTokenizer.from_pretrained(model_name)
                model = MarianMTModel.from_pretrained(model_name).to(self.device)
                model.eval()

                self.models[key] = (model, tokenizer)
            except Exception:
                # Try reverse direction
                model_name = f"Helsinki-NLP/opus-mt-{target_lang}-{source_lang}"
                tokenizer = MarianTokenizer.from_pretrained(model_name)
                model = MarianMTModel.from_pretrained(model_name).to(self.device)
                model.eval()

                self.models[key] = (model, tokenizer)

        return self.models[key]
