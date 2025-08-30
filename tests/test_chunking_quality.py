import re
import unittest

from services.chunking.pipeline import ChunkingPipeline


class TestChunkingQuality(unittest.TestCase):
    def setUp(self):
        self.chunking_pipeline = ChunkingPipeline()

    def test_text_continuity_after_chunk(self):
        """Test that no useful text is lost during parsing and chunking."""
        # Create test elements
        elements = [
            {
                "type": "h1",
                "text": "Test Document",
                "page": 1,
                "bbox": None,
            },
            {
                "type": "text",
                "text": "This is a test paragraph with some content. "
                "It should be preserved during chunking.",
                "page": 1,
                "bbox": None,
            },
            {
                "type": "text",
                "text": "Another paragraph with more content to test continuity.",
                "page": 1,
                "bbox": None,
            },
        ]

        # Build chunks
        chunks = self.chunking_pipeline.build_chunks(elements)

        # Extract all text from elements
        original_text = " ".join(e["text"] for e in elements)
        original_text = self._normalize_text(original_text)

        # Extract all text from chunks
        chunked_text = " ".join(chunk["text"] for chunk in chunks)
        chunked_text = self._normalize_text(chunked_text)

        # Check that chunked text covers original text
        # Allow for minor differences in whitespace and formatting
        original_words = set(original_text.lower().split())
        chunked_words = set(chunked_text.lower().split())

        # At least 95% of original words should be preserved
        preserved_words = original_words.intersection(chunked_words)
        preservation_rate = len(preserved_words) / len(original_words)

        self.assertGreaterEqual(
            preservation_rate, 0.95, f"Text preservation rate {preservation_rate:.2%} is too low"
        )

    def test_table_header_repetition(self):
        """Test that table headers are repeated in each chunk."""
        # Create table element
        table_text = """|Name|Age|City|
|---|---|---|
|John|25|New York|
|Jane|30|London|
|Bob|35|Paris|
|Alice|28|Berlin|"""

        elements = [
            {
                "type": "table",
                "text": table_text,
                "page": 1,
                "bbox": None,
                "table_id": "test_table",
            }
        ]

        # Build chunks
        chunks = self.chunking_pipeline.build_chunks(elements)

        # Find table chunks
        table_chunks = [c for c in chunks if c["level"] == "table"]
        self.assertGreater(len(table_chunks), 0)

        # Check that each table chunk contains headers
        headers = ["Name", "Age", "City"]
        for chunk in table_chunks:
            chunk_text = chunk["text"]
            for header in headers:
                self.assertIn(header, chunk_text, f"Header '{header}' missing from table chunk")

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove hyphens at line breaks
        text = re.sub(r"(\w+)-\s+(\w+)", r"\1\2", text)
        return text.strip()


if __name__ == "__main__":
    unittest.main()
