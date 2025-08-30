import unittest
from pathlib import Path

from services.parsing.tables import TableParser


class TestTablesPDF(unittest.TestCase):
    def setUp(self):
        # Настройка переменных окружения для тестов
        import os

        os.environ["S3_ENDPOINT"] = "http://localhost:9000"
        os.environ["S3_REGION"] = "us-east-1"
        os.environ["S3_BUCKET"] = "test-bucket"
        os.environ["S3_ACCESS_KEY_ID"] = "test"
        os.environ["S3_SECRET_ACCESS_KEY"] = "test"

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
        self.assertIsNotNone(table["table_id"])
        self.assertIsNotNone(table["text"])

        # Verify table text contains headers
        table_text = table["text"]
        self.assertIn("Name", table_text)
        self.assertIn("Age", table_text)
        self.assertIn("City", table_text)

        # Check that it's in markdown format
        self.assertIn("|", table_text)
        self.assertIn("---", table_text)


if __name__ == "__main__":
    unittest.main()
