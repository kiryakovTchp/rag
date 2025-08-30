import unittest
from pathlib import Path

from services.parsing.tables import TableParser


class TestTablesPDF(unittest.TestCase):
    def setUp(self):
        # Настройка переменных окружения для тестов
        import os

        os.environ["S3_ENDPOINT"] = "http://localhost:9000"
        os.environ["S3_REGION"] = "us-east-1"
        os.environ["S3_BUCKET"] = "promoai"
        os.environ["S3_ACCESS_KEY_ID"] = "minio"
        os.environ["S3_SECRET_ACCESS_KEY"] = "minio123"

        self.table_parser = TableParser()
        self.fixture_path = Path(__file__).parent / "fixtures" / "table.pdf"

    def test_table_extraction_from_pdf(self):
        """Test that tables are extracted from PDF and headers are repeated in chunks."""
        # Extract tables from PDF
        tables = self.table_parser.extract_tables(str(self.fixture_path), "application/pdf")

        # Should find at least one table
        self.assertGreater(len(tables), 0)

        # Check table structure
        table = tables[0]
        self.assertEqual(table["type"], "table")
        self.assertIn("table_id", table)
        self.assertIn("text", table)

        # Test that table text contains markdown format
        table_text = table["text"]
        self.assertIn("|", table_text)  # Should contain pipe separators
        self.assertIn("---", table_text)  # Should contain separator line

        # Test chunking of table
        from services.chunking.pipeline import ChunkingPipeline

        chunking_pipeline = ChunkingPipeline()

        # Create element with table
        element = {
            "id": 1,
            "type": "table",
            "text": table_text,
            "page": 1,
            "table_id": table["table_id"],
        }

        chunks = chunking_pipeline.build_chunks([element])

        # Should create at least one table chunk
        self.assertGreater(len(chunks), 0)

        # Check that first chunk is table type
        table_chunk = chunks[0]
        self.assertEqual(table_chunk["level"], "table")
        self.assertIn("table_meta", table_chunk)

        # Check that header is repeated in chunk
        chunk_text = table_chunk["text"]
        lines = chunk_text.split("\n")
        self.assertGreaterEqual(len(lines), 3)  # Header + separator + at least 1 row

        # First line should be header
        header_line = lines[0]
        self.assertIn("|", header_line)

        # Second line should be separator
        separator_line = lines[1]
        self.assertIn("---", separator_line)


if __name__ == "__main__":
    unittest.main()
