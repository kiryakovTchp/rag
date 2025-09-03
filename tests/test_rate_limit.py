"""Test rate limiting and quota functionality."""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.middleware.rate_limit import QuotaLimiter, RateLimiter

client = TestClient(app)


class TestRateLimiter:
    """Test rate limiting functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rate_limiter = RateLimiter(requests_per_minute=5)

    @patch("api.middleware.rate_limit.redis_client")
    def test_rate_limit_allowed(self, mock_redis):
        """Test that requests are allowed within limit."""
        mock_redis.get.return_value = "2"  # 2 requests so far
        mock_redis.pipeline.return_value.execute.return_value = [3, True]

        result = self.rate_limiter.is_allowed("test_user")
        assert result is True

    @patch("api.middleware.rate_limit.redis_client")
    def test_rate_limit_exceeded(self, mock_redis):
        """Test that requests are blocked when limit exceeded."""
        mock_redis.get.return_value = "5"  # Already at limit

        result = self.rate_limiter.is_allowed("test_user")
        assert result is False

    @patch("api.middleware.rate_limit.redis_client")
    def test_rate_limit_redis_error(self, mock_redis):
        """Test that requests are allowed when Redis is down."""
        mock_redis.get.side_effect = Exception("Redis error")

        result = self.rate_limiter.is_allowed("test_user")
        assert result is True

    @patch("api.middleware.rate_limit.redis_client")
    def test_get_remaining(self, mock_redis):
        """Test getting remaining requests."""
        mock_redis.get.return_value = "3"  # 3 requests used

        remaining = self.rate_limiter.get_remaining("test_user")
        assert remaining == 2  # 5 - 3 = 2


class TestQuotaLimiter:
    """Test quota limiting functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.quota_limiter = QuotaLimiter(daily_token_quota=1000)

    @patch("api.middleware.rate_limit.redis_client")
    def test_quota_allowed(self, mock_redis):
        """Test that requests are allowed within quota."""
        mock_redis.get.return_value = "500"  # 500 tokens used
        mock_redis.pipeline.return_value.execute.return_value = [600, True]

        result = self.quota_limiter.check_quota("test_tenant", 100)
        assert result is True

    @patch("api.middleware.rate_limit.redis_client")
    def test_quota_exceeded(self, mock_redis):
        """Test that requests are blocked when quota exceeded."""
        mock_redis.get.return_value = "900"  # 900 tokens used

        result = self.quota_limiter.check_quota("test_tenant", 200)
        assert result is False

    @patch("api.middleware.rate_limit.redis_client")
    def test_quota_redis_error(self, mock_redis):
        """Test that requests are allowed when Redis is down."""
        mock_redis.get.side_effect = Exception("Redis error")

        result = self.quota_limiter.check_quota("test_tenant", 100)
        assert result is True

    @patch("api.middleware.rate_limit.redis_client")
    def test_get_remaining_quota(self, mock_redis):
        """Test getting remaining quota."""
        mock_redis.get.return_value = "600"  # 600 tokens used

        remaining = self.quota_limiter.get_remaining_quota("test_tenant")
        assert remaining == 400  # 1000 - 600 = 400


