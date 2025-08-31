"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from typing import Iterator, List


class LLMProvider(ABC):
    """Base interface for LLM providers."""
    
    @abstractmethod
    def generate(
        self, 
        messages: List[dict], 
        model: str, 
        max_tokens: int, 
        temperature: float, 
        timeout_s: int
    ) -> tuple[str, dict]:
        """Generate a single response.
        
        Args:
            messages: List of message dicts with "role" and "content"
            model: Model name to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            timeout_s: Timeout in seconds
            
        Returns:
            Tuple of (response_text, usage_dict)
            
        Raises:
            Exception: If generation fails
        """
        pass
    
    @abstractmethod
    def stream(
        self, 
        messages: List[dict], 
        model: str, 
        max_tokens: int, 
        temperature: float, 
        timeout_s: int
    ) -> Iterator[str]:
        """Generate streaming response.
        
        Args:
            messages: List of message dicts with "role" and "content"
            model: Model name to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            timeout_s: Timeout in seconds
            
        Yields:
            Text chunks as they arrive
            
        Raises:
            Exception: If generation fails
        """
        pass
