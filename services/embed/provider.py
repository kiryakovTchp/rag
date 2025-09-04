"""Embedding provider wrapper."""

import os
from typing import List, Optional

import numpy as np


class EmbeddingProvider:
    """Embedding provider wrapper that switches between local and Workers AI."""

    def __init__(self, provider: Optional[str] = None):
        """Initialize embedding provider based on environment."""
        self.provider = provider or os.getenv(
            "EMBED_PROVIDER", "ollama"
        )  # Default to ollama
        self.batch_size = int(os.getenv("EMBED_BATCH_SIZE", "64"))
        self._local_embedder = None
        self._workers_ai_embedder = None
        self._ollama_embedder = None

    def _get_local_embedder(self):
        """Lazy load local embedder only when needed."""
        if self._local_embedder is None:
            try:
                from services.embed.bge_m3 import BGEM3Embedder

                self._local_embedder = BGEM3Embedder(batch_size=self.batch_size)
            except ImportError as e:
                raise ImportError(
                    "Local embeddings require sentence-transformers. "
                    "Set EMBED_PROVIDER=workers_ai or install dependencies."
                ) from e
        return self._local_embedder

    def _get_workers_ai_embedder(self):
        """Lazy load Workers AI embedder only when needed."""
        if self._workers_ai_embedder is None:
            # Lazy import to avoid dependency when not used
            from services.embed.workers_ai import WorkersAIEmbedder

            self._workers_ai_embedder = WorkersAIEmbedder(batch_size=self.batch_size)
        return self._workers_ai_embedder

    def _get_ollama_embedder(self):
        """Lazy load Ollama embedder only when needed."""
        if self._ollama_embedder is None:
            from services.embed.ollama import OllamaEmbedder

            self._ollama_embedder = OllamaEmbedder(batch_size=self.batch_size)
        return self._ollama_embedder

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Embed a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            Numpy array of embeddings (n_texts, 1024)
        """
        if self.provider == "local":
            embedder = self._get_local_embedder()
        elif self.provider == "workers_ai":
            embedder = self._get_workers_ai_embedder()
        elif self.provider == "ollama":
            embedder = self._get_ollama_embedder()
        else:
            raise ValueError(f"Unknown embedding provider: {self.provider}")

        return embedder.embed_texts(texts)

    def embed_single(self, text: str) -> np.ndarray:
        """Embed a single text.

        Args:
            text: Text string to embed

        Returns:
            Embedding vector (1024,)
        """
        return self.embed_texts([text])[0]

    def get_dimension(self) -> int:
        """Get embedding dimension.

        Returns:
            Embedding dimension
        """
        if self.provider == "local":
            embedder = self._get_local_embedder()
        elif self.provider == "workers_ai":
            embedder = self._get_workers_ai_embedder()
        else:
            embedder = self._get_ollama_embedder()
        return embedder.get_dimension()

    def get_provider(self) -> str:
        """Get current provider name.

        Returns:
            Provider name (local or workers_ai)
        """
        return self.provider
