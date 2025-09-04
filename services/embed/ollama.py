"""Ollama embedder service."""

import os
import time
from typing import List, Optional

import numpy as np
import requests


class OllamaEmbedder:
    """Embeddings via local/remote Ollama server."""

    def __init__(self, model: Optional[str] = None, batch_size: int = 64):
        """Initialize Ollama embedder.

        Args:
            model: Ollama embedding model (default: mxbai-embed-large)
            batch_size: Batch size for embedding generation
        """
        self.host = os.getenv("OLLAMA_HOST", "http://ollama:11434")
        self.model = model or os.getenv("OLLAMA_EMBED_MODEL", "mxbai-embed-large")
        # mxbai-embed-large -> 1024 dims
        self.dimension = int(os.getenv("EMBED_DIM", "1024"))
        self.batch_size = batch_size
        self.timeout = int(os.getenv("EMBED_TIMEOUT", "30"))
        self.max_retries = int(os.getenv("EMBED_MAX_RETRIES", "3"))
        self.retry_delay = float(os.getenv("EMBED_RETRY_DELAY", "1"))

    def _embed_one(self, text: str) -> np.ndarray:
        url = f"{self.host.rstrip('/')}/api/embeddings"
        payload = {"model": self.model, "input": text}
        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                resp = requests.post(url, json=payload, timeout=self.timeout)
                resp.raise_for_status()
                data = resp.json()
                emb = data.get("embedding")
                if not emb:
                    raise ValueError("No embedding in Ollama response")
                arr = np.array(emb, dtype=np.float32)
                # Normalize (optional but keeps parity with workers_ai implementation)
                norm = np.linalg.norm(arr)
                if norm > 0:
                    arr = arr / norm
                return arr
            except Exception as e:
                last_exc = e
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2**attempt))
                else:
                    raise
        # Should not reach here
        raise last_exc if last_exc else RuntimeError("Unknown embedding error")

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.array([], dtype=np.float32)
        out = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            for t in batch:
                out.append(self._embed_one(t))
        return np.vstack(out) if out else np.array([], dtype=np.float32)

    def embed_single(self, text: str) -> np.ndarray:
        return self._embed_one(text)

    def get_dimension(self) -> int:
        return self.dimension
