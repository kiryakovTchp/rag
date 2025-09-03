"""Answer generation guards and validation."""

import os
import re
from typing import Optional


class AnswerGuard:
    """Guards for answer generation requests."""

    def __init__(self):
        """Initialize guard with configuration."""
        self.max_query_length = 1000
        self.content_filter_enabled = (
            os.getenv("ANSWER_CONTENT_FILTER", "false").lower() == "true"
        )

        # Simple content filter patterns
        self.blocked_patterns = [
            r"\b(spam|scam|hack|crack|virus|malware)\b",
            r"\b(admin|root|sudo|password)\b",
            r"\b(delete|drop|truncate|alter)\b",
            r"\b(script|javascript|eval|exec)\b",
            r"\b(union|select|insert|update)\b",
        ]

    def validate_query(self, query: str) -> None:
        """Validate query input.

        Args:
            query: User query to validate

        Raises:
            ValueError: If query is invalid
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        if len(query) > self.max_query_length:
            raise ValueError(f"Query too long (max {self.max_query_length} characters)")

        # Content filtering
        if self.content_filter_enabled:
            self._check_content_filter(query)

    def _check_content_filter(self, query: str) -> None:
        """Check query against content filter.

        Args:
            query: Query to check

        Raises:
            ValueError: If query contains blocked content
        """
        query_lower = query.lower()

        for pattern in self.blocked_patterns:
            if re.search(pattern, query_lower):
                raise ValueError("Query contains blocked content")

    def validate_parameters(
        self,
        top_k: int,
        max_ctx: int,
        max_tokens: int,
        temperature: float,
        timeout_s: int,
    ) -> None:
        """Validate generation parameters.

        Args:
            top_k: Number of chunks to retrieve
            max_ctx: Maximum context tokens
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            timeout_s: Timeout in seconds

        Raises:
            ValueError: If parameters are invalid
        """
        if top_k < 1 or top_k > 50:
            raise ValueError("top_k must be between 1 and 50")

        if max_ctx < 100 or max_ctx > 4096:
            raise ValueError("max_ctx must be between 100 and 4096")

        if max_tokens < 1 or max_tokens > 4096:
            raise ValueError("max_tokens must be between 1 and 4096")

        if temperature < 0.0 or temperature > 1.0:
            raise ValueError("temperature must be between 0.0 and 1.0")

        if timeout_s < 1 or timeout_s > 120:
            raise ValueError("timeout_s must be between 1 and 120")

    def get_rate_limit_key(self, tenant_id: Optional[str] = None) -> str:
        """Get rate limit key for tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Rate limit key
        """
        if tenant_id:
            return f"rate_limit:answer:{tenant_id}"
        else:
            return "rate_limit:answer:anonymous"
