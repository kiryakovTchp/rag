"""Test metrics functionality."""

import unittest
from unittest.mock import patch

from fastapi import Response

from api.metrics import (
    metrics_endpoint,
    record_cache_hit,
    record_cache_miss,
    record_cost,
    record_quota_exceeded,
    record_rate_limit_exceeded,
    record_token_usage,
    update_celery_metrics,
)


class TestMetrics(unittest.TestCase):
    """Test metrics functions."""

    def test_record_token_usage(self):
        """Test recording token usage."""
        with patch("api.metrics.TOKEN_USAGE") as mock_counter:
            record_token_usage("gemini", "gemini-2.5-flash", "input", 100)

            mock_counter.labels.assert_called_once_with(
                provider="gemini", model="gemini-2.5-flash", direction="input"
            )
            mock_counter.labels.return_value.inc.assert_called_once_with(100)

    def test_record_cost(self):
        """Test recording cost."""
        with patch("api.metrics.COST_USD") as mock_counter:
            record_cost("gemini", "gemini-2.5-flash", 0.05)

            mock_counter.labels.assert_called_once_with(
                provider="gemini", model="gemini-2.5-flash"
            )
            mock_counter.labels.return_value.inc.assert_called_once_with(0.05)

    def test_record_cache_hit(self):
        """Test recording cache hit."""
        with patch("api.metrics.CACHE_HITS") as mock_counter:
            record_cache_hit("answer_cache")

            mock_counter.labels.assert_called_once_with(cache_type="answer_cache")
            mock_counter.labels.return_value.inc.assert_called_once()

    def test_record_cache_miss(self):
        """Test recording cache miss."""
        with patch("api.metrics.CACHE_MISSES") as mock_counter:
            record_cache_miss("answer_cache")

            mock_counter.labels.assert_called_once_with(cache_type="answer_cache")
            mock_counter.labels.return_value.inc.assert_called_once()

    def test_record_rate_limit_exceeded(self):
        """Test recording rate limit violation."""
        with patch("api.metrics.RATE_LIMIT_EXCEEDED") as mock_counter:
            record_rate_limit_exceeded("user123", "/answer")

            mock_counter.labels.assert_called_once_with(
                user_id="user123", endpoint="/answer"
            )
            mock_counter.labels.return_value.inc.assert_called_once()

    def test_record_quota_exceeded(self):
        """Test recording quota violation."""
        with patch("api.metrics.QUOTA_EXCEEDED") as mock_counter:
            record_quota_exceeded("tenant123", "daily_tokens")

            mock_counter.labels.assert_called_once_with(
                tenant_id="tenant123", quota_type="daily_tokens"
            )
            mock_counter.labels.return_value.inc.assert_called_once()

    def test_update_celery_metrics(self):
        """Test updating Celery metrics."""
        with patch("api.metrics.CELERY_QUEUE_SIZE") as mock_queue_size, patch(
            "api.metrics.CELERY_WORKER_ACTIVE"
        ) as mock_worker_active:
            update_celery_metrics("parse", 5, 2)

            mock_queue_size.labels.assert_called_once_with(queue_name="parse")
            mock_queue_size.labels.return_value.set.assert_called_once_with(5)

            mock_worker_active.labels.assert_called_once_with(queue_name="parse")
            mock_worker_active.labels.return_value.set.assert_called_once_with(2)

    @patch("api.metrics.generate_latest")
    def test_metrics_endpoint(self, mock_generate_latest):
        """Test metrics endpoint."""
        mock_generate_latest.return_value = (
            b"# HELP test_metric\n# TYPE test_metric counter\ntest_metric 1.0"
        )

        response = metrics_endpoint()

        self.assertIsInstance(response, Response)
        self.assertEqual(
            response.media_type, "text/plain; version=0.0.4; charset=utf-8"
        )
        self.assertEqual(
            response.content,
            b"# HELP test_metric\n# TYPE test_metric counter\ntest_metric 1.0",
        )


if __name__ == "__main__":
    unittest.main()
