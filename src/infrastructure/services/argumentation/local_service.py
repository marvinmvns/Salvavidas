"""Local argumentation engine service implementation."""
from typing import List
from datetime import datetime
import re

from ....core.interfaces import IArgumentationEngineService
from ....core.entities import (
    ArgumentationSuggestion,
    SuggestionType,
    MeetingContext,
    ObjectionContext
)


class LocalArgumentationEngineService(IArgumentationEngineService):
    """Local argumentation engine using pattern matching and templates."""

    def __init__(self):
        """Initialize local argumentation engine."""
        # Objection patterns and responses
        self.objection_patterns = {
            'price': {
                'keywords': ['expensive', 'cost', 'price', 'budget', 'afford', 'cheap'],
                'responses': [
                    "I understand the investment is significant. Let's look at the ROI - our clients typically see {value} return in the first year.",
                    "That's a valid concern. How about we explore a phased approach to spread the cost?",
                    "Let me show you the total cost of ownership compared to alternatives. Many find it's actually more cost-effective long-term."
                ]
            },
            'timeline': {
                'keywords': ['time', 'long', 'quick', 'fast', 'slow', 'deadline', 'urgent'],
                'responses': [
                    "I hear you on the timeline. We can prioritize the most critical features for immediate delivery.",
                    "What if we start with a pilot program? That way you can see results faster.",
                    "Let's break this into phases - which outcomes are most urgent for you?"
                ]
            },
            'features': {
                'keywords': ['feature', 'functionality', 'capability', 'missing', 'need', 'require'],
                'responses': [
                    "Great question about that feature. While it's not in the base package, we can customize it for your specific needs.",
                    "That functionality is on our roadmap. Would you like early access to beta features?",
                    "Let me understand your workflow better - there might be a way to achieve that with our existing features."
                ]
            },
            'competitor': {
                'keywords': ['competitor', 'alternative', 'other', 'versus', 'compare'],
                'responses': [
                    "I'm glad you're doing your research. The key difference is our focus on {differentiator}.",
                    "That's a solid alternative. What specifically appeals to you about them? Let me show how we address those needs.",
                    "Many of our clients came from there. The main reason they switched was {unique_value}."
                ]
            }
        }

        # Sales closing templates
        self.closing_templates = {
            MeetingContext.SALES: [
                "Based on everything we've discussed, it seems like this addresses your main concerns. Shall we move forward?",
                "What would it take to get started this week?",
                "I can offer {incentive} if we finalize by {deadline}. Does that work for you?"
            ],
            MeetingContext.NEGOTIATION: [
                "It sounds like we're aligned on the key points. Should we draft the agreement?",
                "What final concerns do you have before we proceed?",
                "Let's summarize what we've agreed on and next steps."
            ]
        }

    async def generate_argumentation_suggestions(
        self,
        text: str,
        conversation_history: List[str],
        meeting_context: MeetingContext,
        target_language: str,
        num_suggestions: int = 3
    ) -> List[ArgumentationSuggestion]:
        """Generate argumentation-based suggestions."""
        suggestions = []
        text_lower = text.lower()

        # Detect objection type
        objection_type = None
        for obj_type, data in self.objection_patterns.items():
            if any(kw in text_lower for kw in data['keywords']):
                objection_type = obj_type
                break

        # Generate responses based on context
        if objection_type:
            # Objection handling
            responses = self.objection_patterns[objection_type]['responses']
            for i, response in enumerate(responses[:num_suggestions]):
                suggestions.append(ArgumentationSuggestion(
                    text=response.format(
                        value="3x",
                        differentiator="customer success",
                        unique_value="dedicated support",
                        incentive="10% discount",
                        deadline="Friday"
                    ),
                    suggestion_type=SuggestionType.OBJECTION_HANDLING,
                    priority=i + 1,
                    confidence=0.8 - (i * 0.1),
                    context=f"Detected {objection_type} objection",
                    keywords=[objection_type, "value", "solution"],
                    expected_outcome="Address concern and move conversation forward",
                    timestamp=datetime.now()
                ))

        # Add sales suggestions if appropriate
        if meeting_context == MeetingContext.SALES and '?' in text:
            suggestions.append(ArgumentationSuggestion(
                text="That's an excellent question. Let me show you how this works in practice with a quick demo.",
                suggestion_type=SuggestionType.CLARIFICATION,
                priority=1,
                confidence=0.85,
                context="Question detected - provide clarification",
                keywords=["demo", "example", "clarification"],
                expected_outcome="Clear understanding and engagement",
                timestamp=datetime.now()
            ))

        # Empathy responses for concerns
        concern_words = ['worried', 'concerned', 'unsure', 'hesitant', 'doubt']
        if any(word in text_lower for word in concern_words):
            suggestions.append(ArgumentationSuggestion(
                text="I completely understand your concern. Many of our clients had the same question initially. Let me address that directly.",
                suggestion_type=SuggestionType.EMPATHY,
                priority=1,
                confidence=0.9,
                context="Concern detected - show empathy first",
                keywords=["empathy", "understanding", "validation"],
                expected_outcome="Build trust and rapport",
                timestamp=datetime.now()
            ))

        # If no specific pattern, provide general engagement
        if len(suggestions) == 0:
            suggestions.append(ArgumentationSuggestion(
                text="Tell me more about that. What's most important to you here?",
                suggestion_type=SuggestionType.GENERAL,
                priority=2,
                confidence=0.7,
                context="General engagement",
                keywords=["engagement", "discovery"],
                expected_outcome="Gather more information",
                timestamp=datetime.now()
            ))

        return suggestions[:num_suggestions]

    async def handle_objection(
        self,
        objection_context: ObjectionContext,
        conversation_history: List[str],
        target_language: str
    ) -> List[ArgumentationSuggestion]:
        """Generate counter-arguments for objections."""
        objection_type = objection_context.objection_type
        suggestions = []

        if objection_type in self.objection_patterns:
            responses = self.objection_patterns[objection_type]['responses']

            for i, response in enumerate(responses):
                suggestions.append(ArgumentationSuggestion(
                    text=response.format(
                        value="3x ROI",
                        differentiator="24/7 support",
                        unique_value="proven track record",
                        incentive="extended trial",
                        deadline="end of month"
                    ),
                    suggestion_type=SuggestionType.OBJECTION_HANDLING,
                    priority=i + 1,
                    confidence=0.9 - (i * 0.1),
                    context=f"Counter-argument for {objection_type}",
                    keywords=[objection_type, "solution", "value"],
                    expected_outcome="Overcome objection and build confidence",
                    timestamp=datetime.now()
                ))

        return suggestions

    async def suggest_closing_strategy(
        self,
        conversation_history: List[str],
        meeting_context: MeetingContext,
        target_language: str
    ) -> List[ArgumentationSuggestion]:
        """Suggest strategies to close/conclude the meeting."""
        suggestions = []

        templates = self.closing_templates.get(
            meeting_context,
            self.closing_templates[MeetingContext.SALES]
        )

        for i, template in enumerate(templates):
            suggestions.append(ArgumentationSuggestion(
                text=template.format(
                    incentive="priority implementation",
                    deadline="this Friday"
                ),
                suggestion_type=SuggestionType.CLOSING,
                priority=i + 1,
                confidence=0.85 - (i * 0.05),
                context="Closing strategy",
                keywords=["close", "agreement", "next steps"],
                expected_outcome="Move to decision/commitment",
                timestamp=datetime.now()
            ))

        return suggestions
