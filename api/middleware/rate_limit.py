"""Rate limiting middleware."""

import time
import os
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import redis

# Redis connection
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

def get_rate_limit_key(request: Request, user_id: str) -> str:
    """Generate rate limit key for user."""
    return f"rate_limit:{user_id}:{int(time.time() // 60)}"

def get_quota_key(tenant_id: str) -> str:
    """Generate daily quota key for tenant."""
    date = time.strftime("%Y-%m-%d")
    return f"quota:{tenant_id}:{date}"

async def check_rate_limit(request: Request, user_id: str) -> None:
    """Check rate limit for user."""
    rate_limit_per_min = int(os.getenv("RATE_LIMIT_PER_MIN", "60"))
    
    key = get_rate_limit_key(request, user_id)
    
    try:
        # Get current count
        current = redis_client.get(key)
        if current is None:
            current = 0
        else:
            current = int(current)
        
        # Check if limit exceeded
        if current >= rate_limit_per_min:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {rate_limit_per_min} requests per minute."
            )
        
        # Increment counter
        redis_client.incr(key)
        redis_client.expire(key, 60)  # Expire in 60 seconds
        
    except redis.RedisError:
        # If Redis is unavailable, allow request
        pass

async def check_daily_quota(tenant_id: str, tokens_used: int) -> None:
    """Check daily token quota for tenant."""
    daily_quota = int(os.getenv("DAILY_TOKEN_QUOTA", "200000"))
    
    key = get_quota_key(tenant_id)
    
    try:
        # Get current usage
        current = redis_client.get(key)
        if current is None:
            current = 0
        else:
            current = int(current)
        
        # Check if quota would be exceeded
        if current + tokens_used > daily_quota:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Daily token quota exceeded. Used: {current}, Limit: {daily_quota}"
            )
        
        # Increment usage
        redis_client.incrby(key, tokens_used)
        redis_client.expire(key, 86400)  # Expire in 24 hours
        
    except redis.RedisError:
        # If Redis is unavailable, allow request
        pass

async def update_quota_usage(tenant_id: str, tokens_used: int) -> None:
    """Update quota usage after successful request."""
    key = get_quota_key(tenant_id)
    
    try:
        redis_client.incrby(key, tokens_used)
        redis_client.expire(key, 86400)  # Expire in 24 hours
    except redis.RedisError:
        # If Redis is unavailable, ignore
        pass
