"""Test prompt builder."""

import unittest

from db.models import Chunk
from services.prompt.answer import build_messages


class TestPromptBuilder(unittest.TestCase):
    """Test prompt building functionality."""

    def test_build_messages_with_context(self):
        """Test building messages with context chunks."""
        query = "What is RAG?"

        # Create test chunks
        chunks = [
            Chunk(
                id=1,
                document_id=1,
                text="RAG stands for Retrieval-Augmented Generation.",
                page=1,
            ),
            Chunk(
                id=2,
                document_id=1,
                text="It combines retrieval with generation for better answers.",
                page=2,
            ),
        ]

        messages, remaining_tokens = build_messages(query, chunks, max_ctx_tokens=1000)

        # Check messages structure
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["role"], "user")

        content = messages[0]["content"]

        # Check system instructions are present
        self.assertIn("Отвечай кратко и только по данным из контекста", content)
        self.assertIn("цитируй источники в тексте в формате [doc:", content)
        self.assertIn("Не найдено в источниках", content)

        # Check context is included
        self.assertIn("RAG stands for Retrieval-Augmented Generation", content)
        self.assertIn("It combines retrieval with generation", content)

        # Check citations are formatted
        self.assertIn("[doc:1 chunk:1 page:1]", content)
        self.assertIn("[doc:1 chunk:2 page:2]", content)

        # Check query is included
        self.assertIn("Вопрос: What is RAG?", content)

        # Check remaining tokens
        self.assertGreater(remaining_tokens, 0)

    def test_build_messages_respects_token_limit(self):
        """Test that messages respect token limits."""
        query = "Short query"

        # Create many chunks to exceed limit
        chunks = []
        for i in range(20):
            chunks.append(
                Chunk(
                    id=i,
                    document_id=1,
                    text="This is a very long chunk text that will consume many tokens "
                    * 10,
                    page=1,
                )
            )

        messages, remaining_tokens = build_messages(query, chunks, max_ctx_tokens=500)

        # Should not include all chunks due to token limit
        content = messages[0]["content"]
        chunk_count = content.count("[doc:1 chunk:")
        self.assertLess(chunk_count, 20)

        # Remaining tokens should be small or negative
        self.assertLess(remaining_tokens, 100)

    def test_build_messages_empty_context(self):
        """Test building messages with empty context."""
        query = "Test query"
        chunks = []

        messages, remaining_tokens = build_messages(query, chunks, max_ctx_tokens=1000)

        content = messages[0]["content"]
        self.assertIn("Контекст:", content)
        self.assertIn("Вопрос: Test query", content)
        self.assertGreater(remaining_tokens, 0)

    def test_build_messages_cleanup_text(self):
        """Test that chunk text is properly cleaned."""
        query = "Test"

        chunks = [Chunk(id=1, document_id=1, text="  \n\n  Clean text  \n\n  ", page=1)]

        messages, _ = build_messages(query, chunks, max_ctx_tokens=1000)
        content = messages[0]["content"]

        # Should not have excessive whitespace
        self.assertNotIn("  \n\n  ", content)
        self.assertIn("Clean text", content)


if __name__ == "__main__":
    unittest.main()
