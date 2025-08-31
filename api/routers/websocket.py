"""WebSocket endpoints for real-time job status."""

import json
import logging
from typing import Dict, List
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import JSONResponse

from api.auth import get_current_user
from api.models import User

logger = logging.getLogger(__name__)

router = APIRouter()

# Store active WebSocket connections per tenant
active_connections: Dict[str, List[WebSocket]] = {}


class ConnectionManager:
    """Manage WebSocket connections per tenant."""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, tenant_id: str):
        """Connect a WebSocket for a tenant."""
        await websocket.accept()
        if tenant_id not in self.active_connections:
            self.active_connections[tenant_id] = []
        self.active_connections[tenant_id].append(websocket)
        logger.info(f"WebSocket connected for tenant {tenant_id}")
    
    def disconnect(self, websocket: WebSocket, tenant_id: str):
        """Disconnect a WebSocket for a tenant."""
        if tenant_id in self.active_connections:
            self.active_connections[tenant_id].remove(websocket)
            if not self.active_connections[tenant_id]:
                del self.active_connections[tenant_id]
        logger.info(f"WebSocket disconnected for tenant {tenant_id}")
    
    async def send_personal_message(self, message: dict, tenant_id: str):
        """Send message to all connections of a tenant."""
        if tenant_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[tenant_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Failed to send message to WebSocket: {e}")
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                self.disconnect(connection, tenant_id)


manager = ConnectionManager()


@router.websocket("/ws/jobs")
async def websocket_jobs(websocket: WebSocket):
    """WebSocket endpoint for job status updates."""
    try:
        # Accept connection first to get headers
        await websocket.accept()
        
        # Get authentication token from query params or headers
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=4001, reason="Authentication required")
            return
        
        # Validate token and get user
        try:
            # For now, we'll use a simple token validation
            # In production, this should validate JWT or API key
            if not token.startswith("Bearer "):
                await websocket.close(code=4001, reason="Invalid token format")
                return
            
            # Extract tenant_id from token (simplified for now)
            # In production, decode JWT and extract tenant_id
            tenant_id = "default"  # Placeholder
            
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        # Connect to manager
        await manager.connect(websocket, tenant_id)
        
        # Send initial connection message
        await websocket.send_text(json.dumps({
            "event": "connected",
            "tenant_id": tenant_id,
            "ts": datetime.utcnow().isoformat()
        }))
        
        # Keep connection alive
        try:
            while True:
                # Wait for any message (ping/pong or close)
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            manager.disconnect(websocket, tenant_id)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            manager.disconnect(websocket, tenant_id)
            
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        try:
            await websocket.close(code=1011, reason="Internal error")
        except:
            pass


# Function to emit job events (called from Celery tasks)
async def emit_job_event(tenant_id: str, event_data: dict):
    """Emit job event to all WebSocket connections of a tenant."""
    event_data["ts"] = datetime.utcnow().isoformat()
    await manager.send_personal_message(event_data, tenant_id)


# Export for use in Celery tasks
__all__ = ["emit_job_event"]
