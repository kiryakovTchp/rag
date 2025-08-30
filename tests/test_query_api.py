"""Test query API functionality."""

import os
import time
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app
from db.models import Document, Chunk
from db.session import SessionLocal
from workers.tasks.index import index_document_embeddings


class TestQueryAPI(unittest.TestCase):
    """Test query API functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.client = TestClient(app)
        self.db = SessionLocal()
        
        # Set environment variables
        os.environ["DATABASE_URL"] = "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
        os.environ["EMBED_PROVIDER"] = "local"
        os.environ["EMBED_BATCH_SIZE"] = "64"
        os.environ["RERANK_ENABLED"] = "false"
    
    def tearDown(self):
        """Clean up test environment."""
        self.db.close()
    
    def test_query_api_end_to_end(self):
        """Test end-to-end query API functionality."""
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
        
        # Wait for embed job to complete using document status
        document_id = job_status.get("document_id")
        if document_id:
            for attempt in range(60):
                response = self.client.get(f"/ingest/document/{document_id}")
                document_status = response.json()
                embed_jobs = [j for j in document_status.get("jobs", []) if j.get("type") == "embed"]
                if embed_jobs and embed_jobs[0]["status"] == "done":
                    break
                elif embed_jobs and embed_jobs[0]["status"] == "error":
                    self.fail(f"Embed job failed: {embed_jobs[0].get('error', 'Unknown error')}")
                time.sleep(1)
            else:
                self.fail("Embed job did not complete within 60 seconds")
        
        # Test query API
        query_data = {
            "query": "test document",
            "top_k": 10,
            "rerank": False,
            "max_ctx": 1800
        }
        
        response = self.client.post("/query", json=query_data)
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        
        # Check response structure
        self.assertIn("matches", result)
        self.assertIn("usage", result)
        
        # Should have at least 3 matches
        self.assertGreaterEqual(len(result["matches"]), 3)
        
        # Check usage
        usage = result["usage"]
        self.assertIn("in_tokens", usage)
        self.assertIn("out_tokens", usage)
        self.assertGreater(usage["in_tokens"], 0)
        
        # Check match structure
        match = result["matches"][0]
        self.assertIn("doc_id", match)
        self.assertIn("chunk_id", match)
        self.assertIn("page", match)
        self.assertIn("score", match)
        self.assertIn("snippet", match)
        self.assertIn("breadcrumbs", match)
        
        # Check score range
        self.assertGreaterEqual(match["score"], 0.0)
        self.assertLessEqual(match["score"], 1.0)
        
        # Check usage
        usage = result["usage"]
        self.assertIn("in_tokens", usage)
        self.assertIn("out_tokens", usage)
        self.assertGreater(usage["in_tokens"], 0)
    
    def test_query_validation(self):
        """Test query API validation."""
        # Test empty query
        response = self.client.post("/query", json={"query": ""})
        self.assertEqual(response.status_code, 422)
        
        # Test invalid top_k
        response = self.client.post("/query", json={
            "query": "test",
            "top_k": 300  # > 200
        })
        self.assertEqual(response.status_code, 422)
        
        # Test invalid max_ctx
        response = self.client.post("/query", json={
            "query": "test",
            "max_ctx": 5000  # > 4000
        })
        self.assertEqual(response.status_code, 422)
    
    def test_rerank_disabled(self):
        """Test rerank when disabled."""
        response = self.client.post("/query", json={
            "query": "test",
            "rerank": True
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("not enabled", response.json()["detail"])
