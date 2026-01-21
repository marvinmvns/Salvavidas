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

            # Create prompt for better suggestions
            prompt = f"""<s>[INST] You are a helpful assistant. The other person said: "{current_translation.translated_text}"

Generate exactly {num_suggestions} short, natural response options in {target_language} language.
Format: One response per line, numbered.

Example:
1. First response
2. Second response
3. Third response
[/INST]

Sure! Here are {num_suggestions} natural responses in {target_language}:

"""

            # Generate
            output = self.llm(
                prompt,
                max_tokens=300,
                temperature=0.7,
                top_p=0.95,
                stop=["</s>", "[INST]"]
            )

            response_text = output["choices"][0]["text"].strip()
            print(f"[LLM] Raw response: {response_text}")

            # Parse suggestions (simple split)
            suggestions = []
            lines = [l.strip() for l in response_text.split("\n") if l.strip()]
            print(f"[LLM] Parsed {len(lines)} lines from response")

            for i, line in enumerate(lines[:num_suggestions]):
                # Remove numbering if present (1. 2. 3. etc)
                text = line
                # Remove common prefixes
                for prefix in ["1.", "2.", "3.", "4.", "5.", "-", "*", "•"]:
                    if text.startswith(prefix):
                        text = text[len(prefix):].strip()

                if text:  # Only add non-empty suggestions
                    suggestions.append(
                        SuggestionResponse(
                            text=text,
                            language=target_language,
                            confidence=0.7,
                            context=current_translation.translated_text,
                            alternatives=[]
                        )
                    )
                    print(f"[LLM] Suggestion {i+1}: {text}")

            # Ensure we have at least some suggestions
            if not suggestions:
                print(f"[LLM] Warning: No suggestions parsed, using fallback")
                # Language-specific fallbacks
                fallbacks = {
                    "pt": ["Entendi!", "Obrigado!", "Pode explicar melhor?"],
                    "en": ["I understand!", "Thank you!", "Could you explain more?"],
                    "es": ["¡Entiendo!", "¡Gracias!", "¿Puedes explicar más?"],
                    "fr": ["Je comprends!", "Merci!", "Pouvez-vous expliquer plus?"]
                }
                default_fallback = ["I see!", "Thanks!", "Tell me more."]
                texts = fallbacks.get(target_language, default_fallback)

                suggestions = [
                    SuggestionResponse(
                        text=text,
                        language=target_language,
                        confidence=0.5,
                        context="",
                        alternatives=[]
                    )
                    for text in texts[:num_suggestions]
                ]

            return suggestions

        except Exception as e:
            print(f"[LLM] Error generating suggestions: {e}")
            # Fallback suggestions based on language
            fallbacks = {
                "pt": ["Entendi!", "Obrigado!", "Pode explicar melhor?"],
                "en": ["I understand!", "Thank you!", "Could you explain more?"],
                "es": ["¡Entiendo!", "¡Gracias!", "¿Puedes explicar más?"]
            }
            default_fallback = ["I see!", "Thanks!", "Tell me more."]
            texts = fallbacks.get(target_language, default_fallback)

            return [
                SuggestionResponse(
                    text=text,
                    language=target_language,
                    confidence=0.5,
                    context="",
                    alternatives=[]
                )
                for text in texts[:num_suggestions]
            ]

    async def detect_language(self, text: str) -> str:
        """Detect language using langdetect."""
        try:
            return detect(text)
        except Exception:
            return "en"
