#!/bin/bash

# Start Observability Stack for PromoAI RAG
# This script starts Jaeger, Prometheus, and Grafana

set -e

echo "🚀 Starting PromoAI RAG Observability Stack..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Navigate to infra directory
cd "$(dirname "$0")/../infra"

# Start observability services
echo "📊 Starting Jaeger, Prometheus, and Grafana..."
docker-compose -f observability.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."

# Wait for Jaeger
echo "🔍 Waiting for Jaeger..."
until curl -s http://localhost:16686 > /dev/null 2>&1; do
    sleep 2
done
echo "✅ Jaeger is ready at http://localhost:16686"

# Wait for Prometheus
echo "📈 Waiting for Prometheus..."
until curl -s http://localhost:9090 > /dev/null 2>&1; do
    sleep 2
done
echo "✅ Prometheus is ready at http://localhost:9090"

# Wait for Grafana
echo "📊 Waiting for Grafana..."
until curl -s http://localhost:3000 > /dev/null 2>&1; do
    sleep 2
done
echo "✅ Grafana is ready at http://localhost:3000"

# Wait for Redis monitor
echo "🔴 Waiting for Redis monitor..."
until docker exec redis-monitor redis-cli ping > /dev/null 2>&1; do
    sleep 2
done
echo "✅ Redis monitor is ready at localhost:6380"

echo ""
echo "🎉 Observability Stack is ready!"
echo ""
echo "📊 Services:"
echo "  • Jaeger UI:     http://localhost:16686"
echo "  • Prometheus:    http://localhost:9090"
echo "  • Grafana:       http://localhost:3000 (admin/admin)"
echo "  • Redis Monitor: localhost:6380"
echo ""
echo "🔧 Environment variables to set:"
echo "  export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317"
echo "  export OTEL_SERVICE_NAME=api  # or 'worker' for workers"
echo ""
echo "📝 To stop services:"
echo "  cd infra && docker-compose -f observability.yml down"
echo ""
echo "🧪 To test tracing:"
echo "  # Start API with tracing enabled"
echo "  OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 OTEL_SERVICE_NAME=api uvicorn api.main:app --reload"
echo ""
echo "  # Start worker with tracing enabled"
echo "  OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 OTEL_SERVICE_NAME=worker celery -A workers.app worker --loglevel=info"
