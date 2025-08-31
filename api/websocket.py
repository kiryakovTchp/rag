"""WebSocket endpoints for realtime job status."""

import json
import asyncio
from datetime import datetime
from typing import Dict, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import JSONResponse

from api.auth import get_current_user_ws
from services.job_manager import JobManager

router = APIRouter()

# Store active WebSocket connections per tenant
active_connections: Dict[str, List[WebSocket]] = {}

class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, tenant_id: str):
        """Connect a new WebSocket client."""
        await websocket.accept()
        if tenant_id not in self.active_connections:
            self.active_connections[tenant_id] = []
        self.active_connections[tenant_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, tenant_id: str):
        """Disconnect a WebSocket client."""
        if tenant_id in self.active_connections:
            self.active_connections[tenant_id].remove(websocket)
            if not self.active_connections[tenant_id]:
                del self.active_connections[tenant_id]
    
    async def send_personal_message(self, message: dict, tenant_id: str):
        """Send message to all connections of a tenant."""
        if tenant_id in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[tenant_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    dead_connections.append(connection)
            
            # Clean up dead connections
            for dead_connection in dead_connections:
                self.disconnect(dead_connection, tenant_id)

manager = ConnectionManager()

@router.websocket("/ws/jobs")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for job status updates."""
    try:
        # Get user from WebSocket (will be implemented in auth)
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
            while True:
                # Keep connection alive
                await websocket.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(websocket, tenant_id)
            
    except Exception as e:
        await websocket.close(code=4000, reason=str(e))

async def emit_job_event(tenant_id: str, event_data: dict):
    """Emit job event to WebSocket clients."""
    event = {
        "event": event_data["event"],
        "job_id": event_data["job_id"],
        "document_id": event_data.get("document_id"),
        "type": event_data["type"],
        "progress": event_data.get("progress", 0),
        "ts": datetime.utcnow().isoformat() + "Z"
    }
    
    await manager.send_personal_message(event, tenant_id)

# Export for use in Celery tasks
__all__ = ["emit_job_event", "manager"]
