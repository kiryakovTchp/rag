"""WebSocket endpoints for realtime status updates."""

import json
import asyncio
from datetime import datetime
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import JSONResponse

from api.dependencies.auth import get_current_user_ws
from db.models import User

router = APIRouter()

# Store active connections per tenant
active_connections: Dict[str, Set[WebSocket]] = {}


class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, tenant_id: str):
        """Connect a new WebSocket client."""
        await websocket.accept()
        if tenant_id not in self.active_connections:
            self.active_connections[tenant_id] = set()
        self.active_connections[tenant_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, tenant_id: str):
        """Disconnect a WebSocket client."""
        if tenant_id in self.active_connections:
            self.active_connections[tenant_id].discard(websocket)
            if not self.active_connections[tenant_id]:
                del self.active_connections[tenant_id]
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific WebSocket."""
        await websocket.send_text(json.dumps(message))
    
    async def broadcast_to_tenant(self, message: dict, tenant_id: str):
        """Broadcast message to all connections of a tenant."""
        if tenant_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[tenant_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    disconnected.add(connection)
            
            # Clean up disconnected connections
            for connection in disconnected:
                self.active_connections[tenant_id].discard(connection)
            
            if not self.active_connections[tenant_id]:
                del self.active_connections[tenant_id]


manager = ConnectionManager()


@router.websocket("/ws/jobs")
async def websocket_jobs(websocket: WebSocket):
    """WebSocket endpoint for job status updates."""
    try:
        # Authenticate user
        user = await get_current_user_ws(websocket)
        if not user:
            await websocket.close(code=4001, reason="Authentication required")
            return
        
        tenant_id = user.tenant_id
        if not tenant_id:
            await websocket.close(code=4002, reason="Tenant ID required")
            return
        
        # Connect to WebSocket
        await manager.connect(websocket, tenant_id)
        
        # Send initial connection confirmation
        await manager.send_personal_message({
            "event": "connected",
            "tenant_id": tenant_id,
            "ts": datetime.utcnow().isoformat()
        }, websocket)
        
        # Keep connection alive
        try:
            while True:
                # Wait for any message (ping/pong or disconnect)
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            manager.disconnect(websocket, tenant_id)
            
    except Exception as e:
        try:
            await websocket.close(code=4000, reason=str(e))
        except:
            pass


# Function to emit job events (called from Celery tasks)
async def emit_job_event(tenant_id: str, event_data: dict):
    """Emit job event to all connected clients of a tenant."""
    event_data["ts"] = datetime.utcnow().isoformat()
    await manager.broadcast_to_tenant(event_data, tenant_id)


# Synchronous wrapper for Celery tasks
def emit_job_event_sync(tenant_id: str, event_data: dict):
    """Synchronous wrapper for emitting job events from Celery."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Create task if loop is running
            asyncio.create_task(emit_job_event(tenant_id, event_data))
        else:
            # Run in new event loop if none exists
            asyncio.run(emit_job_event(tenant_id, event_data))
    except RuntimeError:
        # Fallback for Celery worker environment
        pass
