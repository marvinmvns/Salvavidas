"""Local translation service using M2M100."""
from typing import Optional, Dict
from datetime import datetime
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
import torch
import os

from ....core.interfaces import ITranslationService
from ....core.entities import Translation


class LocalTranslationService(ITranslationService):
    """Local translation service using M2M100 (runs on CPU/GPU)."""

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = None
        self.model = None

    async def translate(self, text: str, source_language: str, target_language: str) -> Translation:
        """Translate text using local M2M100 model."""
        if not text or not text.strip():
             return Translation(
                original_text=text,
                translated_text=text,
                source_language=source_language,
                target_language=target_language,
                timestamp=datetime.now(),
                confidence=1.0,
                service="empty"
            )

        # M2M100 uses codes like 'en', 'pt', 'es', etc.
        # Ensure 'auto' is handled
        if source_language == "auto":
            source_language = "en" # Fallback behavior
            
        # Same language optimization
        if source_language == target_language:
             return Translation(
                original_text=text,
                translated_text=text,
                source_language=source_language,
                target_language=target_language,
                timestamp=datetime.now(),
                confidence=1.0,
                service="identity"
            )

        try:
            model, tokenizer = await self._get_model()
            
            # Set source language
            tokenizer.src_lang = source_language
            
            encoded = tokenizer(text, return_tensors="pt").to(self.device)
            
            # Generate translation
            generated_tokens = model.generate(
                **encoded,
                forced_bos_token_id=tokenizer.get_lang_id(target_language)
            )
            
            translated_text = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]
            
            # Clean up any language tags that M2M100 sometimes adds (e.g., "__en__")
            import re
            translated_text = re.sub(r'^__\w+__\s*', '', translated_text).strip()
            
            return Translation(
                original_text=text,
                translated_text=translated_text,
                source_language=source_language,
                target_language=target_language,
                timestamp=datetime.now(),
                confidence=0.95,
                service="local-m2m100"
            )

        except Exception as e:
            print(f"Translation Error: {e}")
            raise RuntimeError(f"Local translation failed: {e}")

    async def _get_model(self):
        """Load the M2M100 model singleton."""
        if self.model is None:
            # Load model
            base_path = "/app/data/models/translation/m2m100_418M"
            
            # Use local path if exists, otherwise fallback to Hub name (enforce local_files_only=True)
            load_path = base_path if os.path.exists(base_path) else "facebook/m2m100_418M"

            try:
                self.tokenizer = M2M100Tokenizer.from_pretrained(load_path, local_files_only=True)
                self.model = M2M100ForConditionalGeneration.from_pretrained(load_path, local_files_only=True).to(self.device)
                self.model.eval()
            except Exception as e:
                # Better error for debugging
                if "sentencepiece" in str(e):
                    raise RuntimeError("Missing sentencepiece dependency. Rebuild container.")
                raise RuntimeError(f"Could not load local model M2M100. Ensure models are downloaded. Error: {e}")

        return self.model, self.tokenizer
