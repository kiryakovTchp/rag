"""Google AI Studio (Gemini) LLM provider."""

import asyncio
import os
import time
from typing import Iterator, List
from concurrent.futures import ThreadPoolExecutor

from google import genai
from google.genai import types

from services.llm.base import LLMProvider


class GeminiProvider(LLMProvider):
    """Google AI Studio provider using Gemini models."""
    
    def __init__(self):
        """Initialize Gemini provider."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        self.client = genai.Client(api_key=api_key)
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def _prepare_messages(self, messages: List[dict]) -> List[types.Content]:
        """Convert messages to Gemini format.
        
        Gemini doesn't have a separate system role, so we prepend system messages
        to the first user message.
        """
        contents = []
        system_parts = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                system_parts.append(content)
            elif role == "user":
                # Combine system messages with user message
                if system_parts:
                    full_content = "\n\n".join(system_parts + [content])
                    system_parts = []  # Clear after using
                else:
                    full_content = content
                
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_text(full_content)]
                ))
            elif role == "assistant":
                contents.append(types.Content(
                    role="model",
                    parts=[types.Part.from_text(content)]
                ))
        
        return contents
    
    def generate(
        self, 
        messages: List[dict], 
        model: str, 
        max_tokens: int, 
        temperature: float, 
        timeout_s: int
    ) -> tuple[str, dict]:
        """Generate a single response."""
        start_time = time.time()
        
        try:
            contents = self._prepare_messages(messages)
            
            # Run in thread pool with timeout
            future = self.executor.submit(
                self._generate_sync,
                contents, model, max_tokens, temperature
            )
            
            response = future.result(timeout=timeout_s)
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Parse usage if available
            usage = {
                "in_tokens": None,
                "out_tokens": None,
                "latency_ms": latency_ms,
                "provider": "gemini",
                "model": model,
                "cost_usd": None
            }
            
            if hasattr(response, 'usage_metadata'):
                usage["in_tokens"] = response.usage_metadata.prompt_token_count
                usage["out_tokens"] = response.usage_metadata.candidates_token_count
            
            return response.text, usage
            
        except Exception as e:
            # Handle specific errors
            if "API key" in str(e) or "403" in str(e):
                raise Exception("LLM_UNAVAILABLE: Invalid API key")
            elif "429" in str(e):
                raise Exception("LLM_UNAVAILABLE: Rate limit exceeded")
            elif "timeout" in str(e).lower():
                raise Exception("LLM_UNAVAILABLE: Request timeout")
            else:
                raise Exception(f"LLM_UNAVAILABLE: {str(e)}")
    
    def _generate_sync(self, contents, model, max_tokens, temperature):
        """Synchronous generation call."""
        config = types.GenerateContentConfig(
            max_output_tokens=max_tokens,
            temperature=temperature
        )
        
        return self.client.models.generate_content(
            model=model,
            contents=contents,
            config=config
        )
    
    def stream(
        self, 
        messages: List[dict], 
        model: str, 
        max_tokens: int, 
        temperature: float, 
        timeout_s: int
    ) -> Iterator[str]:
        """Generate streaming response."""
        try:
            contents = self._prepare_messages(messages)
            
            config = types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                temperature=temperature
            )
            
            # Run in thread pool with timeout
            future = self.executor.submit(
                self._stream_sync,
                contents, model, config
            )
            
            # Yield chunks with timeout
            start_time = time.time()
            for chunk in future.result(timeout=timeout_s):
                if time.time() - start_time > timeout_s:
                    raise Exception("LLM_UNAVAILABLE: Stream timeout")
                
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            # Handle specific errors
            if "API key" in str(e) or "403" in str(e):
                raise Exception("LLM_UNAVAILABLE: Invalid API key")
            elif "429" in str(e):
                raise Exception("LLM_UNAVAILABLE: Rate limit exceeded")
            elif "timeout" in str(e).lower():
                raise Exception("LLM_UNAVAILABLE: Request timeout")
            else:
                raise Exception(f"LLM_UNAVAILABLE: {str(e)}")
    
    def _stream_sync(self, contents, model, config):
        """Synchronous streaming call."""
        return self.client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=config
        )
