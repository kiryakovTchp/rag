"""OpenTelemetry configuration for API tracing and metrics."""

import logging
import os
import time
from typing import Optional

from fastapi import Request
from fastapi.responses import Response as FastAPIResponse
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

logger = logging.getLogger(__name__)

# Prometheus metrics
QUERY_LATENCY = Histogram(
    "query_latency_seconds",
    "Query latency in seconds",
    ["route", "tenant", "method"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

TENANT_QUERIES = Counter(
    "tenant_queries_total", "Total queries per tenant", ["tenant", "route", "method"]
)

REDIS_PUBLISH_FAILURES = Counter(
    "redis_publish_failures_total", "Total Redis publish failures", ["tenant", "topic"]
)

INGEST_JOBS = Counter(
    "ingest_jobs_total", "Total ingest jobs", ["tenant", "status", "type"]
)

# Gauge for queue length (will be updated by workers)
QUEUE_LENGTH = Gauge("queue_length", "Number of jobs in queue", ["queue_name"])


def setup_tracing():
    """Setup OpenTelemetry tracing."""
    # Get configuration from environment
    otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    service_name = os.getenv("OTEL_SERVICE_NAME", "api")

    # Create resource with service information
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": "1.0.0",
            "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        }
    )

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Add OTLP exporter
    if otel_endpoint != "none":
        otlp_exporter = OTLPSpanExporter(endpoint=otel_endpoint)
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Set global tracer provider
    trace.set_tracer_provider(provider)

    # Get tracer
    tracer = trace.get_tracer(__name__)

    logger.info(f"OpenTelemetry tracing initialized for {service_name}")
    return tracer


def instrument_fastapi(app):
    """Instrument FastAPI with OpenTelemetry."""
    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumented with OpenTelemetry")
    except Exception as e:
        logger.warning(f"Failed to instrument FastAPI: {e}")


def instrument_redis():
    """Instrument Redis with OpenTelemetry."""
    try:
        RedisInstrumentor().instrument()
        logger.info("Redis instrumented with OpenTelemetry")
    except Exception as e:
        logger.warning(f"Failed to instrument Redis: {e}")


def instrument_sqlalchemy():
    """Instrument SQLAlchemy with OpenTelemetry."""
    try:
        SQLAlchemyInstrumentor().instrument()
        logger.info("SQLAlchemy instrumented with OpenTelemetry")
    except Exception as e:
        logger.warning(f"Failed to instrument SQLAlchemy: {e}")


def instrument_logging():
    """Instrument logging with OpenTelemetry."""
    try:
        LoggingInstrumentor().instrument()
        logger.info("Logging instrumented with OpenTelemetry")
    except Exception as e:
        logger.warning(f"Failed to instrument logging: {e}")


def get_tracer():
    """Get the global tracer."""
    return trace.get_tracer(__name__)


def create_span(name: str, attributes: Optional[dict] = None):
    """Create a span with given name and attributes."""
    tracer = get_tracer()
    with tracer.start_as_current_span(name, attributes=attributes or {}) as span:
        return span


# Middleware for request metrics
async def metrics_middleware(request: Request, call_next):
    """Middleware to collect request metrics."""
    start_time = time.time()

    # Extract tenant from request (if available)
    tenant = getattr(request.state, "tenant_id", None) or request.headers.get(
        "x-tenant-id", "unknown"
    )

    # Extract route and method
    route = request.url.path
    method = request.method

    # Increment query counter
    TENANT_QUERIES.labels(tenant=tenant, route=route, method=method).inc()

    # Process request
    response = await call_next(request)

    # Calculate latency
    latency = time.time() - start_time

    # Record latency histogram
    QUERY_LATENCY.labels(route=route, tenant=tenant, method=method).observe(latency)

    return response


def get_metrics():
    """Get Prometheus metrics."""
    return FastAPIResponse(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


def record_redis_failure(tenant: str, topic: str):
    """Record Redis publish failure."""
    REDIS_PUBLISH_FAILURES.labels(tenant=tenant, topic=topic).inc()


def record_ingest_job(tenant: str, status: str, job_type: str):
    """Record ingest job metric."""
    INGEST_JOBS.labels(tenant=tenant, status=status, type=job_type).inc()


def update_queue_length(queue_name: str, length: int):
    """Update queue length metric."""
    QUEUE_LENGTH.labels(queue_name=queue_name).set(length)
