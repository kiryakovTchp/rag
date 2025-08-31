"""Test rate limiting functionality."""

import unittest
import time
from unittest.mock import Mock, patch
from fastapi import HTTPException

from api.middleware.rate_limit import check_rate_limit, check_daily_quota, update_quota_usage


class TestRateLimit(unittest.TestCase):
    """Test rate limiting functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_request = Mock()
        self.mock_request.headers = {}
    
    @patch('api.middleware.rate_limit.redis_client')
    @patch.dict('os.environ', {'RATE_LIMIT_PER_MIN': '5'})
    def test_rate_limit_under_limit(self, mock_redis):
        """Test rate limit when under the limit."""
        # Mock Redis to return current count under limit
        mock_redis.get.return_value = b"3"  # 3 requests so far
        
        # Should not raise exception
        try:
            check_rate_limit(self.mock_request, "test_user")
        except HTTPException:
            self.fail("Rate limit should not be exceeded")
        
        # Should increment counter
        mock_redis.incr.assert_called_once()
        mock_redis.expire.assert_called_once_with(mock_redis.incr.return_value, 60)
    
    @patch('api.middleware.rate_limit.redis_client')
    @patch.dict('os.environ', {'RATE_LIMIT_PER_MIN': '5'})
    def test_rate_limit_exceeded(self, mock_redis):
        """Test rate limit when exceeded."""
        # Mock Redis to return current count at limit
        mock_redis.get.return_value = b"5"  # 5 requests (at limit)
        
        # Should raise exception
        with self.assertRaises(HTTPException) as context:
            check_rate_limit(self.mock_request, "test_user")
        
        self.assertEqual(context.exception.status_code, 429)
        self.assertIn("Rate limit exceeded", context.exception.detail)
    
    @patch('api.middleware.rate_limit.redis_client')
    @patch.dict('os.environ', {'RATE_LIMIT_PER_MIN': '5'})
    def test_rate_limit_first_request(self, mock_redis):
        """Test rate limit on first request."""
        # Mock Redis to return None (no previous requests)
        mock_redis.get.return_value = None
        
        # Should not raise exception
        try:
            check_rate_limit(self.mock_request, "test_user")
        except HTTPException:
            self.fail("Rate limit should not be exceeded on first request")
        
        # Should increment counter
        mock_redis.incr.assert_called_once()
    
    @patch('api.middleware.rate_limit.redis_client')
    @patch.dict('os.environ', {'DAILY_TOKEN_QUOTA': '1000'})
    def test_daily_quota_under_limit(self, mock_redis):
        """Test daily quota when under the limit."""
        # Mock Redis to return current usage under quota
        mock_redis.get.return_value = b"500"  # 500 tokens used
        
        # Should not raise exception
        try:
            check_daily_quota("test_tenant", 400)  # 400 more tokens
        except HTTPException:
            self.fail("Daily quota should not be exceeded")
        
        # Should increment usage
        mock_redis.incrby.assert_called_once()
        mock_redis.expire.assert_called_once_with(mock_redis.incrby.return_value, 86400)
    
    @patch('api.middleware.rate_limit.redis_client')
    @patch.dict('os.environ', {'DAILY_TOKEN_QUOTA': '1000'})
    def test_daily_quota_exceeded(self, mock_redis):
        """Test daily quota when exceeded."""
        # Mock Redis to return current usage that would exceed quota
        mock_redis.get.return_value = b"800"  # 800 tokens used
        
        # Should raise exception
        with self.assertRaises(HTTPException) as context:
            check_daily_quota("test_tenant", 300)  # 300 more tokens = 1100 total
        
        self.assertEqual(context.exception.status_code, 402)
        self.assertIn("Daily token quota exceeded", context.exception.detail)
    
    @patch('api.middleware.rate_limit.redis_client')
    @patch.dict('os.environ', {'DAILY_TOKEN_QUOTA': '1000'})
    def test_daily_quota_first_usage(self, mock_redis):
        """Test daily quota on first usage."""
        # Mock Redis to return None (no previous usage)
        mock_redis.get.return_value = None
        
        # Should not raise exception
        try:
            check_daily_quota("test_tenant", 500)
        except HTTPException:
            self.fail("Daily quota should not be exceeded on first usage")
        
        # Should increment usage
        mock_redis.incrby.assert_called_once()
    
    @patch('api.middleware.rate_limit.redis_client')
    def test_update_quota_usage(self, mock_redis):
        """Test updating quota usage."""
        # Should increment usage
        update_quota_usage("test_tenant", 100)
        
        mock_redis.incrby.assert_called_once()
        mock_redis.expire.assert_called_once_with(mock_redis.incrby.return_value, 86400)
    
    @patch('api.middleware.rate_limit.redis_client')
    def test_redis_unavailable_rate_limit(self, mock_redis):
        """Test rate limit when Redis is unavailable."""
        # Mock Redis to raise exception
        mock_redis.get.side_effect = Exception("Redis unavailable")
        
        # Should not raise exception (graceful degradation)
        try:
            check_rate_limit(self.mock_request, "test_user")
        except Exception as e:
            if "Redis unavailable" in str(e):
                self.fail("Should handle Redis unavailability gracefully")
    
    @patch('api.middleware.rate_limit.redis_client')
    def test_redis_unavailable_quota(self, mock_redis):
        """Test daily quota when Redis is unavailable."""
        # Mock Redis to raise exception
        mock_redis.get.side_effect = Exception("Redis unavailable")
        
        # Should not raise exception (graceful degradation)
        try:
            check_daily_quota("test_tenant", 100)
        except Exception as e:
            if "Redis unavailable" in str(e):
                self.fail("Should handle Redis unavailability gracefully")


if __name__ == "__main__":
    unittest.main()
