"""OpenAI LLM service for response suggestions."""
from typing import List
from datetime import datetime
from openai import AsyncOpenAI

from ....core.interfaces import ILanguageModelService
from ....core.entities import Translation, SuggestionResponse


class OpenAILLMService(ILanguageModelService):
    """OpenAI GPT service for generating response suggestions."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4-turbo-preview"
    ):
        """Initialize OpenAI client."""
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

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
            context = "\n".join(conversation_history[-5:])  # Last 5 messages

            # Create prompt
            prompt = f"""Given this conversation context:
{context}

The other person just said: "{current_translation.translated_text}"

Generate {num_suggestions} natural, contextually appropriate responses in {target_language}.
Make them diverse: one formal, one casual, and one question/clarification.

Format each response on a new line, numbered 1-{num_suggestions}."""

            # Generate
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a helpful assistant that suggests natural conversation responses in {target_language}."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.8,
                max_tokens=300
            )

            # Parse suggestions
            suggestions_text = response.choices[0].message.content.strip()
            suggestions = []

            for line in suggestions_text.split("\n"):
                line = line.strip()
                if line and any(line.startswith(f"{i}.") for i in range(1, num_suggestions + 1)):
                    text = line.split(".", 1)[1].strip()
                    suggestions.append(
                        SuggestionResponse(
                            text=text,
                            language=target_language,
                            confidence=0.9,
                            context=current_translation.translated_text,
                            alternatives=[]
                        )
                    )

            return suggestions[:num_suggestions]

        except Exception as e:
            raise RuntimeError(f"OpenAI suggestion generation failed: {e}")

    async def detect_language(self, text: str) -> str:
        """Detect language of text."""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Detect the language of the text and respond with only the 2-letter ISO 639-1 language code (e.g., 'en', 'pt', 'es')."
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0,
                max_tokens=10
            )

            lang_code = response.choices[0].message.content.strip().lower()
            return lang_code

        except Exception:
            return "en"  # Default to English
