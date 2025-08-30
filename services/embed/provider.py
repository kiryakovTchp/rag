"""Embedding provider wrapper."""

import os
from typing import List

import numpy as np

from services.embed.bge_m3 import BGEM3Embedder
from services.embed.workers_ai import WorkersAIEmbedder


class EmbeddingProvider:
    """Embedding provider wrapper that switches between local and Workers AI."""

    def __init__(self):
        """Initialize embedding provider based on environment."""
        self.provider = os.getenv("EMBED_PROVIDER", "local")
        self.batch_size = int(os.getenv("EMBED_BATCH_SIZE", "64"))

        if self.provider == "local":
            self.embedder = BGEM3Embedder(batch_size=self.batch_size)
        elif self.provider == "workers_ai":
            self.embedder = WorkersAIEmbedder(batch_size=self.batch_size)
        else:
            raise ValueError(f"Unknown embedding provider: {self.provider}")

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Embed a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            Numpy array of embeddings (n_texts, 1024)
        """
        return self.embedder.embed_texts(texts)

    def embed_single(self, text: str) -> np.ndarray:
        """Embed a single text.

        Args:
            text: Text string to embed

        Returns:
            Embedding vector (1024,)
        """
        return self.embedder.embed_single(text)

    def get_dimension(self) -> int:
        """Get embedding dimension.

        Returns:
            Embedding dimension
        """
        return self.embedder.get_dimension()

    def get_provider(self) -> str:
        """Get current provider name.

        Returns:
            Provider name (local or workers_ai)
        """
        return self.provider
