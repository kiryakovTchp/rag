"""Answer caching service using Redis."""

import json
import logging
from typing import Optional

import redis

logger = logging.getLogger(__name__)


class AnswerCache:
    """Cache for storing and retrieving answer results."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize answer cache.

        Args:
            redis_url: Redis connection URL
        """
        try:
            self.redis = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis.ping()
            logger.info("Connected to Redis for answer caching")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis = None

    def _make_key(self, query: str, tenant_id: str) -> str:
        """Create cache key for query and tenant."""
        return f"answer:{tenant_id}:{hash(query)}"

    def get_cached_answer(self, query: str, tenant_id: str) -> Optional[dict]:
        """Get cached answer for query.

        Args:
            query: Search query
            tenant_id: Tenant identifier

        Returns:
            Cached answer data or None if not found
        """
        if not self.redis:
            return None

        try:
            key = self._make_key(query, tenant_id)
            cached_data = self.redis.get(key)

            if cached_data:
                logger.info(f"Cache hit for query: {query[:50]}...")
                return json.loads(cached_data)

            logger.info(f"Cache miss for query: {query[:50]}...")
            return None

        except Exception as e:
            logger.error(f"Failed to get cached answer: {e}")
            return None

    def cache_answer(
        self,
        query: str,
        tenant_id: str,
        answer: str,
        citations: list[dict],
        usage: dict,
        ttl: int = 3600,
    ) -> bool:
        """Cache answer result.

        Args:
            query: Search query
            tenant_id: Tenant identifier
            answer: Generated answer
            citations: List of citations
            usage: Usage information
            ttl: Time to live in seconds

        Returns:
            True if cached successfully, False otherwise
        """
        if not self.redis:
            return False

        try:
            key = self._make_key(query, tenant_id)
            data = {
                "answer": answer,
                "citations": citations,
                "usage": usage,
                "tenant_id": tenant_id,
            }

            # Store in Redis with TTL
            self.redis.setex(key, ttl, json.dumps(data))
            logger.info(f"Cached answer for query: {query[:50]}...")
            return True

        except Exception as e:
            logger.error(f"Failed to cache answer: {e}")
            return False

    def invalidate_cache(self, tenant_id: str, pattern: str = "*") -> int:
        """Invalidate cache entries for tenant.

        Args:
            tenant_id: Tenant identifier
            pattern: Pattern to match keys

        Returns:
            Number of keys invalidated
        """
        if not self.redis:
            return 0

        try:
            pattern = f"answer:{tenant_id}:{pattern}"
            keys = self.redis.keys(pattern)

            if keys:
                deleted = self.redis.delete(*keys)
                logger.info(
                    f"Invalidated {deleted} cache entries for tenant {tenant_id}"
                )
                return deleted

            return 0

        except Exception as e:
            logger.error(f"Failed to invalidate cache: {e}")
            return 0

    def get_cache_stats(self, tenant_id: str) -> dict:
        """Get cache statistics for tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Dictionary with cache statistics
        """
        if not self.redis:
            return {"error": "Redis not available"}

        try:
            pattern = f"answer:{tenant_id}:*"
            keys = self.redis.keys(pattern)

            total_keys = len(keys)
            total_memory = 0

            for key in keys:
                try:
                    memory = self.redis.memory_usage(key)
                    if memory:
                        total_memory += memory
                except Exception:
                    pass

            return {
                "tenant_id": tenant_id,
                "total_keys": total_keys,
                "total_memory_bytes": total_memory,
                "redis_connected": True,
            }

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}
