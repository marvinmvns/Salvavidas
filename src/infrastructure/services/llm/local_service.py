"""Local LLM service using llama.cpp."""
from typing import List, Optional
from llama_cpp import Llama
from langdetect import detect

from ....core.interfaces import ILanguageModelService
from ....core.entities import Translation, SuggestionResponse


class LocalLLMService(ILanguageModelService):
    """Local LLM service using llama.cpp with Intel GPU support."""

    def __init__(
        self,
        model_path: str,
        n_gpu_layers: int = 0,
        use_intel_gpu: bool = False
    ):
        """Initialize local LLM."""
        # Intel GPU optimization via oneAPI/SYCL
        if use_intel_gpu:
            n_gpu_layers = 35  # Offload layers to GPU

        self.llm = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=4,
            n_gpu_layers=n_gpu_layers,
            use_mlock=True,
            verbose=False
        )

    async def generate_suggestions(
        self,
        conversation_history: List[str],
        current_translation: Translation,
        target_language: str,
        num_suggestions: int = 3
    ) -> List[SuggestionResponse]:
        """Generate response suggestions."""
        try:
            # Build context
            context = "\n".join(conversation_history[-5:])

            # Create prompt
            prompt = f"""<s>[INST] Given this conversation:
{context}

The other person just said: "{current_translation.translated_text}"

Generate {num_suggestions} natural responses in {target_language}. Be concise.

Responses:
[/INST]"""

            # Generate
            output = self.llm(
                prompt,
                max_tokens=200,
                temperature=0.8,
                top_p=0.9,
                stop=["</s>", "\n\n"]
            )

            response_text = output["choices"][0]["text"].strip()

            # Parse suggestions (simple split)
            suggestions = []
            lines = [l.strip() for l in response_text.split("\n") if l.strip()]

            for i, line in enumerate(lines[:num_suggestions]):
                # Remove numbering if present
                text = line.lstrip("0123456789.-) ")

                suggestions.append(
                    SuggestionResponse(
                        text=text,
                        language=target_language,
                        confidence=0.7,
                        context=current_translation.translated_text,
                        alternatives=[]
                    )
                )

            return suggestions if suggestions else [
                SuggestionResponse(
                    text="Thank you!",
                    language=target_language,
                    confidence=0.5,
                    context="",
                    alternatives=[]
                )
            ]

        except Exception as e:
            # Fallback suggestions
            return [
                SuggestionResponse(
                    text="Thank you!",
                    language=target_language,
                    confidence=0.5,
                    context="",
                    alternatives=[]
                )
            ]

    async def detect_language(self, text: str) -> str:
        """Detect language using langdetect."""
        try:
            return detect(text)
        except Exception:
            return "en"
