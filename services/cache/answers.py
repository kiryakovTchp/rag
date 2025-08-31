"""Answer caching service."""

import hashlib
import json
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

import redis


class AnswerCache:
    """Cache for answer responses."""
    
    def __init__(self):
        """Initialize cache with Redis connection."""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.ttl = int(os.getenv("ANSWER_CACHE_TTL", "300"))  # 5 minutes default
    
    def _generate_key(
        self,
        tenant_id: Optional[str],
        query: str,
        top_k: int,
        rerank: bool,
        max_ctx: int,
        model: str
    ) -> str:
        """Generate cache key from parameters."""
        # Create a hash of the parameters
        key_data = {
            "tenant_id": tenant_id or "",
            "query": query,
            "top_k": top_k,
            "rerank": rerank,
            "max_ctx": max_ctx,
            "model": model
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return f"answer:{hashlib.sha256(key_string.encode()).hexdigest()}"
    
    def get(
        self,
        tenant_id: Optional[str],
        query: str,
        top_k: int,
        rerank: bool,
        max_ctx: int,
        model: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached answer.
        
        Args:
            tenant_id: Tenant identifier
            query: User query
            top_k: Number of chunks retrieved
            rerank: Whether reranking was applied
            max_ctx: Maximum context tokens
            model: LLM model used
            
        Returns:
            Cached answer data or None if not found
        """
        key = self._generate_key(tenant_id, query, top_k, rerank, max_ctx, model)
        
        try:
            cached_data = self.redis.get(key)
            if cached_data:
                data = json.loads(cached_data)
                # Update latency to current time
                data["usage"]["latency_ms"] = 0  # Cache hit
                return data
        except (json.JSONDecodeError, redis.RedisError):
            pass
        
        return None
    
    def set(
        self,
        tenant_id: Optional[str],
        query: str,
        top_k: int,
        rerank: bool,
        max_ctx: int,
        model: str,
        answer: str,
        citations: list,
        usage: dict
    ) -> None:
        """Cache answer response.
        
        Args:
            tenant_id: Tenant identifier
            query: User query
            top_k: Number of chunks retrieved
            rerank: Whether reranking was applied
            max_ctx: Maximum context tokens
            model: LLM model used
            answer: Generated answer
            citations: Citation list
            usage: Usage information
        """
        key = self._generate_key(tenant_id, query, top_k, rerank, max_ctx, model)
        
        cache_data = {
            "answer": answer,
            "citations": citations,
            "usage": usage
        }
        
        try:
            self.redis.setex(
                key,
                self.ttl,
                json.dumps(cache_data)
            )
        except redis.RedisError:
            # Silently fail if Redis is unavailable
            pass
    
    def invalidate_tenant(self, tenant_id: str) -> None:
        """Invalidate all cache entries for a tenant.
        
        Args:
            tenant_id: Tenant identifier
        """
        try:
            # Find all keys for this tenant
            pattern = f"answer:*"
            keys = self.redis.keys(pattern)
            
            for key in keys:
                # Check if key belongs to tenant
                cached_data = self.redis.get(key)
                if cached_data:
                    data = json.loads(cached_data)
                    if data.get("tenant_id") == tenant_id:
                        self.redis.delete(key)
        except (json.JSONDecodeError, redis.RedisError):
            pass
