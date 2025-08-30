"""Test retrieve functionality."""

import os
import time
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app
from db.models import Document, Chunk
from db.session import SessionLocal
from services.retrieve.dense import DenseRetriever
from workers.tasks.index import index_document_embeddings


class TestRetrieve(unittest.TestCase):
    """Test retrieve functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.client = TestClient(app)
        self.db = SessionLocal()
        
        # Set environment variables
        os.environ["DATABASE_URL"] = "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
        os.environ["EMBED_PROVIDER"] = "local"
        os.environ["EMBED_BATCH_SIZE"] = "64"
    
    def tearDown(self):
        """Clean up test environment."""
        self.db.close()
    
    def test_retrieve_from_document(self):
        """Test that retrieve finds relevant chunks from document."""
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
        
        # Wait for processing to complete
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
        
        # Get document
        document = self.db.query(Document).order_by(Document.id.desc()).first()
        self.assertIsNotNone(document)
        
        # Get chunks
        chunks = self.db.query(Chunk).filter(Chunk.document_id == document.id).all()
        self.assertGreater(len(chunks), 0)
        
        # Index embeddings
        index_document_embeddings(document.id)
        
        # Test retrieve
        retriever = DenseRetriever()
        
        # Search for text that should be in the document
        query = "test document"
        results = retriever.search(query, top_k=3)
        
        # Should find at least one result
        self.assertGreater(len(results), 0)
        
        # Check result structure
        result = results[0]
        self.assertIn("chunk_id", result)
        self.assertIn("doc_id", result)
        self.assertIn("score", result)
        self.assertIn("snippet", result)
        self.assertIn("breadcrumbs", result)
        
        # Score should be reasonable
        self.assertGreaterEqual(result["score"], 0.0)
        self.assertLessEqual(result["score"], 1.0)
