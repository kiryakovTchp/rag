"""Test context builder functionality."""

import unittest

from services.retrieve.context_builder import ContextBuilder
from services.retrieve.types import ChunkWithScore


class TestContextBuilder(unittest.TestCase):
    """Test context builder functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.builder = ContextBuilder()
    
    def test_remove_duplicates(self):
        """Test duplicate removal."""
        matches = [
            ChunkWithScore(
                chunk_id=1,
                doc_id=1,
                page=1,
                score=0.9,
                snippet="First chunk",
                breadcrumbs=["H1"]
            ),
            ChunkWithScore(
                chunk_id=2,
                doc_id=1,
                page=1,
                score=0.8,
                snippet="Second chunk",
                breadcrumbs=["H1"]  # Same breadcrumbs
            ),
            ChunkWithScore(
                chunk_id=3,
                doc_id=1,
                page=2,
                score=0.7,
                snippet="Third chunk",
                breadcrumbs=["H2"]
            )
        ]
        
        result = self.builder.build(matches, max_ctx_tokens=1000)
        
        # Should remove duplicate with same breadcrumbs
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["chunk_id"], 1)  # Higher score
        self.assertEqual(result[1]["chunk_id"], 3)
    
    def test_token_limit(self):
        """Test token limit enforcement."""
        # Create chunks with known token counts
        long_text = "This is a very long text that should exceed the token limit. " * 50
        
        matches = [
            ChunkWithScore(
                chunk_id=1,
                doc_id=1,
                page=1,
                score=0.9,
                snippet=long_text,
                breadcrumbs=["H1"]
            ),
            ChunkWithScore(
                chunk_id=2,
                doc_id=1,
                page=1,
                score=0.8,
                snippet="Short text",
                breadcrumbs=["H2"]
            )
        ]
        
        result = self.builder.build(matches, max_ctx_tokens=50)
        
        # Should respect token limit
        total_tokens = sum(self.builder.token_splitter.count_tokens(match["snippet"]) for match in result)
        self.assertLessEqual(total_tokens, 50)
    
    def test_max_chunks_limit(self):
        """Test maximum chunks limit."""
        matches = []
        for i in range(10):
            matches.append(ChunkWithScore(
                chunk_id=i,
                doc_id=1,
                page=1,
                score=0.9 - i * 0.1,
                snippet=f"Chunk {i}",
                breadcrumbs=[f"H{i}"]
            ))
        
        result = self.builder.build(matches, max_ctx_tokens=1000)
        
        # Should limit to 6 chunks
        self.assertLessEqual(len(result), 6)
    
    def test_merge_neighbors(self):
        """Test merging neighboring chunks."""
        matches = [
            ChunkWithScore(
                chunk_id=1,
                doc_id=1,
                page=1,
                score=0.9,
                snippet="First chunk",
                breadcrumbs=["H1"]
            ),
            ChunkWithScore(
                chunk_id=2,
                doc_id=1,
                page=1,
                score=0.8,
                snippet="Second chunk",
                breadcrumbs=["H1"]
            ),
            ChunkWithScore(
                chunk_id=3,
                doc_id=1,
                page=2,
                score=0.7,
                snippet="Third chunk",
                breadcrumbs=["H2"]
            )
        ]
        
        result = self.builder.build(matches, max_ctx_tokens=1000)
        
        # Should merge chunks from same page
        self.assertEqual(len(result), 2)
        
        # First result should be merged
        self.assertIn("First chunk", result[0]["snippet"])
        self.assertIn("Second chunk", result[0]["snippet"])
