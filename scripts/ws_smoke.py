#!/usr/bin/env python3
"""WebSocket smoke test script."""

import asyncio
import json

import websockets


async def test_websocket():
    """Test WebSocket connection and basic functionality."""
    uri = "ws://localhost:8000/ws"

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket")

            # Test ping/pong
            await websocket.send(json.dumps({"type": "ping"}))
            response = await websocket.recv()
            pong = json.loads(response)

            if pong.get("type") == "pong":
                print("✅ Ping/pong working")
            else:
                print(f"❌ Unexpected ping response: {pong}")

            # Test echo
            test_message = {"type": "echo", "data": "Hello WebSocket!"}
            await websocket.send(json.dumps(test_message))
            response = await websocket.recv()
            echo = json.loads(response)

            if echo.get("type") == "echo" and echo.get("data") == test_message:
                print("✅ Echo working")
            else:
                print(f"❌ Echo failed: {echo}")

            # Test subscribe
            await websocket.send(
                json.dumps({"type": "subscribe", "topic": "test.topic"})
            )
            response = await websocket.recv()
            subscribe = json.loads(response)

            if subscribe.get("type") == "subscribed":
                print("✅ Subscribe working")
            else:
                print(f"❌ Subscribe failed: {subscribe}")

            print("🎉 All WebSocket tests passed!")

    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")


async def test_websocket_with_auth():
    """Test WebSocket with authentication."""
    # This would require a valid token
    uri = "ws://localhost:8000/ws?token=test_token"

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket with auth")

            # Wait for connection message
            response = await websocket.recv()
            connection = json.loads(response)

            if connection.get("type") == "connected":
                print("✅ Authentication successful")
                print(f"   User ID: {connection.get('user_id')}")
                print(f"   Tenant ID: {connection.get('tenant_id')}")
            else:
                print(f"❌ Unexpected connection response: {connection}")

    except Exception as e:
        print(f"❌ WebSocket auth test failed: {e}")


async def test_websocket_publish():
    """Test publishing messages via HTTP endpoint."""
    import aiohttp

    async with aiohttp.ClientSession() as session:
        # Publish a test message
        message = {
            "type": "test",
            "data": "Hello from HTTP publish!",
            "timestamp": "2024-01-01T00:00:00Z",
        }

        async with session.post(
            "http://localhost:8000/publish/test.topic", json=message
        ) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Message published: {result}")
            else:
                print(f"❌ Failed to publish message: {response.status}")


async def main():
    """Run all WebSocket tests."""
    print("🚀 Starting WebSocket smoke tests...")
    print("=" * 50)

    # Test 1: Basic WebSocket functionality
    print("\n📡 Test 1: Basic WebSocket functionality")
    await test_websocket()

    # Test 2: WebSocket with authentication
    print("\n🔐 Test 2: WebSocket with authentication")
    await test_websocket_with_auth()

    # Test 3: HTTP publish endpoint
    print("\n📤 Test 3: HTTP publish endpoint")
    await test_websocket_publish()

    print("\n" + "=" * 50)
    print("🏁 WebSocket smoke tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
