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
if python3 scripts/ws_smoke.py; then
    echo "✅ WebSocket smoke test passed"
else
    echo "❌ WebSocket smoke test failed"
    exit 1
fi

# 4. Проверяем реальный WebSocket клиент
echo "4️⃣ Testing real WebSocket client..."
if python3 -c "
import asyncio
import websockets
import json
from services.events.bus import publish_event

async def test_real_ws():
    try:
        # Connect to WebSocket
        uri = 'ws://localhost:8000/ws/jobs'
        websocket = await websockets.connect(uri)
        
        # Wait for connection confirmation
        message = await asyncio.wait_for(websocket.recv(), timeout=5)
        data = json.loads(message)
        if data.get('event') != 'connected':
            raise Exception('Expected connected event')
        
        # Publish test event
        await publish_event('test_tenant.jobs', {
            'event': 'test_event',
            'job_id': 999,
            'document_id': 888,
            'type': 'test'
        })
        
        # Wait for event
        message = await asyncio.wait_for(websocket.recv(), timeout=5)
        data = json.loads(message)
        if data.get('event') != 'test_event':
            raise Exception('Expected test_event')
        
        await websocket.close()
        return True
    except Exception as e:
        print(f'WebSocket test failed: {e}')
        return False

result = asyncio.run(test_real_ws())
exit(0 if result else 1)
"; then
    echo "✅ Real WebSocket client test passed"
else
    echo "❌ Real WebSocket client test failed"
    exit 1
fi

echo ""
echo "🎉 S4-1 WebSocket acceptance check PASSED!"
echo "✅ Workers decoupled from API"
echo "✅ Redis Pub/Sub working"
echo "✅ WebSocket real-time status working"
