"""
AI integration service for communicating with external AI providers.

This service is designed to be provider-agnostic and can be easily
extended to support different AI providers.
"""
import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from openai import OpenAI, APIError, RateLimitError, APIConnectionError
from app.config import get_settings
from app.core.exceptions import AIServiceError

logger = logging.getLogger(__name__)
settings = get_settings()


# System prompt for kid-friendly responses
KID_FRIENDLY_SYSTEM_PROMPT = """You are a helpful, friendly AI assistant designed for children.
Your responses should be:
- Age-appropriate and safe for kids
- Educational and encouraging
- Clear and easy to understand
- Free from any inappropriate content
- Supportive of learning and curiosity

Important guidelines:
- Never discuss violence, inappropriate content, or adult themes
- Encourage curiosity and learning
- Be patient and supportive
- Use simple, clear language
- If asked about something inappropriate, politely redirect to safer topics
- Always prioritize the child's safety and well-being"""


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    def generate_response(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate a response from the AI.

        Args:
            message: User's message
            conversation_history: Previous messages in the conversation

        Returns:
            AI's response text
        """
        pass


class OpenAIProvider(AIProvider):
    """OpenAI API provider implementation."""

    def __init__(self):
        """Initialize OpenAI client."""
        if not settings.OPENAI_API_KEY:
            logger.warning("OpenAI API key not configured")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-3.5-turbo"  # Can be configured via settings

    def generate_response(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate a response using OpenAI API.

        Args:
            message: User's current message
            conversation_history: List of previous messages in format
                [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]

        Returns:
            AI's response text

        Raises:
            AIServiceError: If API call fails
        """
        try:
            # Build messages list with system prompt and history
            messages = [
                {"role": "system", "content": KID_FRIENDLY_SYSTEM_PROMPT}
            ]

            # Add conversation history if provided
            if conversation_history:
                # Limit history to last 10 exchanges to manage context
                recent_history = conversation_history[-20:]  # 10 exchanges = 20 messages
                messages.extend(recent_history)

            # Add current user message
            messages.append({"role": "user", "content": message})

            # Make API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=500,  # Reasonable limit for kid responses
                temperature=0.7,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )

            # Extract and return response text
            return response.choices[0].message.content.strip()

        except RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            raise AIServiceError("AI service is temporarily busy. Please try again in a moment.")

        except APIConnectionError as e:
            logger.error(f"OpenAI connection error: {e}")
            raise AIServiceError("Unable to connect to AI service. Please try again later.")

        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise AIServiceError("AI service encountered an error. Please try again.")

        except Exception as e:
            logger.error(f"Unexpected error in AI service: {e}")
            raise AIServiceError("An unexpected error occurred. Please try again.")


class MockAIProvider(AIProvider):
    """Mock AI provider for testing without API calls."""

    def generate_response(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate a mock response.

        Args:
            message: User's message
            conversation_history: Previous messages (ignored)

        Returns:
            Mock response text
        """
        return f"Thank you for your question about: '{message[:50]}...'. I'm here to help you learn and explore safely!"


class AIService:
    """
    Main AI service that handles provider selection and response generation.

    This service acts as a facade over different AI providers.
    """

    def __init__(self, provider: Optional[AIProvider] = None):
        """
        Initialize AI service with a provider.

        Args:
            provider: AI provider instance. Defaults to OpenAI provider.
        """
        if provider:
            self.provider = provider
        elif settings.OPENAI_API_KEY:
            self.provider = OpenAIProvider()
        else:
            logger.warning("No OpenAI API key configured, using mock provider")
            self.provider = MockAIProvider()

    def get_response(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Get AI response for a message.

        Args:
            message: User's message
            conversation_history: Previous messages in conversation

        Returns:
            AI's response text

        Raises:
            AIServiceError: If response generation fails
        """
        return self.provider.generate_response(message, conversation_history)

    @staticmethod
    def format_history_from_messages(messages: List[Any]) -> List[Dict[str, str]]:
        """
        Format database message objects into conversation history format.

        Args:
            messages: List of Message model objects

        Returns:
            List of dictionaries with role and content
        """
        history = []
        for msg in messages:
            if not msg.blocked:  # Don't include blocked messages in history
                history.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
        return history


# Global AI service instance (can be replaced for testing)
ai_service = AIService()


def get_ai_response(
    message: str,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> str:
    """
    Convenience function to get AI response.

    Args:
        message: User's message
        conversation_history: Previous conversation messages

    Returns:
        AI's response text
    """
    return ai_service.get_response(message, conversation_history)
