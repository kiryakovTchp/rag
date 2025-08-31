"""Rate limiting middleware."""

import os
import time
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import redis

# Redis connection
redis_client = redis.Redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379"),
    decode_responses=True
)


class RateLimiter:
    """Rate limiter using Redis."""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # 1 minute window
    
    def _get_key(self, identifier: str) -> str:
        """Get Redis key for rate limiting."""
        current_window = int(time.time() // self.window_size)
        return f"rate_limit:{identifier}:{current_window}"
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed."""
        key = self._get_key(identifier)
        
        try:
            # Get current count
            current_count = redis_client.get(key)
            count = int(current_count) if current_count else 0
            
            if count >= self.requests_per_minute:
                return False
            
            # Increment count
            pipe = redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, self.window_size)
            pipe.execute()
            
            return True
            
        except Exception as e:
            # If Redis is down, allow requests
            print(f"Rate limiting error: {e}")
            return True
    
    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests for the current window."""
        key = self._get_key(identifier)
        
        try:
            current_count = redis_client.get(key)
            count = int(current_count) if current_count else 0
            return max(0, self.requests_per_minute - count)
        except Exception:
            return self.requests_per_minute


class QuotaLimiter:
    """Daily token quota limiter."""
    
    def __init__(self, daily_token_quota: int = 200000):
        self.daily_token_quota = daily_token_quota
    
    def _get_key(self, tenant_id: str) -> str:
        """Get Redis key for daily quota."""
        today = time.strftime("%Y-%m-%d")
        return f"quota:{tenant_id}:{today}"
    
    def check_quota(self, tenant_id: str, tokens: int) -> bool:
        """Check if request fits within daily quota."""
        key = self._get_key(tenant_id)
        
        try:
            # Get current usage
            current_usage = redis_client.get(key)
            usage = int(current_usage) if current_usage else 0
            
            if usage + tokens > self.daily_token_quota:
                return False
            
            # Increment usage
            pipe = redis_client.pipeline()
            pipe.incrby(key, tokens)
            pipe.expire(key, 86400)  # 24 hours
            pipe.execute()
            
            return True
            
        except Exception as e:
            # If Redis is down, allow requests
            print(f"Quota limiting error: {e}")
            return True
    
    def get_remaining_quota(self, tenant_id: str) -> int:
        """Get remaining daily quota."""
        key = self._get_key(tenant_id)
        
        try:
            current_usage = redis_client.get(key)
            usage = int(current_usage) if current_usage else 0
            return max(0, self.daily_token_quota - usage)
        except Exception:
            return self.daily_token_quota


# Global instances
rate_limiter = RateLimiter(
    requests_per_minute=int(os.getenv("RATE_LIMIT_PER_MIN", "60"))
)

quota_limiter = QuotaLimiter(
    daily_token_quota=int(os.getenv("DAILY_TOKEN_QUOTA", "200000"))
)


async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware."""
    # Skip rate limiting for health checks
    if request.url.path == "/health":
        return await call_next(request)
    
    # Get identifier (user ID or API key ID)
    identifier = None
    
    # Try to get from authorization header
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        if token.startswith("pk_"):
            # API key
            identifier = f"api_key:{token[:20]}"  # Use first 20 chars
        else:
            # JWT token - extract user ID
            try:
                import jwt
                secret = os.getenv("NEXTAUTH_SECRET")
                if secret:
                    payload = jwt.decode(token, secret, algorithms=["HS256"])
                    identifier = f"user:{payload.get('sub', 'unknown')}"
            except:
                identifier = "anonymous"
    
    # Try X-API-Key header
    if not identifier:
        api_key = request.headers.get("X-API-Key")
        if api_key:
            identifier = f"api_key:{api_key[:20]}"
    
    # Fallback to IP address
    if not identifier:
        identifier = f"ip:{request.client.host}"
    
    # Check rate limit
    if not rate_limiter.is_allowed(identifier):
        remaining = rate_limiter.get_remaining(identifier)
        
        response = JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Limit: {rate_limiter.requests_per_minute} per minute",
                "retry_after": 60
            }
        )
        response.headers["X-RateLimit-Limit"] = str(rate_limiter.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["Retry-After"] = "60"
        return response
    
    # Add rate limit headers
    response = await call_next(request)
    remaining = rate_limiter.get_remaining(identifier)
    response.headers["X-RateLimit-Limit"] = str(rate_limiter.requests_per_minute)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    
    return response


def check_quota(tenant_id: str, tokens: int) -> bool:
    """Check daily token quota."""
    return quota_limiter.check_quota(tenant_id, tokens)


def get_remaining_quota(tenant_id: str) -> int:
    """Get remaining daily quota."""
    return quota_limiter.get_remaining_quota(tenant_id)
