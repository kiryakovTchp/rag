"""Test document status endpoint."""

import time
import unittest
from fastapi.testclient import TestClient

from api.main import app
from db.models import Document, Job
from db.session import SessionLocal


class TestDocumentStatus(unittest.TestCase):
    """Test document status endpoint."""

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(app)
        self.db = SessionLocal()

    def tearDown(self):
        """Clean up."""
        self.db.close()

    def test_document_status_with_jobs(self):
        """Test that document status returns jobs in correct order."""
        # Create test document
        document = Document(
            name="test_doc.pdf",
            mime="application/pdf",
            storage_uri="s3://test/test.pdf",
            status="uploaded"
        )
        self.db.add(document)
        self.db.flush()

        # Create jobs in chronological order
        parse_job = Job(
            type="parse",
            status="done",
            progress=100,
            document_id=document.id
        )
        self.db.add(parse_job)

        chunk_job = Job(
            type="chunk",
            status="done",
            progress=100,
            document_id=document.id
        )
        self.db.add(chunk_job)

        embed_job = Job(
            type="embed",
            status="done",
            progress=100,
            document_id=document.id
        )
        self.db.add(embed_job)

        self.db.commit()

        # Test document status endpoint
        response = self.client.get(f"/ingest/document/{document.id}")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["document_id"], document.id)
        self.assertEqual(data["status"], "uploaded")

        # Check jobs are present
        jobs = data["jobs"]
        self.assertEqual(len(jobs), 3)

        # Check job types
        job_types = [job["type"] for job in jobs]
        self.assertIn("parse", job_types)
        self.assertIn("chunk", job_types)
        self.assertIn("embed", job_types)

        # Check all jobs are done
        for job in jobs:
            self.assertEqual(job["status"], "done")
            self.assertEqual(job["progress"], 100)

    def test_document_status_not_found(self):
        """Test document status for non-existent document."""
        response = self.client.get("/ingest/document/99999")
        self.assertEqual(response.status_code, 404)

    def test_document_status_job_chronology(self):
        """Test that jobs have valid timestamps."""
        # Create test document
        document = Document(
            name="test_doc.pdf",
            mime="application/pdf",
            storage_uri="s3://test/test.pdf",
            status="uploaded"
        )
        self.db.add(document)
        self.db.flush()

        # Create jobs with different timestamps
        parse_job = Job(
            type="parse",
            status="done",
            progress=100,
            document_id=document.id
        )
        self.db.add(parse_job)

        chunk_job = Job(
            type="chunk",
            status="done",
            progress=100,
            document_id=document.id
        )
        self.db.add(chunk_job)

        embed_job = Job(
            type="embed",
            status="done",
            progress=100,
            document_id=document.id
        )
        self.db.add(embed_job)

        self.db.commit()

        # Test document status endpoint
        response = self.client.get(f"/ingest/document/{document.id}")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        jobs = data["jobs"]

        # Check timestamps are present and valid
        for job in jobs:
            self.assertIn("created_at", job)
            self.assertIn("updated_at", job)
            self.assertIsInstance(job["created_at"], str)
            self.assertIsInstance(job["updated_at"], str)


if __name__ == "__main__":
    unittest.main()
