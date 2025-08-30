import os
import tempfile
import time
import unittest
from io import BytesIO

from fastapi.testclient import TestClient

from api.main import app
from db.models import Chunk, Document, Element
from db.session import SessionLocal
from storage.r2 import ObjectStore


class TestIntegration(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.client = TestClient(app)
        self.db = SessionLocal()
        self.storage = ObjectStore()

    def tearDown(self):
        """Clean up test environment."""
        self.db.close()

    def test_full_ingest_pipeline(self):
        """Test complete ingest → parse → chunk pipeline."""
        # Create test PDF content
        test_content = b"""
        %PDF-1.4
        1 0 obj
        <<
        /Type /Catalog
        /Pages 2 0 R
        >>
        endobj
        
        2 0 obj
        <<
        /Type /Pages
        /Kids [3 0 R]
        /Count 1
        >>
        endobj
        
        3 0 obj
        <<
        /Type /Page
        /Parent 2 0 R
        /MediaBox [0 0 612 792]
        /Contents 4 0 R
        >>
        endobj
        
        4 0 obj
        <<
        /Length 44
        >>
        stream
        BT
        /F1 12 Tf
        72 720 Td
        (Test Document) Tj
        ET
        endstream
        endobj
        
        xref
        0 5
        0000000000 65535 f 
        0000000009 00000 n 
        0000000058 00000 n 
        0000000115 00000 n 
        0000000204 00000 n 
        trailer
        <<
        /Size 5
        /Root 1 0 R
        >>
        startxref
        272
        %%EOF
        """

        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(test_content)
            temp_file_path = f.name

        try:
            # Upload document via API
            with open(temp_file_path, "rb") as f:
                response = self.client.post(
                    "/ingest",
                    files={"file": ("test.pdf", f, "application/pdf")},
                    data={"tenant_id": "test", "safe_mode": False},
                )

            # Check response
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("job_id", data)
            job_id = data["job_id"]

            # Poll job status until done
            max_attempts = 30
            attempt = 0
            while attempt < max_attempts:
                response = self.client.get(f"/ingest/{job_id}")
                self.assertEqual(response.status_code, 200)

                job_data = response.json()
                status = job_data["status"]
                progress = job_data["progress"]

                print(f"Job {job_id}: status={status}, progress={progress}%")

                if status == "done":
                    break
                elif status == "error":
                    self.fail(f"Job failed with error: {job_data.get('error')}")

                time.sleep(2)  # Wait 2 seconds before next poll
                attempt += 1

            # Check that job completed successfully
            self.assertEqual(job_data["status"], "done")
            self.assertEqual(job_data["progress"], 100)

            # Check database records
            document = (
                self.db.query(Document).filter(Document.id == job_data["document_id"]).first()
            )
            self.assertIsNotNone(document)
            self.assertEqual(document.status, "done")

            # Check elements were created
            elements = self.db.query(Element).filter(Element.document_id == document.id).all()
            self.assertGreater(len(elements), 0, "No elements created")

            # Check chunks were created
            chunks = self.db.query(Chunk).filter(Chunk.document_id == document.id).all()
            self.assertGreater(len(chunks), 0, "No chunks created")

            # Check that chunks have proper metadata
            for chunk in chunks:
                self.assertIsNotNone(chunk.text)
                self.assertGreater(chunk.token_count, 0)
                self.assertIsNotNone(chunk.level)

            print("✅ Pipeline completed successfully:")
            print(f"   - Document: {document.name}")
            print(f"   - Elements: {len(elements)}")
            print(f"   - Chunks: {len(chunks)}")

        finally:
            # Clean up
            os.unlink(temp_file_path)

    def test_storage_integration(self):
        """Test S3 storage integration."""
        test_key = "test/integration_test.txt"
        test_content = b"Integration test content"

        try:
            # Upload test content
            data_stream = BytesIO(test_content)
            s3_uri = self.storage.put_data(data_stream, test_key)
            self.assertTrue(s3_uri.startswith("s3://"))

            # Check file exists
            self.assertTrue(self.storage.exists(test_key))

            # Download and verify content
            downloaded_content = self.storage.get_data(test_key)
            self.assertEqual(downloaded_content, test_content)

            print("✅ Storage integration test passed")

        finally:
            # Clean up
            self.storage.delete(test_key)


if __name__ == "__main__":
    unittest.main()
