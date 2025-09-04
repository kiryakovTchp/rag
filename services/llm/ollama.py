"""Ollama LLM provider implementation."""

import os
import time
from collections.abc import Iterator
from typing import Any

import requests

from services.llm.base import LLMProvider


class OllamaProvider(LLMProvider):
    """LLM provider using local/remote Ollama server."""

    def __init__(self) -> None:
        self.host = os.getenv("OLLAMA_HOST", "http://ollama:11434").rstrip("/")
        self.default_model = os.getenv("OLLAMA_GEN_MODEL", "llama3:8b")
        self.timeout = int(os.getenv("LLM_TIMEOUT", "60"))

    def _messages_to_prompt(self, messages: list[dict]) -> str:
        parts: list[str] = []
        for m in messages:
            content = m.get("content") or ""
            parts.append(str(content))
        return "\n\n".join(parts)

    def generate(
        self,
        messages: list[dict],
        model: str | None,
        max_tokens: int,
        temperature: float = 0.7,
        timeout_s: int = 60,
    ) -> tuple[str, dict]:
        start = time.time()
        prompt = self._messages_to_prompt(messages)
        payload: dict[str, Any] = {
            "model": model or self.default_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        url = f"{self.host}/api/generate"
        resp = requests.post(url, json=payload, timeout=timeout_s or self.timeout)
        resp.raise_for_status()
        data = resp.json()
        text = data.get("response", "")
        latency_ms = int((time.time() - start) * 1000)
        usage = {
            "provider": "ollama",
            "model": payload["model"],
            "in_tokens": None,
            "out_tokens": None,
            "latency_ms": latency_ms,
            "cost_usd": None,
        }
        return text, usage

    def stream(
        self,
        messages: list[dict],
        model: str | None,
        max_tokens: int,
        temperature: float = 0.7,
        timeout_s: int = 60,
    ) -> Iterator[str]:
        prompt = self._messages_to_prompt(messages)
        payload: dict[str, Any] = {
            "model": model or self.default_model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        url = f"{self.host}/api/generate"
        with requests.post(
            url, json=payload, timeout=timeout_s or self.timeout, stream=True
        ) as r:
            r.raise_for_status()
            for line in r.iter_lines(decode_unicode=True):
                if not line:
                    continue
                # Each line is a JSON with keys: response, done, etc.
                try:
                    import json

                    obj = json.loads(line)
                    chunk = obj.get("response")
                    if chunk:
                        yield chunk
                except Exception:
                    # Best-effort parse; ignore broken lines
                    continue
