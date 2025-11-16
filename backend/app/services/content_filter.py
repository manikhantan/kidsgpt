"""
Content filtering service for checking messages against parent rules.

This service is responsible for ensuring kid messages comply with
parent-defined content rules before being sent to the AI.
"""
import re
from typing import Tuple, Optional, List
from app.models import ContentRule, ContentRuleMode


class ContentFilter:
    """
    Service for filtering kid messages based on parent content rules.

    Supports two modes:
    - Allowlist: Only messages containing approved topics are allowed
    - Blocklist: Messages containing blocked keywords are rejected
    """

    @staticmethod
    def check_message(
        message: str,
        content_rules: ContentRule
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a message complies with content rules.

        Args:
            message: The message to check
            content_rules: Parent's content rules

        Returns:
            Tuple of (is_allowed, reason)
            - is_allowed: True if message passes filtering
            - reason: Explanation if blocked, None if allowed
        """
        if content_rules.mode == ContentRuleMode.ALLOWLIST:
            return ContentFilter._check_allowlist(message, content_rules)
        else:
            return ContentFilter._check_blocklist(message, content_rules)

    @staticmethod
    def _check_allowlist(
        message: str,
        content_rules: ContentRule
    ) -> Tuple[bool, Optional[str]]:
        """
        Check message against allowlist mode.

        In allowlist mode, the message must relate to at least one
        of the approved topics.

        Args:
            message: Message to check
            content_rules: Content rules with allowlist topics

        Returns:
            Tuple of (is_allowed, reason)
        """
        if not content_rules.topics:
            # If no topics defined in allowlist, block everything
            return (False, "No approved topics configured. Contact your parent.")

        message_lower = message.lower()

        # Check if message contains any approved topic
        for topic in content_rules.topics:
            topic_lower = topic.lower()
            # Use word boundary matching for better accuracy
            if ContentFilter._contains_word(message_lower, topic_lower):
                return (True, None)

        # No approved topic found in message
        return (
            False,
            f"Message must be about an approved topic: {', '.join(content_rules.topics)}"
        )

    @staticmethod
    def _check_blocklist(
        message: str,
        content_rules: ContentRule
    ) -> Tuple[bool, Optional[str]]:
        """
        Check message against blocklist mode.

        In blocklist mode, the message is rejected if it contains
        any blocked keywords.

        Args:
            message: Message to check
            content_rules: Content rules with blocked keywords

        Returns:
            Tuple of (is_allowed, reason)
        """
        if not content_rules.keywords:
            # If no keywords defined in blocklist, allow everything
            return (True, None)

        message_lower = message.lower()

        # Check if message contains any blocked keyword
        blocked_keywords_found = []
        for keyword in content_rules.keywords:
            keyword_lower = keyword.lower()
            # Use substring matching for blocklist (more restrictive)
            if ContentFilter._contains_keyword(message_lower, keyword_lower):
                blocked_keywords_found.append(keyword)

        if blocked_keywords_found:
            return (
                False,
                "Message contains restricted content. Please rephrase your question."
            )

        return (True, None)

    @staticmethod
    def _contains_word(text: str, word: str) -> bool:
        """
        Check if text contains word (with word boundary matching).

        Uses regex word boundaries for more accurate topic matching.

        Args:
            text: Text to search in (lowercase)
            word: Word to search for (lowercase)

        Returns:
            True if word found in text
        """
        # Escape special regex characters in the word
        escaped_word = re.escape(word)
        # Match as whole word or part of compound word
        pattern = rf'\b{escaped_word}\b|{escaped_word}'
        return bool(re.search(pattern, text))

    @staticmethod
    def _contains_keyword(text: str, keyword: str) -> bool:
        """
        Check if text contains keyword (substring matching).

        Uses substring matching for blocklist to be more restrictive.

        Args:
            text: Text to search in (lowercase)
            keyword: Keyword to search for (lowercase)

        Returns:
            True if keyword found in text
        """
        return keyword in text

    @staticmethod
    def sanitize_message(message: str) -> str:
        """
        Sanitize user input to prevent injection attacks.

        Args:
            message: Raw user message

        Returns:
            Sanitized message
        """
        # Remove null bytes
        message = message.replace('\x00', '')

        # Remove excessive whitespace
        message = ' '.join(message.split())

        # Limit message length (redundant with Pydantic but good to have)
        max_length = 2000
        if len(message) > max_length:
            message = message[:max_length]

        return message.strip()


def filter_message(
    message: str,
    content_rules: ContentRule
) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to filter a message.

    Args:
        message: Message to filter
        content_rules: Parent's content rules

    Returns:
        Tuple of (is_allowed, reason)
    """
    sanitized = ContentFilter.sanitize_message(message)
    return ContentFilter.check_message(sanitized, content_rules)
