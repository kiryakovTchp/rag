"""WebSocket endpoint for real-time communication."""

import asyncio
import json
import logging
import os
from typing import Any

import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from api.dependencies.auth import get_current_user_ws
from services.events.bus import publish_event

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            f"WebSocket connected. Total connections: {len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(
            f"WebSocket disconnected. Total connections: {len(self.active_connections)}"
        )

    async def send_personal_message(
        self, message: dict[str, Any], websocket: WebSocket
    ):
        """Send message to specific WebSocket connection."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: dict[str, Any]):
        """Broadcast message to all active connections."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to broadcast message: {e}")
                disconnected.append(connection)

        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)


manager = ConnectionManager()


@router.get("/")
async def get():
    """WebSocket test page."""
    html = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>WebSocket Test</title>
        </head>
        <body>
            <h1>WebSocket Test</h1>
            <div id="messages"></div>
            <input type="text" id="messageText" placeholder="Type a message...">
            <button onclick="sendMessage()">Send</button>
            <script>
                var ws = new WebSocket("ws://localhost:8000/ws");
                ws.onmessage = function(event) {
                    var messages = document.getElementById('messages');
                    var message = document.createElement('div');
                    message.textContent = event.data;
                    messages.appendChild(message);
                };
                function sendMessage() {
                    var input = document.getElementById("messageText");
                    ws.send(input.value);
                    input.value = '';
                }
            </script>
        </body>
    </html>
    """
    return HTMLResponse(html)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication."""
    await manager.connect(websocket)

    try:
        # Authenticate user
        user = await get_current_user_ws(websocket)
        if not user:
            await websocket.send_text(json.dumps({"error": "Authentication required"}))
            return

        # Subscribe to user's events
        tenant_id = getattr(user, "tenant_id", "unknown")
        user_id = getattr(user, "id", "unknown")

        logger.info(f"User {user_id} connected to WebSocket for tenant {tenant_id}")

        # Send welcome message
        await manager.send_personal_message(
            {"type": "connected", "user_id": user_id, "tenant_id": tenant_id}, websocket
        )

        # Handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle different message types
                if message.get("type") == "subscribe":
                    # Subscribe to specific events
                    topic = message.get("topic", f"tenant.{tenant_id}")
                    await websocket.send_text(
                        json.dumps({"type": "subscribed", "topic": topic})
                    )

                elif message.get("type") == "ping":
                    # Respond to ping
                    await websocket.send_text(json.dumps({"type": "pong"}))

                else:
                    # Echo back unknown messages
                    await websocket.send_text(
                        json.dumps({"type": "echo", "data": message})
                    )

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"error": "Invalid JSON"}))
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await websocket.send_text(json.dumps({"error": "Internal error"}))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        manager.disconnect(websocket)


@router.websocket("/ws/jobs")
async def websocket_jobs(websocket: WebSocket):
    """WebSocket endpoint for job events via Redis Pub/Sub."""
    await websocket.accept()

    # Auth
    user = await get_current_user_ws(websocket)
    if not user:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    tenant_id = getattr(user, "tenant_id", None) or websocket.query_params.get(
        "tenant_id"
    )
    if not tenant_id:
        await websocket.close(code=4002, reason="No tenant_id provided")
        return

    # Connect Redis
    try:
        from api.config import get_settings

        redis_url = get_settings().redis_url or os.getenv(
            "REDIS_URL", "redis://localhost:6379"
        )
    except Exception:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    try:
        redis = aioredis.from_url(redis_url)
        pubsub = redis.pubsub()
        topic = f"{tenant_id}.jobs"
        await pubsub.subscribe(topic)
    except Exception:
        try:
            await websocket.close(code=4000, reason="Redis unavailable")
        finally:
            return

    # Send connected event
    await websocket.send_text(
        json.dumps({"event": "connected", "tenant_id": tenant_id})
    )

    async def redis_listener():
        try:
            async for message in pubsub.listen():
                if message.get("type") == "message":
                    try:
                        payload = json.loads(message.get("data"))
                    except Exception:
                        payload = {"error": "Invalid JSON"}
                    await websocket.send_text(json.dumps(payload))
        except Exception as e:
            logger.error(f"Redis listener error: {e}")

    async def ws_listener():
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    msg = json.loads(data)
                    if msg.get("type") == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                except json.JSONDecodeError:
                    await websocket.send_text(json.dumps({"error": "Invalid JSON"}))
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.error(f"WebSocket listener error: {e}")

    try:
        await asyncio.gather(redis_listener(), ws_listener())
    except WebSocketDisconnect:
        pass
    finally:
        try:
            await pubsub.unsubscribe(topic)
            await pubsub.close()
        except Exception:
            pass
        try:
            await redis.close()
        except Exception:
            pass


@router.post("/publish/{topic}")
async def publish_message(topic: str, message: dict[str, Any]):
    """Publish message to topic."""
    try:
        await publish_event(topic, message)
        return {"status": "published", "topic": topic}
    except Exception as e:
        logger.error(f"Failed to publish message: {e}")
        return {"error": "Failed to publish message"}
