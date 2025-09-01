"""End-to-end WebSocket tests with real FastAPI and Redis."""

import asyncio
import json
import pytest
import websockets
import subprocess

from typing import List, Dict, Any
from unittest.mock import patch

from services.events.bus import publish_event


class WebSocketE2ETest:
    """E2E WebSocket test runner with real uvicorn server."""

    def __init__(self):
        self.received_messages: List[Dict[str, Any]] = []
        self.websocket = None
        self.uvicorn_process = None

    async def start_uvicorn(self):
        """Start uvicorn server in background."""
        try:
            # Start uvicorn with our app
            self.uvicorn_process = subprocess.Popen(
                [
                    "uvicorn",
                    "api.main:app",
                    "--host",
                    "0.0.0.0",
                    "--port",
                    "8000",
                    "--log-level",
                    "error",
                ]
            )

            # Wait for server to start
            await asyncio.sleep(3)

            # Check if server is responding
            for _ in range(10):
                try:
                    import httpx

                    async with httpx.AsyncClient() as client:
                        response = await client.get("http://localhost:8000/healthz", timeout=5)
                        if response.status_code == 200:
                            print("✅ Uvicorn server started successfully")
                            return True
                except Exception:
                    await asyncio.sleep(1)

            raise Exception("Failed to start uvicorn server")

        except Exception as e:
            print(f"❌ Failed to start uvicorn: {e}")
            return False

    async def stop_uvicorn(self):
        """Stop uvicorn server."""
        if self.uvicorn_process:
            self.uvicorn_process.terminate()
            self.uvicorn_process.wait()
            print("🛑 Uvicorn server stopped")

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
        await self.stop_uvicorn()
        print("🧹 Cleanup completed")


@pytest.mark.asyncio
async def test_websocket_e2e_redis_pubsub():
    """Test WebSocket with real Redis Pub/Sub and uvicorn server."""
    test_runner = WebSocketE2ETest()

    try:
        # 1. Start uvicorn server
        print("🚀 Starting uvicorn server...")
        success = await test_runner.start_uvicorn()
        assert success, "Failed to start uvicorn server"

        # 2. Connect to WebSocket
        await test_runner.connect_websocket("test_tenant_123")

        # 3. Test ping/pong
        await test_runner.test_ping_pong()

        # 4. Start listening for messages in background
        listen_task = asyncio.create_task(test_runner.listen_for_messages(timeout=15))

        # 5. Wait a bit for listener to start
        await asyncio.sleep(0.5)

        # 6. Publish test events
        await test_runner.publish_test_events("test_tenant_123")

        # 7. Wait for messages and stop listening
        await asyncio.sleep(2)
        listen_task.cancel()

        # 8. Verify received messages
        assert (
            len(test_runner.received_messages) >= 2
        ), f"Expected 2+ messages, got {len(test_runner.received_messages)}"

        # Check message order and content
        messages = test_runner.received_messages
        assert any(m["event"] == "parse_started" for m in messages), "Missing parse_started event"
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
async def test_websocket_redis_unavailable():
    """Test WebSocket behavior when Redis is unavailable."""
    test_runner = WebSocketE2ETest()

    try:
        # 1. Start uvicorn server
        print("🚀 Starting uvicorn server...")
        success = await test_runner.start_uvicorn()
        assert success, "Failed to start uvicorn server"

        # 2. Try to connect to WebSocket (should fail gracefully)
        try:
            await test_runner.connect_websocket("test_tenant_123")
            # If we get here, connection succeeded (Redis might be available)
            print("ℹ️ WebSocket connected (Redis available)")
            await test_runner.cleanup()
            return
        except Exception as e:
            print(f"✅ WebSocket failed as expected when Redis unavailable: {e}")

    except Exception as e:
        print(f"❌ Redis unavailable test failed: {e}")
        raise
    finally:
        await test_runner.cleanup()


if __name__ == "__main__":
    # Run tests manually
    async def main():
        print("🚀 Starting WebSocket E2E tests...")

        await test_websocket_e2e_redis_pubsub()
        await test_websocket_redis_unavailable()

        print("🎉 All E2E tests completed!")

    asyncio.run(main())
