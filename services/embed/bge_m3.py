"""BGE-M3 embedder service."""

from typing import List

import numpy as np


class BGEM3Embedder:
    """BGE-M3 embedder using sentence-transformers."""

    def __init__(self, batch_size: int = 64):
        """Initialize BGE-M3 embedder.

        Args:
            batch_size: Batch size for embedding generation
        """
        self.batch_size = batch_size
        self.model = None
        self.dimension = 1024

        # Lazy import to avoid startup failures
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer("BAAI/bge-m3")
        except ImportError:
            raise ValueError(
                "Local embeddings require `sentence-transformers` and compatible deps. "
                "Either install deps or set EMBED_PROVIDER=workers_ai."
            )

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Embed a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            Numpy array of embeddings (n_texts, 1024) float32
        """
        if not texts:
            return np.array([], dtype=np.float32)

        # Process in batches
        all_embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]

            # Generate embeddings with L2 normalization
            embeddings = self.model.encode(batch, normalize_embeddings=True)
            all_embeddings.append(embeddings)

        # Concatenate all batches and ensure float32
        if all_embeddings:
            result = np.vstack(all_embeddings).astype(np.float32)
            return result
        else:
            return np.array([], dtype=np.float32)

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
            Embedding dimension (1024)
        """
        return self.dimension
