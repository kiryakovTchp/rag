"""Test answer orchestrator."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from services.answer.orchestrator import AnswerOrchestrator
from db.models import Chunk, Document


class TestAnswerOrchestrator(unittest.TestCase):
    """Test answer orchestrator functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=Session)
        
        # Mock all dependencies to avoid external connections
        with patch('services.answer.orchestrator.PGVectorIndex') as mock_index_class, \
             patch('services.answer.orchestrator.get_llm_provider') as mock_get_llm, \
             patch('services.answer.orchestrator.EmbeddingProvider') as mock_embedder_class, \
             patch('services.answer.orchestrator.WorkersAIReranker') as mock_reranker_class, \
             patch('services.answer.orchestrator.AnswerCache') as mock_cache_class:
            
            self.mock_index = Mock()
            self.mock_llm = Mock()
            self.mock_embedder = Mock()
            self.mock_reranker = Mock()
            self.mock_cache = Mock()
            
            mock_index_class.return_value = self.mock_index
            mock_get_llm.return_value = self.mock_llm
            mock_embedder_class.return_value = self.mock_embedder
            mock_reranker_class.return_value = self.mock_reranker
            mock_cache_class.return_value = self.mock_cache
            
            self.orchestrator = AnswerOrchestrator(self.mock_db)
    
    def test_generate_answer_success(self):
        """Test successful answer generation."""
        # Mock dependencies
        self.mock_llm.generate.return_value = ("Test answer", {"provider": "gemini", "model": "test"})
        
        self.mock_embedder.embed_single.return_value = [0.1] * 1024
        
        self.mock_index.search.return_value = [(1, 0.8), (2, 0.7)]
        
        # Mock database query
        mock_chunks = [
            Chunk(id=1, document_id=1, text="Test chunk 1", page=1),
            Chunk(id=2, document_id=1, text="Test chunk 2", page=2)
        ]
        self.mock_db.query.return_value.filter.return_value.in_.return_value.all.return_value = mock_chunks
        
        # Test
        result = self.orchestrator.generate_answer("Test query")
        
        # Verify
        self.assertEqual(result["answer"], "Test answer")
        self.assertEqual(len(result["citations"]), 2)
        self.assertEqual(result["usage"]["provider"], "gemini")
        
        # Verify LLM was called
        self.mock_llm.generate.assert_called_once()
        call_args = self.mock_llm.generate.call_args
        self.assertEqual(call_args[1]["model"], "gemini-2.5-flash")
    
    def test_generate_answer_no_context(self):
        """Test answer generation with no relevant context."""
        # Mock dependencies
        self.mock_embedder.embed_single.return_value = [0.1] * 1024
        
        self.mock_index.search.return_value = []  # No results
        
        # Test
        with self.assertRaises(Exception) as cm:
            self.orchestrator.generate_answer("Test query")
        
        self.assertIn("No relevant context found", str(cm.exception))
    
    def test_generate_answer_with_rerank(self):
        """Test answer generation with reranking enabled."""
        # Mock dependencies
        self.mock_llm.generate.return_value = ("Test answer", {"provider": "gemini", "model": "test"})
        
        self.mock_embedder.embed_single.return_value = [0.1] * 1024
        
        self.mock_index.search.return_value = [(1, 0.8), (2, 0.7)]
        
        # Mock reranker
        self.orchestrator.reranker.rerank.return_value = [1, 0]  # Reorder chunks
        
        # Mock database query
        mock_chunks = [
            Chunk(id=1, document_id=1, text="Test chunk 1", page=1),
            Chunk(id=2, document_id=1, text="Test chunk 2", page=2)
        ]
        self.mock_db.query.return_value.filter.return_value.in_.return_value.all.return_value = mock_chunks
        
        # Test with rerank=True
        result = self.orchestrator.generate_answer("Test query", rerank=True)
        
        # Verify reranker was called
        self.orchestrator.reranker.rerank.assert_called_once()
        
        # Verify result
        self.assertEqual(result["answer"], "Test answer")
        self.assertEqual(len(result["citations"]), 2)
    
    def test_stream_answer(self):
        """Test streaming answer generation."""
        # Mock dependencies
        self.mock_llm.stream.return_value = ["Hello", " world", "!"]
        
        self.mock_embedder.embed_single.return_value = [0.1] * 1024
        
        self.mock_index.search.return_value = [(1, 0.8)]
        
        # Mock database query
        mock_chunks = [Chunk(id=1, document_id=1, text="Test chunk", page=1)]
        self.mock_db.query.return_value.filter.return_value.in_.return_value.all.return_value = mock_chunks
        
        # Test
        stream = self.orchestrator.stream_answer("Test query")
        chunks = list(stream)
        
        # Verify streaming
        self.assertEqual(len(chunks), 4)  # 3 text chunks + 1 done
        
        # Check text chunks
        text_chunks = [c for c in chunks if c["type"] == "chunk"]
        self.assertEqual(len(text_chunks), 3)
        self.assertEqual(text_chunks[0]["text"], "Hello")
        self.assertEqual(text_chunks[1]["text"], " world")
        self.assertEqual(text_chunks[2]["text"], "!")
        
        # Check final chunk
        done_chunk = [c for c in chunks if c["type"] == "done"][0]
        self.assertIn("citations", done_chunk)
        self.assertIn("usage", done_chunk)
    
    def test_generate_answer_with_tenant_logging(self):
        """Test answer generation with tenant logging."""
        # Mock dependencies
        self.mock_llm.generate.return_value = ("Test answer", {"provider": "gemini", "model": "test"})
        
        self.mock_embedder.embed_single.return_value = [0.1] * 1024
        
        self.mock_index.search.return_value = [(1, 0.8)]
        
        # Mock database query
        mock_chunks = [Chunk(id=1, document_id=1, text="Test chunk", page=1)]
        self.mock_db.query.return_value.filter.return_value.in_.return_value.all.return_value = mock_chunks
        
        # Mock logging
        with patch('services.answer.orchestrator.log_answer_usage') as mock_log:
            result = self.orchestrator.generate_answer("Test query", tenant_id="test_tenant")
            
                    # Verify logging was called
        mock_log.assert_called_once()
        call_args = mock_log.call_args
        self.assertEqual(call_args[1]["tenant_id"], "test_tenant")
        self.assertEqual(call_args[1]["query"], "Test query")

    def test_rerank_order_by_chunk_id(self):
        """Test that reranking preserves order by chunk_id, not list position."""
        # Mock dependencies
        self.mock_llm.generate.return_value = ("Test answer", {"provider": "gemini", "model": "test"})
        
        self.mock_embedder.embed_single.return_value = [0.1] * 1024
        
        # Mock search results with specific chunk IDs
        self.mock_index.search.return_value = [(10, 0.8), (5, 0.9), (15, 0.7)]  # chunk_id, score
        
        # Mock reranker to return reordered indices
        self.orchestrator.reranker.rerank.return_value = [1, 0, 2]  # Reorder: 2nd, 1st, 3rd
        
        # Mock database query - chunks in different order than search results
        mock_chunks = [
            Chunk(id=5, document_id=1, text="Second chunk", page=2),   # chunk_id=5
            Chunk(id=10, document_id=1, text="First chunk", page=1),   # chunk_id=10
            Chunk(id=15, document_id=1, text="Third chunk", page=3),   # chunk_id=15
        ]
        
        # Mock the entire query chain
        mock_query = Mock()
        mock_filter = Mock()
        mock_in = Mock()
        mock_all = Mock()
        
        mock_query.filter.return_value = mock_filter
        mock_filter.in_.return_value = mock_in
        mock_in.all.return_value = mock_chunks
        
        self.mock_db.query.return_value = mock_query
        
        # Mock cache to return None (no cache hit)
        self.mock_cache.get.return_value = None
        
        # Test with rerank=True
        result = self.orchestrator.generate_answer("Test query", rerank=True)
        
        # Verify reranker was called with correct pairs order
        self.orchestrator.reranker.rerank.assert_called_once()
        call_args = self.orchestrator.reranker.rerank.call_args
        pairs = call_args[0][0]  # First argument is pairs
        
        # Pairs should be in order of search_results: chunk_id 10, 5, 15
        self.assertEqual(pairs[0][1], "First chunk")   # chunk_id=10
        self.assertEqual(pairs[1][1], "Second chunk")  # chunk_id=5
        self.assertEqual(pairs[2][1], "Third chunk")   # chunk_id=15
        
        # Verify reranked chunks are in correct order based on reranker indices
        # reranker returned [1, 0, 2], so order should be: pairs[1], pairs[0], pairs[2]
        # This means: chunk_id=5, chunk_id=10, chunk_id=15
        # The first chunk in context should be chunk_id=5 ("Second chunk")
        # We can't directly test this without mocking build_messages, but we can verify
        # that reranker was called with the correct pairs order


if __name__ == "__main__":
    unittest.main()
