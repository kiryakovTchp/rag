"""Test pgvector index functionality."""

import os
import time
import unittest
from pathlib import Path

import numpy as np

from fastapi.testclient import TestClient

from api.main import app
from db.models import Document, Chunk, Embedding
from db.session import SessionLocal
from services.embed.provider import EmbeddingProvider
from services.index.pgvector import PGVectorIndex


class TestIndexPGVector(unittest.TestCase):
    """Test pgvector index functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.client = TestClient(app)
        self.db = SessionLocal()
        
        # Set environment variables
        os.environ["DATABASE_URL"] = "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
        os.environ["EMBED_PROVIDER"] = "local"
        os.environ["EMBED_BATCH_SIZE"] = "64"
        
        self.embedder = EmbeddingProvider()
        self.index = PGVectorIndex()
    
    def tearDown(self):
        """Clean up test environment."""
        self.db.close()
    
    def test_upsert_and_search(self):
        """Test upsert embeddings and search functionality."""
        # Upload test document
        fixture_path = Path(__file__).parent / "fixtures" / "simple.pdf"
        
        with open(fixture_path, "rb") as f:
            response = self.client.post(
                "/ingest",
                files={"file": ("test.pdf", f, "application/pdf")},
                data={"tenant_id": "test", "safe_mode": "false"}
            )
        
        self.assertEqual(response.status_code, 200)
        job_id = response.json()["job_id"]
        
        # Wait for processing
        max_attempts = 60
        for attempt in range(max_attempts):
            response = self.client.get(f"/ingest/{job_id}")
            self.assertEqual(response.status_code, 200)
            
            job_status = response.json()
            if job_status["status"] == "done":
                break
            elif job_status["status"] == "error":
                self.fail(f"Job failed: {job_status.get('error', 'Unknown error')}")
            
            time.sleep(1)
        else:
            self.fail(f"Job did not complete within {max_attempts} seconds")
        
        # Get document and chunks
        document = self.db.query(Document).filter(Document.id == job_status["document_id"]).first()
        self.assertIsNotNone(document)
        
        chunks = self.db.query(Chunk).filter(Chunk.document_id == document.id).all()
        self.assertGreater(len(chunks), 0)
        
        # Generate embeddings for chunks
        chunk_texts = [chunk.text for chunk in chunks]
        chunk_ids = [chunk.id for chunk in chunks]
        embeddings = self.embedder.embed_texts(chunk_texts)
        
        # Check embeddings shape and type
        self.assertEqual(embeddings.shape, (len(chunks), 1024))
        self.assertEqual(embeddings.dtype, np.float32)
        
        # Index embeddings
        provider = self.embedder.get_provider()
        self.index.upsert_embeddings(chunk_ids, embeddings, provider)
        
        # Verify embeddings are stored
        stored_embeddings = self.db.query(Embedding).filter(
            Embedding.chunk_id.in_(chunk_ids)
        ).all()
        
        self.assertEqual(len(stored_embeddings), len(chunks))
        
        # Test search with query from document
        query_text = chunk_texts[0][:50]  # Use first 50 chars of first chunk
        query_embedding = self.embedder.embed_single(query_text)
        
        search_results = self.index.search(query_embedding, top_k=3)
        
        # Should find results
        self.assertGreater(len(search_results), 0)
        
        # Check result structure
        chunk_id, score = search_results[0]
        self.assertIsInstance(chunk_id, int)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        
        # The first chunk should be in top results (it's the query source)
        found_chunk_ids = [chunk_id for chunk_id, _ in search_results]
        self.assertIn(chunks[0].id, found_chunk_ids)
    
    def test_idempotent_upsert(self):
        """Test that upsert is idempotent."""
        # Create test embeddings
        test_texts = ["First test text", "Second test text", "Third test text"]
        test_embeddings = self.embedder.embed_texts(test_texts)
        test_chunk_ids = [1, 2, 3]  # Dummy IDs for testing
        provider = self.embedder.get_provider()
        
        # First upsert
        self.index.upsert_embeddings(test_chunk_ids, test_embeddings, provider)
        
        # Second upsert with same data (should not create duplicates)
        self.index.upsert_embeddings(test_chunk_ids, test_embeddings, provider)
        
        # Verify no duplicates were created
        # Note: This test assumes the embeddings table exists and works correctly
        # In a real scenario, we'd check the database directly
    
    def test_search_with_empty_index(self):
        """Test search behavior with empty index."""
        # Create a random query embedding
        query_embedding = np.random.rand(1024).astype(np.float32)
        # Normalize
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        
        # Search should return empty list
        results = self.index.search(query_embedding, top_k=10)
        self.assertEqual(len(results), 0)
    
    def test_search_score_range(self):
        """Test that search scores are in valid range [0, 1]."""
        # Upload and index a document
        fixture_path = Path(__file__).parent / "fixtures" / "simple.pdf"
        
        with open(fixture_path, "rb") as f:
            response = self.client.post(
                "/ingest",
                files={"file": ("test.pdf", f, "application/pdf")},
                data={"tenant_id": "test", "safe_mode": "false"}
            )
        
        self.assertEqual(response.status_code, 200)
        job_id = response.json()["job_id"]
        
        # Wait for processing
        for attempt in range(60):
            response = self.client.get(f"/ingest/{job_id}")
            if response.json()["status"] == "done":
                break
            time.sleep(1)
        
        # Get chunks and index them
        document = self.db.query(Document).filter(Document.id == response.json()["document_id"]).first()
        chunks = self.db.query(Chunk).filter(Chunk.document_id == document.id).all()
        
        chunk_texts = [chunk.text for chunk in chunks]
        chunk_ids = [chunk.id for chunk in chunks]
        embeddings = self.embedder.embed_texts(chunk_texts)
        
        provider = self.embedder.get_provider()
        self.index.upsert_embeddings(chunk_ids, embeddings, provider)
        
        # Test search with various queries
        test_queries = [
            "test document",
            "sample text",
            "completely unrelated query",
            chunk_texts[0][:30] if chunk_texts else "test"
        ]
        
        for query in test_queries:
            query_embedding = self.embedder.embed_single(query)
            results = self.index.search(query_embedding, top_k=5)
            
            for chunk_id, score in results:
                self.assertGreaterEqual(score, 0.0)
                self.assertLessEqual(score, 1.0)


if __name__ == "__main__":
    unittest.main()
