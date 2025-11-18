"""
AI integration service for communicating with external AI providers.

This service is designed to be provider-agnostic and can be easily
extended to support different AI providers.
"""
import logging
from typing import List, Dict, Any, Optional, Iterator
from abc import ABC, abstractmethod
from openai import OpenAI, APIError, RateLimitError, APIConnectionError
import google.generativeai as genai
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

    @abstractmethod
    def generate_response_stream(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Iterator[str]:
        """
        Generate a streaming response from the AI.

        Args:
            message: User's message
            conversation_history: Previous messages in the conversation

        Yields:
            Chunks of AI's response text
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

    def generate_response_stream(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Iterator[str]:
        """
        Generate a streaming response using OpenAI API.

        Args:
            message: User's current message
            conversation_history: List of previous messages in format
                [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]

        Yields:
            Chunks of AI's response text

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

            # Make streaming API call
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=500,  # Reasonable limit for kid responses
                temperature=0.7,
                presence_penalty=0.1,
                frequency_penalty=0.1,
                stream=True
            )

            # Yield response chunks
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

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


class GeminiProvider(AIProvider):
    """Google Gemini AI provider implementation."""

    def __init__(self):
        """Initialize Gemini client."""
        if not settings.GEMINI_API_KEY:
            logger.warning("Gemini API key not configured")
        
        # Configure the API key
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # Create the model
        self.model_name = "gemini-2.0-flash-lite"
        self.model = genai.GenerativeModel(self.model_name)

    def generate_response(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate a response using Google Gemini API.

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
            # Build contents for Gemini API
            contents = KID_FRIENDLY_SYSTEM_PROMPT + "\n\n"

            if conversation_history:
                # Limit history to last 10 exchanges to manage context
                recent_history = conversation_history[-20:]  # 10 exchanges = 20 messages
                for msg in recent_history:
                    role_prefix = "User: " if msg["role"] == "user" else "Assistant: "
                    contents += role_prefix + msg["content"] + "\n\n"

            # Add current user message
            contents += "User: " + message + "\n\nAssistant: "

            # Generate response
            response = self.model.generate_content(
                contents,
                generation_config={
                    "max_output_tokens": 500,
                    "temperature": 0.7,
                }
            )

            return response.text.strip()

        except Exception as e:
            error_str = str(e).lower()
            if "quota" in error_str or "rate" in error_str:
                logger.error(f"Gemini rate limit exceeded: {e}")
                raise AIServiceError("AI service is temporarily busy. Please try again in a moment.")
            elif "connection" in error_str or "network" in error_str:
                logger.error(f"Gemini connection error: {e}")
                raise AIServiceError("Unable to connect to AI service. Please try again later.")
            elif "invalid" in error_str and "key" in error_str:
                logger.error(f"Gemini API key error: {e}")
                raise AIServiceError("AI service configuration error. Please contact administrator.")
            else:
                logger.error(f"Unexpected error in Gemini service: {e}")
                raise AIServiceError("An unexpected error occurred. Please try again.")

    def generate_response_stream(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Iterator[str]:
        """
        Generate a streaming response using Google Gemini API.

        Args:
            message: User's current message
            conversation_history: List of previous messages in format
                [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]

        Yields:
            Chunks of AI's response text

        Raises:
            AIServiceError: If API call fails
        """
        try:
            # Build contents for Gemini API
            contents = KID_FRIENDLY_SYSTEM_PROMPT + "\n\n"

            if conversation_history:
                # Limit history to last 10 exchanges to manage context
                recent_history = conversation_history[-20:]  # 10 exchanges = 20 messages
                for msg in recent_history:
                    role_prefix = "User: " if msg["role"] == "user" else "Assistant: "
                    contents += role_prefix + msg["content"] + "\n\n"

            # Add current user message
            contents += "User: " + message + "\n\nAssistant: "

            # Generate streaming response
            response = self.model.generate_content(
                contents,
                generation_config={
                    "max_output_tokens": 500,
                    "temperature": 0.7,
                },
                stream=True
            )

            # Yield response chunks - properly handle the streaming iterator
            for chunk in response:
                # Access the text from the chunk's parts
                if hasattr(chunk, 'text') and chunk.text:
                    yield chunk.text
                elif hasattr(chunk, 'parts'):
                    for part in chunk.parts:
                        if hasattr(part, 'text') and part.text:
                            yield part.text

        except Exception as e:
            error_str = str(e).lower()
            if "quota" in error_str or "rate" in error_str:
                logger.error(f"Gemini rate limit exceeded: {e}")
                raise AIServiceError("AI service is temporarily busy. Please try again in a moment.")
            elif "connection" in error_str or "network" in error_str:
                logger.error(f"Gemini connection error: {e}")
                raise AIServiceError("Unable to connect to AI service. Please try again later.")
            elif "invalid" in error_str and "key" in error_str:
                logger.error(f"Gemini API key error: {e}")
                raise AIServiceError("AI service configuration error. Please contact administrator.")
            else:
                logger.error(f"Unexpected error in Gemini service: {e}")
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

    def generate_response_stream(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Iterator[str]:
        """
        Generate a mock streaming response.
        Args:
            message: User's message
            conversation_history: Previous messages (ignored)
        Yields:
            Chunks of mock response text
        """
        import time
        response = f"Thank you for your question about: '{message[:50]}...'. I'm here to help you learn and explore safely!"
        # Simulate streaming by yielding words one at a time
        words = response.split()
        for word in words:
            yield word + " "
            time.sleep(0.05)  # Small delay to simulate streaming


class AIService:
    """
    Main AI service that handles provider selection and response generation.

    This service acts as a facade over different AI providers.
    """

    def __init__(self, provider: Optional[AIProvider] = None):
        """
        Initialize AI service with a provider.

        Args:
            provider: AI provider instance. If not provided, selects based on AI_PROVIDER setting.
        """
        if provider:
            self.provider = provider
        else:
            self.provider = self._select_provider()

    def _select_provider(self) -> AIProvider:
        """
        Select the appropriate AI provider based on configuration.

        Provider selection logic:
        - If AI_PROVIDER is "openai": Use OpenAI (requires OPENAI_API_KEY)
        - If AI_PROVIDER is "gemini": Use Gemini (requires GEMINI_API_KEY)
        - If AI_PROVIDER is "auto" (default): Prefer Gemini if key exists, else OpenAI, else Mock

        Returns:
            AIProvider instance
        """
        provider_setting = settings.AI_PROVIDER.lower()

        if provider_setting == "openai":
            if settings.OPENAI_API_KEY:
                logger.info("Using OpenAI provider")
                return OpenAIProvider()
            else:
                logger.warning("OpenAI provider requested but no API key configured, using mock provider")
                return MockAIProvider()

        elif provider_setting == "gemini":
            if settings.GEMINI_API_KEY:
                logger.info("Using Gemini provider")
                return GeminiProvider()
            else:
                logger.warning("Gemini provider requested but no API key configured, using mock provider")
                return MockAIProvider()

        else:  # "auto" or any other value
            # Auto-select: prefer Gemini, then OpenAI, then Mock
            if settings.GEMINI_API_KEY:
                logger.info("Auto-selected Gemini provider")
                return GeminiProvider()
            elif settings.OPENAI_API_KEY:
                logger.info("Auto-selected OpenAI provider")
                return OpenAIProvider()
            else:
                logger.warning("No API keys configured, using mock provider")
                return MockAIProvider()

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

    def get_response_stream(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Iterator[str]:
        """
        Get streaming AI response for a message.

        Args:
            message: User's message
            conversation_history: Previous messages in conversation

        Yields:
            Chunks of AI's response text

        Raises:
            AIServiceError: If response generation fails
        """
        return self.provider.generate_response_stream(message, conversation_history)

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

    def generate_session_title(self, user_messages: List[str]) -> str:
        """
        Generate a concise title for a chat session based on user messages.

        Args:
            user_messages: List of user message contents (first 2-3 messages)

        Returns:
            A concise title (3-7 words) describing the conversation topic
        """
        if not user_messages:
            return "New Chat"

        # Combine first few user messages for context
        combined_messages = " ".join(user_messages[:3])

        # Create a prompt for title generation
        title_prompt = f"""Based on the following user messages from a child, generate a very short, descriptive title (3-7 words) that captures what the conversation is about. The title should be child-friendly and in present continuous or noun form.

Messages: {combined_messages[:500]}

Examples of good titles:
- Learning about dinosaurs
- Math homework help
- Space exploration questions
- Story about a dragon
- Drawing tips for beginners

Respond with ONLY the title, nothing else."""

        try:
            print(self.provider)
            # Use a simpler approach - just get a direct response
            if isinstance(self.provider, MockAIProvider):
                # For mock provider, generate a simple rule-based title
                return self._generate_rule_based_title(user_messages)

            # For real providers, we need to use direct API calls without the system prompt
            if isinstance(self.provider, OpenAIProvider):
                response = self.provider.client.chat.completions.create(
                    model=self.provider.model,
                    messages=[{"role": "user", "content": title_prompt}],
                    max_tokens=20,
                    temperature=0.5
                )
                title = response.choices[0].message.content.strip()
            elif isinstance(self.provider, GeminiProvider):
                # Use the new client API for title generation
                response = self.provider.client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[title_prompt],
                    config={
                        "max_output_tokens": 20,
                        "temperature": 0.5,
                    }
                )
                title = response.text.strip()
            else:
                return self._generate_rule_based_title(user_messages)
            print('title', title)

            # Clean up the title - remove quotes, limit length
            title = title.strip('"\'').strip()
            words = title.split()
            if len(words) > 7:
                title = " ".join(words[:7])

            return title if title else "New Chat"

        except Exception as e:
            logger.warning(f"Failed to generate AI title, using rule-based: {e}")
            return self._generate_rule_based_title(user_messages)

    def _generate_rule_based_title(self, user_messages: List[str]) -> str:
        """
        Generate a rule-based title from keywords when AI is unavailable.

        Args:
            user_messages: List of user message contents

        Returns:
            A simple keyword-based title
        """
        if not user_messages:
            return "New Chat"

        combined_text = " ".join(user_messages[:2]).lower()

        # Common topic keywords
        topics = {
            "math": "Math help session",
            "homework": "Homework assistance",
            "science": "Science questions",
            "history": "History exploration",
            "dinosaur": "Learning about dinosaurs",
            "space": "Space exploration",
            "planet": "Planets and astronomy",
            "story": "Story time",
            "animal": "Animal facts",
            "drawing": "Drawing help",
            "art": "Art and creativity",
            "game": "Gaming discussion",
            "book": "Book discussion",
            "write": "Writing assistance",
            "spell": "Spelling practice",
            "read": "Reading help",
        }

        for keyword, title in topics.items():
            if keyword in combined_text:
                return title

        # Default: use first few words of first message
        return user_messages[0]


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


def get_ai_response_stream(
    message: str,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> Iterator[str]:
    """
    Convenience function to get streaming AI response.

    Args:
        message: User's message
        conversation_history: Previous conversation messages

    Yields:
        Chunks of AI's response text
    """
    return ai_service.get_response_stream(message, conversation_history)


def generate_session_title(user_messages: List[str]) -> str:
    """
    Convenience function to generate a session title.

    Args:
        user_messages: List of user message contents

    Returns:
        Generated title string
    """
    return ai_service.generate_session_title(user_messages)
