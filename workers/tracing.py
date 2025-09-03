"""OpenTelemetry configuration for Celery workers."""

import logging
import os
import time
from typing import Optional

from celery import Task

# OpenTelemetry temporarily disabled for stability
# from opentelemetry import trace
# from opentelemetry.sdk.trace import TracerProvider
# from opentelemetry.sdk.trace.export import BatchSpanProcessor
# from opentelemetry.sdk.resources import Resource
# from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
# from opentelemetry.instrumentation.celery import CeleryInstrumentor
# from opentelemetry.instrumentation.redis import RedisInstrumentor
# from opentelemetry.instrumentation.logging import LoggingInstrumentor
from prometheus_client import Counter, Gauge, Histogram, generate_latest

logger = logging.getLogger(__name__)

# Prometheus metrics for workers
INGEST_JOB_DURATION = Histogram(
    "ingest_job_duration_seconds",
    "Ingest job duration in seconds",
    ["tenant", "job_type", "status"],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0],
)

EMBEDDING_DURATION = Histogram(
    "embedding_duration_seconds",
    "Embedding generation duration in seconds",
    ["tenant", "model", "text_count"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

RERANK_DURATION = Histogram(
    "rerank_duration_seconds",
    "Reranking duration in seconds",
    ["tenant", "model", "candidate_count"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

QUEUE_LENGTH = Gauge("worker_queue_length", "Number of jobs in queue", ["queue_name"])

WORKER_TASKS_PROCESSED = Counter(
    "worker_tasks_processed_total",
    "Total tasks processed by worker",
    ["worker_name", "task_name", "status"],
)


def setup_tracing():
    """Setup OpenTelemetry tracing for workers."""
    # OpenTelemetry temporarily disabled for stability
    logger.info("OpenTelemetry tracing disabled for stability")
    return None


def instrument_celery():
    """Instrument Celery with OpenTelemetry."""
    # OpenTelemetry temporarily disabled for stability
    logger.info("Celery instrumentation disabled for stability")


def instrument_redis():
    """Instrument Redis with OpenTelemetry."""
    # OpenTelemetry temporarily disabled for stability
    logger.info("Redis instrumentation disabled for stability")


def instrument_logging():
    """Instrument logging with OpenTelemetry."""
    # OpenTelemetry temporarily disabled for stability
    logger.info("Logging instrumentation disabled for stability")


def get_tracer():
    """Get the global tracer."""
    return None


def create_span(name: str, attributes: Optional[dict] = None):
    """Create a span with given name and attributes."""
    return None


# Celery task wrapper for tracing and metrics
class TracedTask(Task):
    """Celery task with OpenTelemetry tracing and Prometheus metrics."""

    def __call__(self, *args, **kwargs):
        """Execute task with tracing."""
        start_time = time.time()

        # Extract tenant and job info from task
        tenant = "unknown"
        job_type = self.name
        job_id = None

        try:
            # Try to extract tenant from task arguments
            if args and len(args) > 0:
                if isinstance(args[0], dict):
                    tenant = args[0].get("tenant_id", "unknown")
                    job_id = args[0].get("job_id")
                elif len(args) > 1 and isinstance(args[1], dict):
                    tenant = args[1].get("tenant_id", "unknown")
                    job_id = args[1].get("job_id")
        except Exception:
            tenant = "unknown"

        # Create span for task execution
        with create_span(
            f"celery.task.{self.name}",
            {
                "celery.task.name": self.name,
                "celery.task.id": self.request.id,
                "tenant.id": tenant,
                "job.id": job_id,
            },
        ):
            try:
                # Execute task
                result = super().__call__(*args, **kwargs)

                # Record success metrics
                duration = time.time() - start_time
                WORKER_TASKS_PROCESSED.labels(
                    worker_name=os.getenv("CELERY_WORKER_ID", "unknown"),
                    task_name=self.name,
                    status="success",
                ).inc()

                # Record duration based on task type
                if "ingest" in self.name:
                    INGEST_JOB_DURATION.labels(
                        tenant=tenant, job_type=job_type, status="success"
                    ).observe(duration)
                elif "embed" in self.name:
                    EMBEDDING_DURATION.labels(
                        tenant=tenant,
                        model="sentence-transformers",
                        text_count=1,  # Will be updated with actual count
                    ).observe(duration)
                elif "rerank" in self.name:
                    RERANK_DURATION.labels(
                        tenant=tenant,
                        model="rerank-model",
                        candidate_count=1,  # Will be updated with actual count
                    ).observe(duration)

                return result

            except Exception:
                # Record failure metrics
                duration = time.time() - start_time
                WORKER_TASKS_PROCESSED.labels(
                    worker_name=os.getenv("CELERY_WORKER_ID", "unknown"),
                    task_name=self.name,
                    status="failure",
                ).inc()

                # Record duration for failed tasks
                if "ingest" in self.name:
                    INGEST_JOB_DURATION.labels(
                        tenant=tenant, job_type=job_type, status="failure"
                    ).observe(duration)

                # Re-raise exception
                raise


def record_ingest_job(tenant: str, job_type: str, status: str, duration: float):
    """Record ingest job metric."""
    INGEST_JOB_DURATION.labels(tenant=tenant, job_type=job_type, status=status).observe(
        duration
    )


def record_embedding_job(tenant: str, model: str, text_count: int, duration: float):
    """Record embedding job metric."""
    EMBEDDING_DURATION.labels(
        tenant=tenant, model=model, text_count=text_count
    ).observe(duration)


def record_rerank_job(tenant: str, model: str, candidate_count: int, duration: float):
    """Record rerank job metric."""
    RERANK_DURATION.labels(
        tenant=tenant, model=model, candidate_count=candidate_count
    ).observe(duration)


def update_queue_length(queue_name: str, length: int):
    """Update queue length metric."""
    QUEUE_LENGTH.labels(queue_name=queue_name).set(length)


def get_worker_metrics():
    """Get Prometheus metrics for worker."""
    return generate_latest()
