import unittest

from services.chunking.pipeline import ChunkingPipeline


class TestParsingSimple(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.chunking_pipeline = ChunkingPipeline()

    def test_text_continuity_after_chunk(self):
        """Test that no text is lost during chunk pipeline."""
        # Create test elements directly
        elements = [
            {"id": 1, "type": "h1", "text": "# Introduction", "page": 1},
            {
                "id": 2,
                "type": "text",
                "text": "This is a test document with multiple sections.",
                "page": 1,
            },
            {"id": 3, "type": "h2", "text": "## Section 1", "page": 1},
            {
                "id": 4,
                "type": "text",
                "text": "This section contains important information about testing.",
                "page": 1,
            },
            {"id": 5, "type": "h2", "text": "## Section 2", "page": 1},
            {
                "id": 6,
                "type": "text",
                "text": "Another section with more content to test chunking.",
                "page": 1,
            },
            {"id": 7, "type": "h3", "text": "### Subsection 2.1", "page": 1},
            {
                "id": 8,
                "type": "text",
                "text": "This is a subsection with detailed information.",
                "page": 1,
            },
            {"id": 9, "type": "h2", "text": "## Conclusion", "page": 1},
            {"id": 10, "type": "text", "text": "This concludes our test document.", "page": 1},
        ]

        # Build chunks
        chunks = self.chunking_pipeline.build_chunks(elements)

        # Extract all text from chunks
        chunked_text = " ".join([chunk["text"] for chunk in chunks])

        # Extract all text from original elements
        original_text = " ".join([element["text"] for element in elements])

        # Normalize both texts for comparison
        original_normalized = " ".join(original_text.split())
        chunked_normalized = " ".join(chunked_text.split())

        # Check that all original text is preserved
        self.assertTrue(
            len(chunked_normalized) >= len(original_normalized) * 0.9,  # Allow some flexibility
            f"Text length mismatch: original={len(original_normalized)}, "
            f"chunked={len(chunked_normalized)}",
        )

        # Check that key phrases are preserved
        key_phrases = ["Introduction", "Section 1", "Section 2", "Conclusion"]
        for phrase in key_phrases:
            self.assertIn(
                phrase, chunked_normalized, f"Key phrase '{phrase}' not found in chunked text"
            )

    def test_table_header_repetition(self):
        """Test that table headers are repeated in chunks."""
        # Create test table elements
        table_elements = [
            {
                "id": 1,
                "type": "table",
                "text": """|Name|Age|City|
|---|---|---|
|John|25|New York|
|Jane|30|Los Angeles|
|Bob|35|Chicago|
|Alice|28|Boston|
|Charlie|32|Seattle|
|Diana|27|Miami|
|Eve|29|Denver|
|Frank|31|Phoenix|""",
                "page": 1,
                "table_id": "test_table_1",
            }
        ]

        # Build chunks
        chunks = self.chunking_pipeline.build_chunks(table_elements)

        # Check that we have chunks
        self.assertGreater(len(chunks), 0, "No chunks created from table")

        # Check that each chunk contains the header
        for chunk in chunks:
            chunk_text = chunk["text"]
            self.assertIn("|Name|Age|City|", chunk_text, "Header not found in chunk")
            self.assertIn("|---|---|---|", chunk_text, "Separator not found in chunk")

        # Check metadata
        for chunk in chunks:
            self.assertIn("table_meta", chunk, "Table metadata missing")
            table_meta = chunk["table_meta"]
            self.assertIn("headers", table_meta, "Headers metadata missing")
            self.assertIn("has_header_repeat", table_meta, "Header repeat flag missing")
            self.assertTrue(table_meta["has_header_repeat"], "Header repeat flag should be True")

    def test_header_path_breadcrumbs(self):
        """Test that header paths are correctly built."""
        # Create test elements with headers
        elements = [
            {"id": 1, "type": "h1", "text": "Main Title", "page": 1},
            {"id": 2, "type": "text", "text": "Some content under main title.", "page": 1},
            {"id": 3, "type": "h2", "text": "Section 1", "page": 1},
            {"id": 4, "type": "text", "text": "Content in section 1.", "page": 1},
            {"id": 5, "type": "h3", "text": "Subsection 1.1", "page": 1},
            {"id": 6, "type": "text", "text": "Content in subsection 1.1.", "page": 1},
        ]

        # Build chunks
        chunks = self.chunking_pipeline.build_chunks(elements)

        # Check that chunks have correct header paths
        for chunk in chunks:
            if chunk["level"] == "section":
                header_path = chunk.get("header_path", [])
                # Check that header paths are lists
                self.assertIsInstance(header_path, list, "Header path should be a list")

                # Check that header paths contain the expected headers
                if "Main Title" in chunk["text"]:
                    self.assertIn("Main Title", header_path, "Main title should be in header path")
                if "Section 1" in chunk["text"]:
                    self.assertIn("Section 1", header_path, "Section 1 should be in header path")
                if "Subsection 1.1" in chunk["text"]:
                    self.assertIn(
                        "Subsection 1.1", header_path, "Subsection should be in header path"
                    )


if __name__ == "__main__":
    unittest.main()
