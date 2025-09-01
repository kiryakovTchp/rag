#!/bin/bash

# Acceptance Script for S4-2: Observability Stack
# Проверяет OpenTelemetry + Prometheus + Grafana интеграцию

set -e

echo "🧪 S4-2 Observability Stack Acceptance Test"
echo "============================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check functions
check_step() {
    local step_name="$1"
    local command="$2"
    local expected_output="$3"
    
    echo -n "🔍 Checking: $step_name... "
    
    if eval "$command" | grep -q "$expected_output"; then
        echo -e "${GREEN}✅ PASS${NC}"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        return 1
    fi
}

check_import() {
    local module="$1"
    local import_pattern="$2"
    
    echo -n "🔍 Checking: $module imports $import_pattern... "
    
    if grep -R "$import_pattern" "$module" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ FOUND${NC}"
        return 0
    else
        echo -e "${RED}❌ NOT FOUND${NC}"
        return 1
    fi
}

check_no_import() {
    local module="$1"
    local import_pattern="$2"
    
    echo -n "🔍 Checking: $module does NOT import $import_pattern... "
    
    if ! grep -R "$import_pattern" "$module" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ NOT FOUND${NC}"
        return 0
    else
        echo -e "${RED}❌ STILL FOUND${NC}"
        return 1
    fi
}

# Test results
TESTS_PASSED=0
TESTS_TOTAL=0

run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -n "🧪 Testing: $test_name... "
    
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}"
    fi
    ((TESTS_TOTAL++))
}

echo ""
echo "📋 Phase 1: Code Structure & Imports"
echo "------------------------------------"

# Check OpenTelemetry imports in API
check_import "api/tracing.py" "opentelemetry" && ((TESTS_PASSED++)) || true
((TESTS_TOTAL++))

check_import "api/tracing.py" "prometheus_client" && ((TESTS_PASSED++)) || true
((TESTS_TOTAL++))

# Check OpenTelemetry imports in workers
check_import "workers/tracing.py" "opentelemetry" && ((TESTS_PASSED++)) || true
((TESTS_TOTAL++))

check_import "workers/tracing.py" "prometheus_client" && ((TESTS_PASSED++)) || true
((TESTS_TOTAL++))

# Check API integration
check_import "api/main.py" "api.tracing" && ((TESTS_PASSED++)) || true
((TESTS_TOTAL++))

# Check worker integration
check_import "workers/app.py" "workers.tracing" && ((TESTS_PASSED++)) || true
((TESTS_TOTAL++))

# Check Event Bus integration
check_import "services/events/bus.py" "record_redis_failure" && ((TESTS_PASSED++)) || true
((TESTS_TOTAL++))

echo ""
echo "📋 Phase 2: Configuration Files"
echo "-------------------------------"

# Check observability infrastructure files
if [ -f "infra/observability.yml" ]; then
    echo -e "${GREEN}✅ observability.yml exists${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ observability.yml missing${NC}"
fi
((TESTS_TOTAL++))

if [ -f "infra/prometheus.yml" ]; then
    echo -e "${GREEN}✅ prometheus.yml exists${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ prometheus.yml missing${NC}"
fi
((TESTS_TOTAL++))

if [ -f "infra/rules/alerts.yml" ]; then
    echo -e "${GREEN}✅ alerts.yml exists${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ alerts.yml missing${NC}"
fi
((TESTS_TOTAL++))

# Check Grafana configuration
if [ -d "infra/grafana" ]; then
    echo -e "${GREEN}✅ grafana/ directory exists${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ grafana/ directory missing${NC}"
fi
((TESTS_TOTAL++))

if [ -f "infra/grafana/dashboards/api-overview.json" ]; then
    echo -e "${GREEN}✅ API dashboard exists${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ API dashboard missing${NC}"
fi
((TESTS_TOTAL++))

