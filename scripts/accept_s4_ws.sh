#!/bin/bash

# S4-1 WebSocket Acceptance Script
# Проверяет развязку воркеров и API через Redis Pub/Sub

set -e

echo "🔍 S4-1 WebSocket Acceptance Check"
echo "=================================="

# 1. Проверяем отсутствие импортов API в workers
echo "1️⃣ Checking for API imports in workers..."
if grep -R "from api.websocket" workers/ 2>/dev/null; then
    echo "❌ Found API imports in workers - FAILED"
    exit 1
else
    echo "✅ No API imports found in workers"
fi

# 2. Проверяем Redis подключение
echo "2️⃣ Testing Redis connection..."
if redis-cli PING | grep -q "PONG"; then
    echo "✅ Redis connection successful"
else
    echo "❌ Redis connection failed"
    exit 1
fi

# 3. Запускаем smoke тест
echo "3️⃣ Running WebSocket smoke test..."
if python scripts/ws_smoke.py; then
    echo "✅ WebSocket smoke test passed"
else
    echo "❌ WebSocket smoke test failed"
    exit 1
fi

echo ""
echo "🎉 S4-1 WebSocket acceptance check PASSED!"
echo "✅ Workers decoupled from API"
echo "✅ Redis Pub/Sub working"
echo "✅ WebSocket real-time status working"
