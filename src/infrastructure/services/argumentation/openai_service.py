"""OpenAI argumentation engine service implementation."""
from typing import List
from datetime import datetime
import json

from ....core.interfaces import IArgumentationEngineService
from ....core.entities import (
    ArgumentationSuggestion,
    SuggestionType,
    MeetingContext,
    ObjectionContext
)


class OpenAIArgumentationEngineService(IArgumentationEngineService):
    """OpenAI-powered argumentation engine for advanced suggestions."""

    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        """Initialize OpenAI argumentation engine."""
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=api_key)
            self.model = model
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai")

    async def generate_argumentation_suggestions(
        self,
        text: str,
        conversation_history: List[str],
        meeting_context: MeetingContext,
        target_language: str,
        num_suggestions: int = 3
    ) -> List[ArgumentationSuggestion]:
        """Generate advanced argumentation suggestions using GPT."""

        context_descriptions = {
            MeetingContext.SALES: "a sales conversation",
            MeetingContext.INTERVIEW: "a job interview",
            MeetingContext.PRESENTATION: "a business presentation",
            MeetingContext.NEGOTIATION: "a negotiation",
            MeetingContext.GENERAL: "a professional meeting"
        }

        history_text = "\n".join([f"- {msg}" for msg in conversation_history[-5:]])

        prompt = f"""You are an expert communication advisor in {context_descriptions[meeting_context]}.

Conversation history:
{history_text}

Current message from the other person:
"{text}"

Generate {num_suggestions} strategic response suggestions. For each suggestion:
1. Provide the actual response text in {target_language}
2. Classify it (sales, objection_handling, negotiation, clarification, closing, empathy, technical, general)
3. Assign priority (1=highest, 5=lowest)
4. Give confidence (0.0-1.0)
5. Explain the strategy
6. List key points to emphasize
7. Describe expected outcome

Respond in JSON array format:
[
  {{
    "text": "response here",
    "type": "sales",
    "priority": 1,
    "confidence": 0.9,
    "strategy": "why this works",
    "keywords": ["point1", "point2"],
    "outcome": "expected result"
  }}
]"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a strategic communication expert specializing in persuasive and effective responses."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )

            result_text = response.choices[0].message.content.strip()

            # Parse JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()

            results = json.loads(result_text)

            suggestions = []
            for item in results:
                # Map type string to enum
                type_map = {
                    "sales": SuggestionType.SALES,
                    "objection_handling": SuggestionType.OBJECTION_HANDLING,
                    "negotiation": SuggestionType.NEGOTIATION,
                    "clarification": SuggestionType.CLARIFICATION,
                    "closing": SuggestionType.CLOSING,
                    "empathy": SuggestionType.EMPATHY,
                    "technical": SuggestionType.TECHNICAL,
                    "general": SuggestionType.GENERAL,
                }

                suggestions.append(ArgumentationSuggestion(
                    text=item.get("text", ""),
                    suggestion_type=type_map.get(item.get("type", "general").lower(), SuggestionType.GENERAL),
                    priority=int(item.get("priority", 3)),
                    confidence=float(item.get("confidence", 0.8)),
                    context=item.get("strategy", ""),
                    keywords=item.get("keywords", []),
                    expected_outcome=item.get("outcome", ""),
                    timestamp=datetime.now()
                ))

            return suggestions[:num_suggestions]

        except Exception as e:
            print(f"OpenAI argumentation error: {e}")
            # Fallback
            return [ArgumentationSuggestion(
                text="Could you tell me more about that?",
                suggestion_type=SuggestionType.GENERAL,
                priority=2,
                confidence=0.6,
                context="Fallback response",
                keywords=["engagement"],
                expected_outcome="Continue conversation",
                timestamp=datetime.now()
            )]

    async def handle_objection(
        self,
        objection_context: ObjectionContext,
        conversation_history: List[str],
        target_language: str
    ) -> List[ArgumentationSuggestion]:
        """Generate counter-arguments for objections using GPT."""

        history_text = "\n".join([f"- {msg}" for msg in conversation_history[-5:]])

        prompt = f"""You are an expert at handling objections in professional conversations.

Conversation history:
{history_text}

Objection details:
Type: {objection_context.objection_type}
Text: "{objection_context.objection_text}"
Severity: {objection_context.severity * 100}%

Generate 3 strategic counter-arguments in {target_language}. Each should:
- Acknowledge the concern empathetically
- Provide a value-based response
- Move the conversation forward positively

Respond in JSON array format with same structure as before."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at handling objections with empathy and strategic value propositions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=600
            )

            result_text = response.choices[0].message.content.strip()

            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()

            results = json.loads(result_text)
            suggestions = []

            for item in results:
                suggestions.append(ArgumentationSuggestion(
                    text=item.get("text", ""),
                    suggestion_type=SuggestionType.OBJECTION_HANDLING,
                    priority=int(item.get("priority", 2)),
                    confidence=float(item.get("confidence", 0.85)),
                    context=item.get("strategy", ""),
                    keywords=item.get("keywords", []),
                    expected_outcome=item.get("outcome", ""),
                    timestamp=datetime.now()
                ))

            return suggestions

        except Exception as e:
            print(f"OpenAI objection handling error: {e}")
            return []

    async def suggest_closing_strategy(
        self,
        conversation_history: List[str],
        meeting_context: MeetingContext,
        target_language: str
    ) -> List[ArgumentationSuggestion]:
        """Suggest closing strategies using GPT."""

        history_text = "\n".join([f"- {msg}" for msg in conversation_history[-10:]])

        prompt = f"""Based on this conversation, suggest 3 strategic ways to close/conclude positively.

Conversation:
{history_text}

Context: {meeting_context.value}
Language: {target_language}

Provide closing strategies that:
- Summarize key agreements
- Create urgency appropriately
- Outline clear next steps

JSON format as before."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at closing conversations with clear next steps and positive momentum."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=500
            )

            result_text = response.choices[0].message.content.strip()

            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()

            results = json.loads(result_text)
            suggestions = []

            for item in results:
                suggestions.append(ArgumentationSuggestion(
                    text=item.get("text", ""),
                    suggestion_type=SuggestionType.CLOSING,
                    priority=int(item.get("priority", 1)),
                    confidence=float(item.get("confidence", 0.9)),
                    context=item.get("strategy", ""),
                    keywords=item.get("keywords", []),
                    expected_outcome=item.get("outcome", ""),
                    timestamp=datetime.now()
                ))

            return suggestions

        except Exception as e:
            print(f"OpenAI closing strategy error: {e}")
            return []