class TestRateLimitMiddleware:
    """Test rate limiting middleware."""

    @patch("api.middleware.rate_limit.rate_limiter")
    def test_rate_limit_middleware_allowed(self, mock_rate_limiter):
        """Test that middleware allows requests within limit."""
        mock_rate_limiter.is_allowed.return_value = True
        mock_rate_limiter.get_remaining.return_value = 3

        with patch("api.middleware.rate_limit.jwt") as mock_jwt:
            mock_jwt.decode.return_value = {"sub": "test_user"}

            response = client.get("/health")
            assert response.status_code == 200

    @patch("api.middleware.rate_limit.rate_limiter")
    def test_rate_limit_middleware_exceeded(self, mock_rate_limiter):
        """Test that middleware blocks requests when limit exceeded."""
        mock_rate_limiter.is_allowed.return_value = False
        mock_rate_limiter.get_remaining.return_value = 0

        with patch("api.middleware.rate_limit.jwt") as mock_jwt:
            mock_jwt.decode.return_value = {"sub": "test_user"}

            response = client.get("/health")
            assert response.status_code == 429
            assert "Rate limit exceeded" in response.json()["error"]

    def test_rate_limit_middleware_health_check(self):
        """Test that health checks bypass rate limiting."""
        response = client.get("/health")
        assert response.status_code == 200

    @patch("api.middleware.rate_limit.rate_limiter")
    def test_rate_limit_middleware_api_key(self, mock_rate_limiter):
        """Test rate limiting with API key."""
        mock_rate_limiter.is_allowed.return_value = True
        mock_rate_limiter.get_remaining.return_value = 5

        response = client.get(
            "/health", headers={"Authorization": "Bearer pk_test_api_key_123"}
        )
        assert response.status_code == 200

        # Should use API key as identifier
        mock_rate_limiter.is_allowed.assert_called_with("api_key:pk_test_api_key_123")

    @patch("api.middleware.rate_limit.rate_limiter")
    def test_rate_limit_middleware_x_api_key(self, mock_rate_limiter):
        """Test rate limiting with X-API-Key header."""
        mock_rate_limiter.is_allowed.return_value = True
        mock_rate_limiter.get_remaining.return_value = 5

        response = client.get("/health", headers={"X-API-Key": "pk_test_api_key_456"})
        assert response.status_code == 200

        # Should use API key as identifier
        mock_rate_limiter.is_allowed.assert_called_with("api_key:pk_test_api_key_456")


class TestQuotaIntegration:
    """Test quota integration with answer endpoints."""

    @patch("api.middleware.rate_limit.check_quota")
    @patch("api.middleware.rate_limit.get_remaining_quota")
    @patch("api.dependencies.auth.get_current_user")
    def test_answer_quota_exceeded(
        self, mock_auth, mock_get_remaining, mock_check_quota
    ):
        """Test that answer endpoint returns 402 when quota exceeded."""
        # Mock user
        mock_user = Mock()
        mock_user.tenant_id = "test_tenant"
        mock_auth.return_value = mock_user

        # Mock quota exceeded
        mock_check_quota.return_value = False
        mock_get_remaining.return_value = 50

        response = client.post(
            "/answer",
            headers={"Authorization": "Bearer test_token"},
            json={
                "query": "What is this about?",
                "top_k": 10,
                "rerank": True,
                "max_ctx": 2000,
            },
        )

        assert response.status_code == 402
        assert "Daily token quota exceeded" in response.json()["detail"]

    @patch("api.middleware.rate_limit.check_quota")
    @patch("api.dependencies.auth.get_current_user")
    def test_stream_answer_quota_exceeded(self, mock_auth, mock_check_quota):
        """Test that stream answer endpoint returns 402 when quota exceeded."""
        # Mock user
        mock_user = Mock()
        mock_user.tenant_id = "test_tenant"
        mock_auth.return_value = mock_user

        # Mock quota exceeded
        mock_check_quota.return_value = False

        response = client.post(
            "/answer/stream",
            headers={"Authorization": "Bearer test_token"},
            json={
                "query": "What is this about?",
                "top_k": 10,
                "rerank": True,
                "max_ctx": 2000,
            },
        )

        assert response.status_code == 402
        assert "Daily token quota exceeded" in response.json()["detail"]


class TestRateLimitHeaders:
    """Test rate limit headers in responses."""

    @patch("api.middleware.rate_limit.rate_limiter")
    def test_rate_limit_headers(self, mock_rate_limiter):
        """Test that rate limit headers are included in responses."""
        mock_rate_limiter.is_allowed.return_value = True
        mock_rate_limiter.get_remaining.return_value = 3

        response = client.get("/health")

        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert response.headers["X-RateLimit-Limit"] == "60"
        assert response.headers["X-RateLimit-Remaining"] == "3"

    @patch("api.middleware.rate_limit.rate_limiter")
    def test_rate_limit_exceeded_headers(self, mock_rate_limiter):
        """Test rate limit headers when limit exceeded."""
        mock_rate_limiter.is_allowed.return_value = False
        mock_rate_limiter.get_remaining.return_value = 0

        with patch("api.middleware.rate_limit.jwt") as mock_jwt:
            mock_jwt.decode.return_value = {"sub": "test_user"}

            response = client.get("/health")

            assert response.status_code == 429
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
            assert "Retry-After" in response.headers
            assert response.headers["Retry-After"] == "60"


if __name__ == "__main__":
    pytest.main([__file__])
