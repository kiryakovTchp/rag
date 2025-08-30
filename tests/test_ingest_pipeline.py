import time
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app
from db.models import Chunk, Document, Element
from db.session import SessionLocal


class TestIngestPipeline(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.db = SessionLocal()
        self.fixture_path = Path(__file__).parent / "fixtures" / "simple.pdf"

    def tearDown(self):
        self.db.close()

    def test_full_ingest_pipeline(self):
        """Test complete ingest pipeline: upload -> parse -> chunk."""
        # Upload PDF
        with open(self.fixture_path, "rb") as f:
            response = self.client.post(
                "/ingest",
                files={"file": ("test.pdf", f, "application/pdf")},
            )

        self.assertEqual(response.status_code, 200)
        job_id = response.json()["job_id"]

        # Poll for job completion
        max_attempts = 30
        for _ in range(max_attempts):
            response = self.client.get(f"/ingest/{job_id}")
            self.assertEqual(response.status_code, 200)

            job_status = response.json()
            if job_status["status"] == "done":
                break
            elif job_status["status"] == "error":
                self.fail(f"Job failed: {job_status.get('error', 'Unknown error')}")

            time.sleep(1)
        else:
            self.fail("Job did not complete within expected time")

        # Verify database records
        document = self.db.query(Document).filter(Document.id == job_status["document_id"]).first()
        self.assertIsNotNone(document)
        self.assertEqual(document.status, "done")

        # Check elements
        elements = self.db.query(Element).filter(Element.document_id == document.id).all()
        self.assertGreater(len(elements), 0)

        element_types = [e.type for e in elements]
        self.assertTrue(any(t in ["title", "text"] for t in element_types))

        # Check chunks
        chunks = self.db.query(Chunk).filter(Chunk.document_id == document.id).all()
        self.assertGreater(len(chunks), 0)

        for chunk in chunks:
            self.assertGreater(chunk.token_count, 0)
            self.assertIsNotNone(chunk.page)
            self.assertIsNotNone(chunk.header_path)
            # header_path может быть пустым для простых документов без заголовков


if __name__ == "__main__":
    unittest.main()
