"""Test answer caching functionality."""

import unittest
import redis
from unittest.mock import Mock, patch
from services.cache.answers import AnswerCache


class TestAnswerCache(unittest.TestCase):
    """Test answer caching functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        with patch('services.cache.answers.redis.from_url') as mock_redis:
            self.mock_redis = Mock()
            mock_redis.return_value = self.mock_redis
            self.cache = AnswerCache()
    
    def test_generate_key_consistency(self):
        """Test that cache key generation is consistent."""
        # Same parameters should generate same key
        key1 = self.cache._generate_key("tenant1", "query", 10, False, 2000, "model1")
        key2 = self.cache._generate_key("tenant1", "query", 10, False, 2000, "model1")
        self.assertEqual(key1, key2)
        
        # Different parameters should generate different keys
        key3 = self.cache._generate_key("tenant2", "query", 10, False, 2000, "model1")
        self.assertNotEqual(key1, key3)
        
        key4 = self.cache._generate_key("tenant1", "different query", 10, False, 2000, "model1")
        self.assertNotEqual(key1, key4)
    
    def test_get_cached_answer(self):
        """Test getting cached answer."""
        cached_data = {
            "answer": "Test answer",
            "citations": [{"doc_id": 1, "chunk_id": 1, "score": 0.8}],
            "usage": {"latency_ms": 100, "provider": "gemini"},
            "tenant_id": "tenant1"
        }
        
        self.mock_redis.get.return_value = '{"answer": "Test answer", "citations": [{"doc_id": 1, "chunk_id": 1, "score": 0.8}], "usage": {"latency_ms": 100, "provider": "gemini"}, "tenant_id": "tenant1"}'
        
        result = self.cache.get("tenant1", "query", 10, False, 2000, "model1")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["answer"], "Test answer")
        self.assertEqual(result["usage"]["latency_ms"], 0)  # Cache hit
    
    def test_get_no_cache(self):
        """Test getting answer when not cached."""
        self.mock_redis.get.return_value = None
        
        result = self.cache.get("tenant1", "query", 10, False, 2000, "model1")
        
        self.assertIsNone(result)
    
    def test_set_cache(self):
        """Test setting cache."""
        answer = "Test answer"
        citations = [{"doc_id": 1, "chunk_id": 1, "score": 0.8}]
        usage = {"latency_ms": 100, "provider": "gemini"}
        
        self.cache.set("tenant1", "query", 10, False, 2000, "model1", answer, citations, usage)
        
        # Verify redis.setex was called
        self.mock_redis.setex.assert_called_once()
        call_args = self.mock_redis.setex.call_args
        
        # Check TTL
        self.assertEqual(call_args[0][1], 300)  # Default TTL
        
        # Check data contains tenant_id
        cached_data = eval(call_args[0][2])  # Parse JSON string
        self.assertEqual(cached_data["tenant_id"], "tenant1")
    
    def test_invalidate_tenant(self):
        """Test invalidating cache for specific tenant."""
        # Mock keys
        self.mock_redis.keys.return_value = ["answer:key1", "answer:key2", "answer:key3"]
        
        # Mock cached data for different tenants
        self.mock_redis.get.side_effect = [
            '{"tenant_id": "tenant1", "answer": "test1"}',
            '{"tenant_id": "tenant2", "answer": "test2"}',
            '{"tenant_id": "tenant1", "answer": "test3"}'
        ]
        
        self.cache.invalidate_tenant("tenant1")
        
        # Should delete keys for tenant1 only
        self.assertEqual(self.mock_redis.delete.call_count, 2)
        
        # Verify the correct keys were deleted
        delete_calls = self.mock_redis.delete.call_args_list
        self.assertIn("answer:key1", [call[0][0] for call in delete_calls])
        self.assertIn("answer:key3", [call[0][0] for call in delete_calls])
    
    def test_invalidate_tenant_no_matches(self):
        """Test invalidating cache when no matches found."""
        self.mock_redis.keys.return_value = ["answer:key1"]
        self.mock_redis.get.return_value = '{"tenant_id": "tenant2", "answer": "test"}'
        
        self.cache.invalidate_tenant("tenant1")
        
        # Should not delete any keys
        self.mock_redis.delete.assert_not_called()
    
    def test_cache_redis_error_handling(self):
        """Test that Redis errors are handled gracefully."""
        # Test get with Redis error
        self.mock_redis.get.side_effect = redis.RedisError("Redis error")
        
        result = self.cache.get("tenant1", "query", 10, False, 2000, "model1")
        self.assertIsNone(result)
        
        # Reset side effect
        self.mock_redis.get.side_effect = None
        
        # Test set with Redis error
        self.mock_redis.setex.side_effect = redis.RedisError("Redis error")
        
        # Should not raise exception
        try:
            self.cache.set("tenant1", "query", 10, False, 2000, "model1", "answer", [], {})
        except Exception:
            self.fail("Cache.set should handle Redis errors gracefully")


if __name__ == "__main__":
    unittest.main()
