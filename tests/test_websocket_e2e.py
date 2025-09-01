"""End-to-end WebSocket tests with real FastAPI and Redis."""

import asyncio
import json
import pytest
import websockets
from typing import List, Dict, Any
from fastapi.testclient import TestClient
from unittest.mock import patch

from api.main import app
from services.events.bus import publish_event


class WebSocketE2ETest:
    """E2E WebSocket test runner."""

    def __init__(self):
        self.client = TestClient(app)
        self.received_messages: List[Dict[str, Any]] = []
        self.websocket = None

    async def connect_websocket(self, tenant_id: str = "test_tenant"):
        """Connect to WebSocket endpoint."""
        # Mock authentication for testing
        with patch("api.auth.get_current_user_ws") as mock_auth:
            mock_auth.return_value = {"tenant_id": tenant_id, "user_id": "test_user"}

            # Connect to WebSocket
            uri = "ws://localhost:8000/ws/jobs"
            self.websocket = await websockets.connect(uri)

            # Wait for connection confirmation
            message = await self.websocket.recv()
            data = json.loads(message)
            assert data["event"] == "connected"
            assert data["tenant_id"] == tenant_id

            print(f"✅ WebSocket connected for tenant {tenant_id}")

    async def listen_for_messages(self, timeout: int = 10):
        """Listen for WebSocket messages."""
        try:
            while True:
                message = await asyncio.wait_for(self.websocket.recv(), timeout=timeout)
                data = json.loads(message)
                self.received_messages.append(data)
                print(f"📨 Received: {data}")
        except asyncio.TimeoutError:
            print("⏰ Timeout waiting for messages")
        except Exception as e:
            print(f"❌ Error listening: {e}")

    async def publish_test_events(self, tenant_id: str = "test_tenant"):
        """Publish test events to Redis."""
        events = [
            {
                "event": "parse_started",
                "job_id": 123,
                "document_id": 456,
                "type": "parse",
                "progress": 0,
            },
            {
                "event": "parse_progress",
                "job_id": 123,
                "document_id": 456,
                "type": "parse",
                "progress": 50,
            },
            {
                "event": "parse_done",
                "job_id": 123,
                "document_id": 456,
                "type": "parse",
                "progress": 100,
            },
        ]

        for event in events:
            topic = f"{tenant_id}.jobs"
            success = await publish_event(topic, event)
            assert success, f"Failed to publish event: {event}"
            print(f"📤 Published: {event}")
            await asyncio.sleep(0.1)  # Small delay between events

    async def test_ping_pong(self):
        """Test ping/pong functionality."""
        ping_message = {"type": "ping"}
        await self.websocket.send(json.dumps(ping_message))

        # Wait for pong response
        message = await asyncio.wait_for(self.websocket.recv(), timeout=5)
        data = json.loads(message)
        assert data["type"] == "pong"
        print("✅ Ping/pong working")

    async def cleanup(self):
        """Clean up test resources."""
        if self.websocket:
            await self.websocket.close()
        print("🧹 Cleanup completed")


@pytest.mark.asyncio
async def test_websocket_e2e_redis_pubsub():
    """Test WebSocket with real Redis Pub/Sub."""
    test_runner = WebSocketE2ETest()

    try:
        # 1. Connect to WebSocket
        await test_runner.connect_websocket("test_tenant_123")

        # 2. Test ping/pong
        await test_runner.test_ping_pong()

        # 3. Start listening for messages in background
        listen_task = asyncio.create_task(test_runner.listen_for_messages(timeout=15))

        # 4. Wait a bit for listener to start
        await asyncio.sleep(0.5)

        # 5. Publish test events
        await test_runner.publish_test_events("test_tenant_123")

        # 6. Wait for messages and stop listening
        await asyncio.sleep(2)
        listen_task.cancel()

        # 7. Verify received messages
        assert (
            len(test_runner.received_messages) >= 3
        ), f"Expected 3+ messages, got {len(test_runner.received_messages)}"

        # Check message order and content
        messages = test_runner.received_messages
        assert any(m["event"] == "parse_started" for m in messages), "Missing parse_started event"
        assert any(m["event"] == "parse_progress" for m in messages), "Missing parse_progress event"
        assert any(m["event"] == "parse_done" for m in messages), "Missing parse_done event"

        # Check message structure
        for message in messages:
            assert "event" in message, f"Message missing event: {message}"
            assert "job_id" in message, f"Message missing job_id: {message}"
            assert "ts" in message, f"Message missing timestamp: {message}"
            assert "tenant_id" in message, f"Message missing tenant_id: {message}"

        print(f"✅ E2E test passed! Received {len(messages)} messages")

    except Exception as e:
        print(f"❌ E2E test failed: {e}")
        raise
    finally:
        await test_runner.cleanup()


@pytest.mark.asyncio
async def test_websocket_reconnection():
    """Test WebSocket reconnection handling."""
    test_runner = WebSocketE2ETest()

    try:
        # 1. Connect first time
        await test_runner.connect_websocket("test_tenant_reconnect")

        # 2. Close connection
        await test_runner.websocket.close()

        # 3. Reconnect
        await test_runner.connect_websocket("test_tenant_reconnect")

        # 4. Test functionality still works
        await test_runner.test_ping_pong()

        print("✅ Reconnection test passed!")

    except Exception as e:
        print(f"❌ Reconnection test failed: {e}")
        raise
    finally:
        await test_runner.cleanup()


@pytest.mark.asyncio
async def test_multiple_tenants():
    """Test multiple tenant isolation."""
    test_runner1 = WebSocketE2ETest()
    test_runner2 = WebSocketE2ETest()

    try:
        # 1. Connect two tenants
        await test_runner1.connect_websocket("tenant_a")
        await test_runner2.connect_websocket("tenant_b")

        # 2. Start listening
        listen1 = asyncio.create_task(test_runner1.listen_for_messages(timeout=10))
        listen2 = asyncio.create_task(test_runner2.listen_for_messages(timeout=10))

        await asyncio.sleep(0.5)

        # 3. Publish events to different tenants
        await test_runner1.publish_test_events("tenant_a")
        await test_runner2.publish_test_events("tenant_b")

        # 4. Wait and verify isolation
        await asyncio.sleep(2)
        listen1.cancel()
        listen2.cancel()

        # Tenant A should only receive tenant_a events
        tenant_a_messages = [
            m for m in test_runner1.received_messages if m.get("tenant_id") == "tenant_a"
        ]
        assert (
            len(tenant_a_messages) >= 3
        ), f"Tenant A should receive 3+ messages, got {len(tenant_a_messages)}"

        # Tenant B should only receive tenant_b events
        tenant_b_messages = [
            m for m in test_runner2.received_messages if m.get("tenant_id") == "tenant_b"
        ]
        assert (
            len(tenant_b_messages) >= 3
        ), f"Tenant B should receive 3+ messages, got {len(tenant_b_messages)}"

        print("✅ Multi-tenant isolation test passed!")

    except Exception as e:
        print(f"❌ Multi-tenant test failed: {e}")
        raise
    finally:
        await test_runner1.cleanup()
        await test_runner2.cleanup()


if __name__ == "__main__":
    # Run tests manually
    async def main():
        print("🚀 Starting WebSocket E2E tests...")

        await test_websocket_e2e_redis_pubsub()
        await test_websocket_reconnection()
        await test_multiple_tenants()

        print("🎉 All E2E tests completed!")

    asyncio.run(main())
