"""LLM provider factory."""

import os

from services.llm.base import LLMProvider
from services.llm.gemini import GeminiProvider
from services.llm.ollama import OllamaProvider


def get_llm_provider() -> LLMProvider:
    """Get LLM provider based on environment configuration.

    Returns:
        Configured LLM provider instance

    Raises:
        ValueError: If provider is not supported or configuration is invalid
    """
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()

    if provider == "gemini":
        return GeminiProvider()
    if provider == "ollama":
        return OllamaProvider()
    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}. Supported: gemini, ollama"
        )
