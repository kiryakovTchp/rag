"""WebSocket endpoint for real-time communication."""

import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from api.auth import get_current_user_ws
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
        tenant_id = user.get("tenant_id", "unknown")
        user_id = user.get("user_id", "unknown")

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


@router.post("/publish/{topic}")
async def publish_message(topic: str, message: dict[str, Any]):
    """Publish message to topic."""
    try:
        await publish_event(topic, message)
        return {"status": "published", "topic": topic}
    except Exception as e:
        logger.error(f"Failed to publish message: {e}")
        return {"error": "Failed to publish message"}
