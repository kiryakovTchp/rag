"""PostgreSQL pgvector index backend."""

import json
import os
from typing import List, Tuple

import numpy as np
from sqlalchemy import create_engine, text

from db.models import Chunk, Embedding
from db.session import SessionLocal


class PGVectorIndex:
    """PostgreSQL pgvector index backend."""

    def __init__(self):
        """Initialize pgvector index."""
        self.engine = create_engine(os.getenv("DATABASE_URL"))
        self._ensure_pgvector_extension()

    def _ensure_pgvector_extension(self):
        """Ensure pgvector extension is enabled."""
        with self.engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()

    def upsert_embeddings(self, chunks: List[Chunk], vectors: np.ndarray, provider: str):
        """Upsert embeddings for chunks.

        Args:
            chunks: List of chunks
            vectors: Numpy array of embeddings (n_chunks, 1024)
            provider: Embedding provider name
        """
        if len(chunks) != len(vectors):
            raise ValueError("Number of chunks must match number of vectors")

        db = SessionLocal()
        try:
            for chunk, vector in zip(chunks, vectors):
                # Convert vector to JSON string
                vector_json = json.dumps(vector.tolist())

                # Upsert embedding
                embedding = db.query(Embedding).filter(Embedding.chunk_id == chunk.id).first()

                if embedding:
                    # Update existing
                    embedding.vector = vector_json
                    embedding.provider = provider
                else:
                    # Create new
                    embedding = Embedding(chunk_id=chunk.id, vector=vector_json, provider=provider)
                    db.add(embedding)

            db.commit()
        finally:
            db.close()

    def search(self, query_vector: np.ndarray, top_k: int = 100) -> List[Tuple[int, float]]:
        """Search for similar chunks.

        Args:
            query_vector: Query embedding vector (1024,)
            top_k: Number of results to return

        Returns:
            List of (chunk_id, score) tuples sorted by score DESC
        """
        # Convert query vector to JSON
        query_json = json.dumps(query_vector.tolist())

        # SQL query using cosine similarity
        sql = """
        SELECT e.chunk_id, 
               1 - (e.vector <=> :query_vector) as score
        FROM embeddings e
        ORDER BY e.vector <=> :query_vector
        LIMIT :top_k
        """

        with self.engine.connect() as conn:
            result = conn.execute(text(sql), {"query_vector": query_json, "top_k": top_k})

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
