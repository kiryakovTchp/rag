"""Prometheus metrics for the API."""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
import time

# Request metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Error metrics
ERROR_COUNT = Counter(
    'http_errors_total',
    'Total HTTP errors',
    ['method', 'endpoint', 'error_type']
)

# Token usage metrics
TOKEN_USAGE = Counter(
    'llm_tokens_total',
    'Total LLM tokens used',
    ['provider', 'model', 'direction']  # direction: input/output
)

# Cost metrics
COST_USD = Counter(
    'llm_cost_usd_total',
    'Total LLM cost in USD',
    ['provider', 'model']
)

# Queue metrics
CELERY_QUEUE_SIZE = Gauge(
    'celery_queue_size',
    'Number of tasks in Celery queue',
    ['queue_name']
)

CELERY_WORKER_ACTIVE = Gauge(
    'celery_worker_active',
    'Number of active Celery workers',
    ['queue_name']
)

# Cache metrics
CACHE_HITS = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

CACHE_MISSES = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

# Rate limit metrics
RATE_LIMIT_EXCEEDED = Counter(
    'rate_limit_exceeded_total',
    'Total rate limit violations',
    ['user_id', 'endpoint']
)

QUOTA_EXCEEDED = Counter(
    'quota_exceeded_total',
    'Total quota violations',
    ['tenant_id', 'quota_type']
)


class MetricsMiddleware:
    """Middleware to collect request metrics."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        
        # Create a custom send function to capture response
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Record request metrics
                method = scope.get("method", "UNKNOWN")
                path = scope.get("path", "/")
                status_code = message.get("status", 500)
                
                REQUEST_COUNT.labels(
                    method=method,
                    endpoint=path,
                    status_code=status_code
                ).inc()
                
                # Record duration
                duration = time.time() - start_time
                REQUEST_DURATION.labels(
                    method=method,
                    endpoint=path
                ).observe(duration)
                
                # Record errors
                if status_code >= 400:
                    error_type = "4xx" if status_code < 500 else "5xx"
                    ERROR_COUNT.labels(
                        method=method,
                        endpoint=path,
                        error_type=error_type
                    ).inc()
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


def record_token_usage(provider: str, model: str, direction: str, tokens: int):
    """Record token usage."""
    TOKEN_USAGE.labels(
        provider=provider,
        model=model,
        direction=direction
    ).inc(tokens)


def record_cost(provider: str, model: str, cost_usd: float):
    """Record cost."""
    COST_USD.labels(
        provider=provider,
        model=model
    ).inc(cost_usd)


def record_cache_hit(cache_type: str):
    """Record cache hit."""
    CACHE_HITS.labels(cache_type=cache_type).inc()


def record_cache_miss(cache_type: str):
    """Record cache miss."""
    CACHE_MISSES.labels(cache_type=cache_type).inc()


def record_rate_limit_exceeded(user_id: str, endpoint: str):
    """Record rate limit violation."""
    RATE_LIMIT_EXCEEDED.labels(
        user_id=user_id,
        endpoint=endpoint
    ).inc()


def record_quota_exceeded(tenant_id: str, quota_type: str):
    """Record quota violation."""
    QUOTA_EXCEEDED.labels(
        tenant_id=tenant_id,
        quota_type=quota_type
    ).inc()


def update_celery_metrics(queue_name: str, queue_size: int, active_workers: int):
    """Update Celery metrics."""
    CELERY_QUEUE_SIZE.labels(queue_name=queue_name).set(queue_size)
    CELERY_WORKER_ACTIVE.labels(queue_name=queue_name).set(active_workers)


async def metrics_endpoint():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
