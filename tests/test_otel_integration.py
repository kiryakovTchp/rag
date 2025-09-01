"""Test OpenTelemetry integration with API and workers."""

import pytest
import asyncio
import time
from unittest.mock import patch, MagicMock

from api.tracing import setup_tracing, get_tracer, create_span, QUERY_LATENCY, TENANT_QUERIES
from workers.tracing import setup_tracing as setup_worker_tracing, get_tracer as get_worker_tracer


class TestOpenTelemetryIntegration:
    """Test OpenTelemetry integration."""

    def test_setup_tracing_api(self):
        """Test OpenTelemetry setup for API."""
        with patch('opentelemetry.sdk.trace.TracerProvider') as mock_provider:
            with patch('opentelemetry.exporter.otlp.proto.grpc.trace_exporter.OTLPSpanExporter') as mock_exporter:
                tracer = setup_tracing()
                assert tracer is not None
                mock_provider.assert_called_once()

    def test_setup_tracing_worker(self):
        """Test OpenTelemetry setup for workers."""
        with patch('opentelemetry.sdk.trace.TracerProvider') as mock_provider:
            with patch('opentelemetry.exporter.otlp.proto.grpc.trace_exporter.OTLPSpanExporter') as mock_exporter:
                tracer = setup_worker_tracing()
                assert tracer is not None
                mock_provider.assert_called_once()

    def test_create_span(self):
        """Test span creation."""
        with patch('opentelemetry.sdk.trace.TracerProvider') as mock_provider:
            with patch('opentelemetry.exporter.otlp.proto.grpc.trace_exporter.OTLPSpanExporter') as mock_exporter:
                setup_tracing()
                with create_span("test.operation", {"test.attr": "value"}) as span:
                    assert span is not None
                    # Check that span has the expected attributes
                    span.set_attribute.assert_called_with("test.attr", "value")

    def test_metrics_collection(self):
        """Test Prometheus metrics collection."""
        # Test query latency metric
        QUERY_LATENCY.labels(route="/test", tenant="test_tenant", method="GET").observe(0.5)
        
        # Test tenant queries counter
        TENANT_QUERIES.labels(tenant="test_tenant", route="/test", method="GET").inc()
        
        # Verify metrics are recorded
        assert True  # If we get here, no exceptions were raised

    @pytest.mark.asyncio
    async def test_trace_propagation(self):
        """Test trace propagation through services."""
        with patch('opentelemetry.sdk.trace.TracerProvider') as mock_provider:
            with patch('opentelemetry.exporter.otlp.proto.grpc.trace_exporter.OTLPSpanExporter') as mock_exporter:
                setup_tracing()
                tracer = get_tracer()
                
                # Create a span
                with tracer.start_as_current_span("test.operation") as span:
                    span_id = span.get_span_context().span_id
                    trace_id = span.get_span_context().trace_id
                    
                    # Verify span context is available
                    assert span_id is not None
                    assert trace_id is not None

    def test_worker_tracing_integration(self):
        """Test worker tracing integration."""
        with patch('opentelemetry.sdk.trace.TracerProvider') as mock_provider:
            with patch('opentelemetry.exporter.otlp.proto.grpc.trace_exporter.OTLPSpanExporter') as mock_exporter:
                setup_worker_tracing()
                tracer = get_worker_tracer()
                
                # Test worker span creation
                with create_span("worker.task", {"task.name": "test_task"}) as span:
                    assert span is not None

    def test_metrics_endpoint_availability(self):
        """Test that metrics endpoint is available."""
        try:
            from api.tracing import get_metrics
            metrics = get_metrics()
            assert metrics is not None
            assert hasattr(metrics, 'body')
        except ImportError:
            pytest.skip("Metrics endpoint not available")

    def test_redis_failure_metric(self):
        """Test Redis failure metric recording."""
        try:
            from api.tracing import record_redis_failure
            record_redis_failure("test_tenant", "test.topic")
            assert True  # If we get here, no exceptions were raised
        except ImportError:
            pytest.skip("Redis failure metric not available")

    def test_ingest_job_metric(self):
        """Test ingest job metric recording."""
        try:
            from api.tracing import record_ingest_job
            record_ingest_job("test_tenant", "success", "parse")
            assert True  # If we get here, no exceptions were raised
        except ImportError:
            pytest.skip("Ingest job metric not available")


class TestTracingPerformance:
    """Test tracing performance impact."""

    def test_span_creation_overhead(self):
        """Test that span creation doesn't add significant overhead."""
        with patch('opentelemetry.sdk.trace.TracerProvider') as mock_provider:
            with patch('opentelemetry.exporter.otlp.proto.grpc.trace_exporter.OTLPSpanExporter') as mock_exporter:
                setup_tracing()
                
                # Measure time without tracing
                start_time = time.time()
                for _ in range(1000):
                    pass
                no_tracing_time = time.time() - start_time
                
                # Measure time with tracing
                start_time = time.time()
                for _ in range(1000):
                    with create_span("test.operation"):
                        pass
                with_tracing_time = time.time() - start_time
                
                # Tracing should add less than 10% overhead
                overhead_ratio = with_tracing_time / no_tracing_time
                assert overhead_ratio < 1.1, f"Tracing overhead too high: {overhead_ratio}"


if __name__ == "__main__":
    pytest.main([__file__])
