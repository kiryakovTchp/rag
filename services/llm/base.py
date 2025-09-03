"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from collections.abc import Iterator


class LLMProvider(ABC):
    """Base class for LLM providers."""

    @abstractmethod
    def generate(
        self,
        messages: list[dict],
        model: str,
        max_tokens: int,
        temperature: float = 0.7,
        timeout_s: int = 60,
    ) -> tuple[str, dict]:
        """Generate text from messages.

        Args:
            messages: List of message dictionaries
            model: Model name to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            timeout_s: Timeout in seconds

        Returns:
            Tuple of (generated_text, usage_info)
        """
        pass

    @abstractmethod
    def stream(
        self,
        messages: list[dict],
        model: str,
        max_tokens: int,
        temperature: float = 0.7,
        timeout_s: int = 60,
    ) -> Iterator[dict]:
        """Stream text generation from messages.

        Args:
            messages: List of message dictionaries
            model: Model name to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            timeout_s: Timeout in seconds

        Returns:
            Iterator of response chunks
        """
        pass