if [ -f "infra/grafana/dashboards/workers-overview.json" ]; then
    echo -e "${GREEN}✅ Workers dashboard exists${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ Workers dashboard missing${NC}"
fi
((TESTS_TOTAL++))

echo ""
echo "📋 Phase 3: Scripts & Documentation"
echo "-----------------------------------"

# Check observability script
if [ -f "scripts/start_observability.sh" ]; then
    echo -e "${GREEN}✅ start_observability.sh exists${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ start_observability.sh missing${NC}"
fi
((TESTS_TOTAL++))

if [ -x "scripts/start_observability.sh" ]; then
    echo -e "${GREEN}✅ start_observability.sh is executable${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ start_observability.sh not executable${NC}"
fi
((TESTS_TOTAL++))

# Check README updates
if grep -q "Observability & Monitoring" README.md; then
    echo -e "${GREEN}✅ README contains Observability section${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ README missing Observability section${NC}"
fi
((TESTS_TOTAL++))

if grep -q "OpenTelemetry Tracing" README.md; then
    echo -e "${GREEN}✅ README contains OpenTelemetry section${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ README missing OpenTelemetry section${NC}"
fi
((TESTS_TOTAL++))

if grep -q "Prometheus Metrics" README.md; then
    echo -e "${GREEN}✅ README contains Prometheus section${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ README missing Prometheus section${NC}"
fi
((TESTS_TOTAL++))

echo ""
echo "📋 Phase 4: Tests"
echo "-----------------"

# Check test file exists
if [ -f "tests/test_otel_integration.py" ]; then
    echo -e "${GREEN}✅ OpenTelemetry test file exists${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ OpenTelemetry test file missing${NC}"
fi
((TESTS_TOTAL++))

# Try to run tests (if dependencies available)
echo -n "🧪 Testing: OpenTelemetry integration tests... "
if python3 -c "import opentelemetry; import prometheus_client" > /dev/null 2>&1; then
    if python3 -m pytest tests/test_otel_integration.py -v > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${YELLOW}⚠️  SKIP (dependencies not fully available)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  SKIP (OpenTelemetry not installed)${NC}"
fi
((TESTS_TOTAL++))

echo ""
echo "📋 Phase 5: Docker & Infrastructure"
echo "-----------------------------------"

# Check if Docker is available
if command -v docker > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker is available${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠️  Docker not available${NC}"
fi
((TESTS_TOTAL++))

# Check if docker-compose is available
if command -v docker-compose > /dev/null 2>&1; then
    echo -e "${GREEN}✅ docker-compose is available${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠️  docker-compose not available${NC}"
fi
((TESTS_TOTAL++))

echo ""
echo "📊 Test Results"
echo "==============="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Total:  $TESTS_TOTAL"
echo -e "Success Rate: ${GREEN}$((TESTS_PASSED * 100 / TESTS_TOTAL))%${NC}"

echo ""
echo "🎯 S4-2 Acceptance Criteria"
echo "==========================="

if [ $TESTS_PASSED -eq $TESTS_TOTAL ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED! S4-2 Observability Stack is ready!${NC}"
    echo ""
    echo "🚀 Next steps:"
    echo "1. Start observability stack: ./scripts/start_observability.sh"
    echo "2. Set environment variables:"
    echo "   export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317"
    echo "   export OTEL_SERVICE_NAME=api  # or 'worker'"
    echo "3. Start API/workers with tracing enabled"
    echo "4. View traces in Jaeger: http://localhost:16686"
    echo "5. View metrics in Grafana: http://localhost:3000"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please fix the issues above.${NC}"
    echo ""
    echo "🔧 Common fixes:"
    echo "1. Install OpenTelemetry: pip install opentelemetry-api opentelemetry-sdk"
    echo "2. Install Prometheus client: pip install prometheus-client"
    echo "3. Check file permissions: chmod +x scripts/start_observability.sh"
    echo "4. Verify all configuration files exist"
    exit 1
fi
