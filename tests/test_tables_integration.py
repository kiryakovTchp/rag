import time
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app
from db.models import Chunk, Document, Element
from db.session import SessionLocal


class TestTablesIntegration(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.db = SessionLocal()
        self.fixture_path = Path(__file__).parent / "fixtures" / "table.pdf"

    def tearDown(self):
        self.db.close()

    def test_table_ingest_pipeline(self):
        """Test table extraction through full ingest pipeline."""
        # Upload PDF with tables
        with open(self.fixture_path, "rb") as f:
            response = self.client.post(
                "/ingest",
                files={"file": ("table.pdf", f, "application/pdf")},
                data={"tenant_id": "test", "safe_mode": "false"}
            )

        self.assertEqual(response.status_code, 200)
        job_id = response.json()["job_id"]

        # Poll for job completion
        max_attempts = 90  # 90 seconds timeout for table processing
        for attempt in range(max_attempts):
            response = self.client.get(f"/ingest/{job_id}")
            self.assertEqual(response.status_code, 200)

            job_status = response.json()
            if job_status["status"] == "done":
                print(f"✅ Table job completed in {attempt + 1} seconds")
                break
            elif job_status["status"] == "error":
                self.fail(f"Job failed: {job_status.get('error', 'Unknown error')}")

            time.sleep(1)
        else:
            self.fail(f"Job did not complete within {max_attempts} seconds")

        # Verify database records
        document = self.db.query(Document).filter(Document.id == job_status["document_id"]).first()
        self.assertIsNotNone(document)

        # Check table elements
        table_elements = self.db.query(Element).filter(
            Element.document_id == document.id,
            Element.type == "table"
        ).all()
        
        self.assertGreater(len(table_elements), 0, "Should have at least one table element")

        # Check table chunks
        table_chunks = self.db.query(Chunk).filter(
            Chunk.document_id == document.id,
            Chunk.level == "table"
        ).all()
        
        self.assertGreater(len(table_chunks), 0, "Should have at least one table chunk")

        # Check that table chunks have headers repeated
        for chunk in table_chunks:
            self.assertIsNotNone(chunk.table_meta)
            chunk_text = chunk.text
            
            # Should contain markdown table format
            self.assertIn("|", chunk_text)
            self.assertIn("---", chunk_text)
            
            # Should have header repeated
            lines = chunk_text.split("\n")
            self.assertGreaterEqual(len(lines), 3)  # Header + separator + at least 1 row
            
            # First line should be header
            header_line = lines[0]
            self.assertIn("|", header_line)
            
            # Second line should be separator
            separator_line = lines[1]
            self.assertIn("---", separator_line)
            
            # Should have some data rows
            data_lines = [line for line in lines[2:] if line.strip() and "|" in line]
            self.assertGreater(len(data_lines), 0, "Should have data rows")


if __name__ == "__main__":
    unittest.main()
