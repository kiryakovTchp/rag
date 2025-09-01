"""WebSocket endpoints for realtime job status via Redis Pub/Sub."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.auth import get_current_user_ws
from services.events.bus import subscribe_loop

router = APIRouter()

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections with Redis Pub/Sub integration."""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self._subscription_tasks: Dict[str, asyncio.Task] = {}

        async def connect(self, websocket: WebSocket, tenant_id: str):
        """Connect a new WebSocket client and subscribe to Redis channel."""
        await websocket.accept()
        if tenant_id not in self.active_connections:
            self.active_connections[tenant_id] = []
            # Start Redis subscription for this tenant
            try:
                await self._start_subscription(tenant_id)
            except Exception as e:
                logger.error(f"Failed to connect WebSocket for tenant {tenant_id}: {e}")
                await websocket.close(code=4000, reason="Redis connection failed")
                raise
        
        self.active_connections[tenant_id].append(websocket)
        logger.info(f"WebSocket connected for tenant {tenant_id}")

    def disconnect(self, websocket: WebSocket, tenant_id: str):
        """Disconnect a WebSocket client."""
        if tenant_id in self.active_connections:
            self.active_connections[tenant_id].remove(websocket)
            if not self.active_connections[tenant_id]:
                del self.active_connections[tenant_id]
                # Stop Redis subscription for this tenant
                self._stop_subscription(tenant_id)
                logger.info(f"WebSocket disconnected for tenant {tenant_id}")

        async def _start_subscription(self, tenant_id: str):
        """Start Redis subscription for tenant."""
        if tenant_id in self._subscription_tasks:
            return
        
        topic = f"{tenant_id}.jobs"
        try:
            task = asyncio.create_task(subscribe_loop(topic, self._handle_redis_message))
            self._subscription_tasks[tenant_id] = task
            logger.info(f"Started Redis subscription for {topic}")
        except Exception as e:
            logger.error(f"Failed to start Redis subscription for {topic}: {e}")
            # Close WebSocket connection with error code
            if tenant_id in self.active_connections:
                for connection in self.active_connections[tenant_id]:
                    try:
                        await connection.close(code=4000, reason="Redis connection failed")
                    except Exception:
                        pass
            raise

    def _stop_subscription(self, tenant_id: str):
        """Stop Redis subscription for tenant."""
        if tenant_id in self._subscription_tasks:
            task = self._subscription_tasks[tenant_id]
            if not task.done():
                task.cancel()
            del self._subscription_tasks[tenant_id]

    async def _handle_redis_message(self, message: dict):
        """Handle message from Redis and relay to WebSocket clients."""
        # Extract tenant_id from topic (assuming message contains it)
        tenant_id = message.get("tenant_id")
        if not tenant_id:
            logger.warning("Message missing tenant_id, cannot relay")
            return

        if tenant_id in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[tenant_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.warning(f"Failed to send to WebSocket: {e}")
                    dead_connections.append(connection)

            # Clean up dead connections
            for dead_connection in dead_connections:
                self.disconnect(dead_connection, tenant_id)

    async def send_personal_message(self, message: dict, tenant_id: str):
        """Send message to all connections of a tenant."""
        if tenant_id in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[tenant_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.warning(f"Failed to send personal message: {e}")
                    dead_connections.append(connection)

            # Clean up dead connections
            for dead_connection in dead_connections:
                self.disconnect(dead_connection, tenant_id)

    async def close_all(self):
        """Close all connections and subscriptions."""
        for tenant_id in list(self.active_connections.keys()):
            for connection in self.active_connections[tenant_id]:
                try:
                    await connection.close(code=1000, reason="Server shutdown")
                except Exception:
                    pass
            self._stop_subscription(tenant_id)
        self.active_connections.clear()


manager = ConnectionManager()


@router.websocket("/ws/jobs")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for job status updates via Redis Pub/Sub."""
    try:
        # Get user from WebSocket
        user = await get_current_user_ws(websocket)
        if not user:
            await websocket.close(code=4001, reason="Unauthorized")
            return

        tenant_id = user.get("tenant_id")
        if not tenant_id:
            await websocket.close(code=4002, reason="No tenant ID")
            return

        await manager.connect(websocket, tenant_id)

        try:
            # Send connection confirmation
            await websocket.send_text(
                json.dumps(
                    {
                        "event": "connected",
                        "tenant_id": tenant_id,
                        "ts": datetime.utcnow().isoformat() + "Z",
                    }
                )
            )

            # Keep connection alive with ping/pong
            while True:
                try:
                    data = await websocket.receive_text()
                    message = json.loads(data)

                    # Handle ping
                    if message.get("type") == "ping":
                        await websocket.send_text(
                            json.dumps({"type": "pong", "ts": datetime.utcnow().isoformat() + "Z"})
                        )

                except WebSocketDisconnect:
                    break
                except json.JSONDecodeError:
                    # Ignore invalid JSON
                    continue

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for tenant {tenant_id}")
        finally:
            manager.disconnect(websocket, tenant_id)

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=4000, reason=str(e))


# Export for use in API
__all__ = ["manager"]
