#!/usr/bin/env python3
"""Manual test script for PGVectorIndex."""

import os

import numpy as np

from services.embed.provider import EmbeddingProvider
from services.index.pgvector import PGVectorIndex


def test_pgvector_manual():
    """Test PGVectorIndex manually."""
    # Set environment
    os.environ[
        "DATABASE_URL"
    ] = "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
    os.environ["EMBED_PROVIDER"] = "local"

    print("🧪 Testing PGVectorIndex manually...")

    # Initialize services
    embedder = EmbeddingProvider()
    index = PGVectorIndex()

    # Test texts
    test_texts = [
        "This is a test document about machine learning",
        "Vector embeddings are used for semantic search",
        "PostgreSQL with pgvector provides efficient similarity search",
        "BGE-M3 is a multilingual embedding model",
        "RAG systems combine retrieval and generation",
    ]

    # Generate embeddings
    print("📊 Generating embeddings...")
    embeddings = embedder.embed_texts(test_texts)

    print(f"   Shape: {embeddings.shape}")
    print(f"   Dtype: {embeddings.dtype}")
    print(f"   L2 norms: {np.linalg.norm(embeddings, axis=1)}")

    # Test chunk IDs (dummy)
    chunk_ids = [1, 2, 3, 4, 5]
    provider = embedder.get_provider()

    # Upsert embeddings
    print("💾 Upserting embeddings...")
    index.upsert_embeddings(chunk_ids, embeddings, provider)
    print("   ✅ Upsert completed")

    # Test search
    print("🔍 Testing search...")
    query_text = "machine learning and embeddings"
    query_embedding = embedder.embed_single(query_text)

    results = index.search(query_embedding, top_k=3)

    print(f"   Query: '{query_text}'")
    print(f"   Results: {len(results)} found")

    for i, (chunk_id, score) in enumerate(results):
        print(f"   {i+1}. chunk_id={chunk_id}, score={score:.3f}")

    print("✅ PGVectorIndex test completed!")


if __name__ == "__main__":
    test_pgvector_manual()
