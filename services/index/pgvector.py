"""PostgreSQL pgvector index backend."""

import json
import os
from typing import List, Tuple

import numpy as np
from sqlalchemy import text

from db.models import Chunk, Embedding
from db.session import SessionLocal, engine


class PGVectorIndex:
    """PostgreSQL pgvector index backend."""

    def __init__(self):
        """Initialize pgvector index."""
        self._ensure_pgvector_extension()

    def _ensure_pgvector_extension(self):
        """Ensure pgvector extension is enabled."""
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()

    def upsert_embeddings(self, chunk_ids: List[int], vectors: np.ndarray, provider: str):
        """Upsert embeddings for chunks.

        Args:
            chunk_ids: List of chunk IDs
            vectors: Numpy array of embeddings (n_chunks, 1024) float32
            provider: Embedding provider name
        """
        if len(chunk_ids) != len(vectors):
            raise ValueError("Number of chunk_ids must match number of vectors")

        # Ensure vectors are float32
        vectors = vectors.astype(np.float32)

        db = SessionLocal()
        try:
            # Use raw SQL for efficient upsert
            sql = """
            INSERT INTO embeddings (chunk_id, vector, provider, created_at)
            VALUES (:chunk_id, :vector, :provider, NOW())
            ON CONFLICT (chunk_id) 
            DO UPDATE SET 
                vector = EXCLUDED.vector,
                provider = EXCLUDED.provider,
                updated_at = NOW()
            """

            for chunk_id, vector in zip(chunk_ids, vectors):
                # pgvector adapter will handle numpy array conversion directly
                db.execute(
                    text(sql),
                    {
                        "chunk_id": chunk_id,
                        "vector": vector,  # numpy array passed directly
                        "provider": provider,
                    },
                )

            db.commit()
        finally:
            db.close()

    def search(self, query_vector: np.ndarray, top_k: int = 100) -> List[Tuple[int, float]]:
        """Search for similar chunks.

        Args:
            query_vector: Query embedding vector (1024,) float32
            top_k: Number of results to return

        Returns:
            List of (chunk_id, score) tuples sorted by score DESC
        """
        import os

        # Ensure query vector is float32
        query_vector = query_vector.astype(np.float32)

        # Get probes from environment
        probes = int(os.getenv("IVFFLAT_PROBES", "10"))

        # SQL query using cosine similarity with L2 normalization
        sql = """
        SET LOCAL ivfflat.probes = COALESCE(:probes, 10);
        SELECT e.chunk_id, 
               1 - (e.vector <=> :query_vector) as score
        FROM embeddings e
        ORDER BY e.vector <=> :query_vector
        LIMIT :top_k
        """

        with engine.connect() as conn:
            result = conn.execute(
                text(sql), {"query_vector": query_vector, "top_k": top_k, "probes": probes}
            )

            results = []
            for row in result:
                chunk_id = row[0]
                score = float(row[1])
                results.append((chunk_id, score))

            return results

    def get_chunk_by_id(self, chunk_id: int) -> Chunk:
        """Get chunk by ID.

        Args:
            chunk_id: Chunk ID

        Returns:
            Chunk object
        """
        db = SessionLocal()
        try:
            return db.query(Chunk).filter(Chunk.id == chunk_id).first()
        finally:
            db.close()
