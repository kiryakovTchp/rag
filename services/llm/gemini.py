"""Gemini LLM provider using Google's Generative AI."""

import logging
import os
import time
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor

try:
    from google import genai  # для пакета google-genai
    from google.genai import types  # types находится в google.genai
except ImportError:
    # Если google-genai не установлен, создаем заглушки
    genai = None
    types = None
    raise ImportError(
        "google-genai package is required. Install with: pip install google-genai"
    )

from services.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """Gemini LLM provider implementation."""

    def __init__(self):
        """Initialize Gemini provider."""
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY or GEMINI_API_KEY environment variable required"
            )

        genai.configure(api_key=api_key)
        self.executor = ThreadPoolExecutor(max_workers=4)

    def _prepare_messages(self, messages: list[dict]) -> list[types.Content]:
        """Convert messages to Gemini format.

        Args:
            messages: List of message dictionaries

        Returns:
            List of Gemini Content objects
        """
        gemini_messages: list = []

        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")

            if role == "system":
                # Gemini doesn't support system messages, prepend to first user message
                if gemini_messages and gemini_messages[-1].role == "user":
                    gemini_messages[-1].parts[
                        0
                    ].text = f"{content}\n\n{gemini_messages[-1].parts[0].text}"
                else:
                    # Create a user message with system content
                    gemini_messages.append(
                        types.Content(
                            role="user", parts=[types.Part.from_text(content)]
                        )
                    )
            elif role == "user":
                gemini_messages.append(
                    types.Content(role="user", parts=[types.Part.from_text(content)])
                )
            elif role == "assistant":
                gemini_messages.append(
                    types.Content(role="model", parts=[types.Part.from_text(content)])
                )

        return gemini_messages

    def generate(
        self,
        messages: list[dict],
        model: str,
        max_tokens: int,
        temperature: float = 0.7,
        timeout_s: int = 60,
    ) -> tuple[str, dict]:
        """Generate text using Gemini.

        Args:
            messages: List of message dictionaries
            model: Model name (e.g., "gemini-pro")
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            timeout_s: Timeout in seconds

        Returns:
            Tuple of (generated_text, usage_info)
        """
        try:
            # Prepare messages
            gemini_messages = self._prepare_messages(messages)

            # Configure generation
            # config = types.GenerationConfig(
            #     max_output_tokens=max_tokens, temperature=temperature
            # )

            # Generate response
            start_time = time.time()
            response = self._generate_sync(
                gemini_messages, model, max_tokens, temperature
            )
            duration = time.time() - start_time

            # Extract usage info
            usage = {
                "provider": "gemini",
                "model": model,
                "in_tokens": self._count_tokens(messages),
                "out_tokens": len(response.split()),
                "latency_ms": int(duration * 1000),
                "cost_usd": self._estimate_cost(model, max_tokens),
            }

            return response, usage

        except Exception as e:
            # Handle specific errors
            if "API key" in str(e) or "403" in str(e):
                raise Exception("LLM_UNAVAILABLE: Invalid API key") from e
            elif "429" in str(e):
                raise Exception("LLM_UNAVAILABLE: Rate limit exceeded") from e
            elif "timeout" in str(e).lower():
                raise Exception("LLM_UNAVAILABLE: Request timeout") from e
            else:
                raise Exception(f"LLM_UNAVAILABLE: {str(e)}") from e

    def _generate_sync(self, contents, model, max_tokens, temperature):
        """Synchronous generation using executor."""
        model_instance = genai.GenerativeModel(model)

        config = types.GenerationConfig(
            max_output_tokens=max_tokens, temperature=temperature
        )

        response = model_instance.generate_content(contents, generation_config=config)

        return response.text

    def stream(
        self,
        messages: list[dict],
        model: str,
        max_tokens: int,
        temperature: float = 0.7,
        timeout_s: int = 60,
    ) -> Iterator[dict]:
        """Stream text generation using Gemini.

        Args:
            messages: List of message dictionaries
            model: Model name (e.g., "gemini-pro")
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            timeout_s: Timeout in seconds

        Yields:
            Response chunks as dictionaries
        """
        try:
            # Prepare messages
            gemini_messages = self._prepare_messages(messages)

            # Configure generation
            config = types.GenerationConfig(
                max_output_tokens=max_tokens, temperature=temperature
            )

            # Stream response
            start_time = time.time()
            for chunk in self._stream_sync(gemini_messages, model, config):
                if chunk.text:
                    yield {"type": "chunk", "text": chunk.text}

            # Send final chunk with usage info
            duration = time.time() - start_time
            usage = {
                "provider": "gemini",
                "model": model,
                "in_tokens": self._count_tokens(messages),
                "out_tokens": 0,  # Will be calculated from chunks
                "latency_ms": int(duration * 1000),
                "cost_usd": self._estimate_cost(model, max_tokens),
            }

            yield {"type": "done", "usage": usage}

        except Exception as e:
            # Handle specific errors
            if "API key" in str(e) or "403" in str(e):
                raise Exception("LLM_UNAVAILABLE: Invalid API key") from e
            elif "429" in str(e):
                raise Exception("LLM_UNAVAILABLE: Rate limit exceeded") from e
            elif "timeout" in str(e).lower():
                raise Exception("LLM_UNAVAILABLE: Request timeout") from e
            else:
                raise Exception(f"LLM_UNAVAILABLE: {str(e)}") from e

    def _stream_sync(self, contents, model, config):
        """Synchronous streaming using executor."""
        model_instance = genai.GenerativeModel(model)

        response = model_instance.generate_content(
            contents, generation_config=config, stream=True
        )

        for chunk in response:
            yield chunk

    def _count_tokens(self, messages: list[dict]) -> int:
        """Estimate token count for messages."""
        total = 0
        for message in messages:
            content = message.get("content", "")
            total += len(content.split()) * 1.3  # Rough estimate
        return int(total)

    def _estimate_cost(self, model: str, max_tokens: int) -> float:
        """Estimate cost for generation."""
        # Rough cost estimates (USD per 1K tokens)
        costs = {
            "gemini-pro": 0.0005,  # $0.0005 per 1K input tokens
            "gemini-pro-vision": 0.0005,
        }

        base_cost = costs.get(model, 0.001)
        return (max_tokens / 1000) * base_cost
