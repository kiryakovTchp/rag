"""OpenTelemetry tracing configuration."""

import os
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# Initialize tracer
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Configure Jaeger exporter
jaeger_exporter = JaegerExporter(
    agent_host_name=os.getenv("JAEGER_HOST", "localhost"),
    agent_port=int(os.getenv("JAEGER_PORT", "6831")),
)

# Add span processor
span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)


def setup_tracing(app):
    """Setup OpenTelemetry tracing for FastAPI app."""
    FastAPIInstrumentor.instrument_app(app)
    
    # Instrument SQLAlchemy
    SQLAlchemyInstrumentor().instrument()
    
    # Instrument Redis
    RedisInstrumentor().instrument()
    
    # Instrument HTTP requests
    RequestsInstrumentor().instrument()


def create_span(name: str, attributes: dict = None):
    """Create a span with given name and attributes."""
    if attributes is None:
        attributes = {}
    
    with tracer.start_as_current_span(name, attributes=attributes) as span:
        return span


def add_event_to_span(span, name: str, attributes: dict = None):
    """Add event to current span."""
    if attributes is None:
        attributes = {}
    
    span.add_event(name, attributes)


def set_span_attribute(span, key: str, value):
    """Set attribute on current span."""
    span.set_attribute(key, value)


# Context managers for common operations
class LLMSpan:
    """Context manager for LLM operations."""
    
    def __init__(self, provider: str, model: str, query: str):
        self.provider = provider
        self.model = model
        self.query = query
        self.span = None
    
    def __enter__(self):
        self.span = create_span(
            "llm.generate",
            {
                "llm.provider": self.provider,
                "llm.model": self.model,
                "llm.query_length": len(self.query)
            }
        )
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            self.span.end()


class EmbeddingSpan:
    """Context manager for embedding operations."""
    
    def __init__(self, provider: str, text_count: int):
        self.provider = provider
        self.text_count = text_count
        self.span = None
    
    def __enter__(self):
        self.span = create_span(
            "embedding.generate",
            {
                "embedding.provider": self.provider,
                "embedding.text_count": self.text_count
            }
        )
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            self.span.end()


class SearchSpan:
    """Context manager for search operations."""
    
    def __init__(self, query: str, top_k: int):
        self.query = query
        self.top_k = top_k
        self.span = None
    
    def __enter__(self):
        self.span = create_span(
            "vector.search",
            {
                "search.query_length": len(self.query),
                "search.top_k": self.top_k
            }
        )
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            self.span.end()


class JobSpan:
    """Context manager for job operations."""
    
    def __init__(self, job_type: str, job_id: int, document_id: int):
        self.job_type = job_type
        self.job_id = job_id
        self.document_id = document_id
        self.span = None
    
    def __enter__(self):
        self.span = create_span(
            f"job.{self.job_type}",
            {
                "job.id": self.job_id,
                "job.type": self.job_type,
                "job.document_id": self.document_id
            }
        )
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            self.span.end()
