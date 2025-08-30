"""Test embed and pgvector integration."""

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


class TestEmbedPGVector(unittest.TestCase):
    """Test embed and pgvector integration."""
    
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
    
    def test_embed_dimension_and_normalization(self):
        """Test embedding dimension and normalization."""
        # Test single embedding
        text = "This is a test document for embedding."
        embedding = self.embedder.embed_single(text)
        
        # Check dimension
        self.assertEqual(embedding.shape, (1024,))
        self.assertEqual(self.embedder.get_dimension(), 1024)
        
        # Check normalization (L2 norm should be close to 1)
        norm = np.linalg.norm(embedding)
        self.assertAlmostEqual(norm, 1.0, places=3)
        
        # Test batch embedding
        texts = ["First text", "Second text", "Third text"]
        embeddings = self.embedder.embed_texts(texts)
        
        # Check shape
        self.assertEqual(embeddings.shape, (3, 1024))
        
        # Check all embeddings are normalized
        for i in range(3):
            norm = np.linalg.norm(embeddings[i])
            self.assertAlmostEqual(norm, 1.0, places=3)
    
    def test_cosine_similarity(self):
        """Test cosine similarity between embeddings."""
        # Create similar texts
        text1 = "The cat is on the mat."
        text2 = "A cat sits on the mat."
        text3 = "The weather is sunny today."
        
        # Get embeddings
        emb1 = self.embedder.embed_single(text1)
        emb2 = self.embedder.embed_single(text2)
        emb3 = self.embedder.embed_single(text3)
        
        # Calculate cosine similarities
        sim_12 = np.dot(emb1, emb2)  # Already normalized
        sim_13 = np.dot(emb1, emb3)
        
        # Similar texts should have higher similarity
        self.assertGreater(sim_12, sim_13)
        
        # Self-similarity should be 1
        sim_11 = np.dot(emb1, emb1)
        self.assertAlmostEqual(sim_11, 1.0, places=5)
    
    def test_pgvector_integration(self):
        """Test full integration: embed → index → search."""
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
        embeddings = self.embedder.embed_texts(chunk_texts)
        
        # Check embeddings shape
        self.assertEqual(embeddings.shape, (len(chunks), 1024))
        
        # Index embeddings using chunk IDs only
        chunk_ids = [chunk.id for chunk in chunks]
        provider = self.embedder.get_provider()
        self.index.upsert_embeddings(chunk_ids, embeddings, provider)
        
        # Verify embeddings are stored
        stored_embeddings = self.db.query(Embedding).filter(
            Embedding.chunk_id.in_([chunk.id for chunk in chunks])
        ).all()
        
        self.assertEqual(len(stored_embeddings), len(chunks))
        
        # Test search
        query_text = "test document"
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
    
    def test_idempotency(self):
        """Test that upsert is idempotent."""
        # Create a test chunk
        document = self.db.query(Document).first()
        if not document:
            self.skipTest("No document available for testing")
        
        chunk = self.db.query(Chunk).filter(Chunk.document_id == document.id).first()
        if not chunk:
            self.skipTest("No chunk available for testing")
        
        # Generate embedding
        embedding = self.embedder.embed_single(chunk.text)
        provider = self.embedder.get_provider()
        
        # First upsert
        self.index.upsert_embeddings([chunk], embedding.reshape(1, -1), provider)
        
        # Count embeddings
        count1 = self.db.query(Embedding).filter(Embedding.chunk_id == chunk.id).count()
        
        # Second upsert (should not create duplicate)
        self.index.upsert_embeddings([chunk], embedding.reshape(1, -1), provider)
        
        # Count should be the same
        count2 = self.db.query(Embedding).filter(Embedding.chunk_id == chunk.id).count()
        
        self.assertEqual(count1, count2)
        self.assertEqual(count1, 1)  # Should be exactly one embedding per chunk


if __name__ == "__main__":
    unittest.main()
