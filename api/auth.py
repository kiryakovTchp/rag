"""Authentication and authorization utilities."""

import jwt
import os
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, Request, WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user_ws(websocket: WebSocket) -> Optional[Dict[str, Any]]:
    """Get current user from WebSocket connection."""
    try:
        # Get token from query params or headers
        token = websocket.query_params.get("token")
        if not token:
            # Try to get from headers
            auth_header = websocket.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]
        
        if not token:
            return None
        
        # Validate JWT token
        secret = os.getenv("NEXTAUTH_SECRET")
        if not secret:
            return None
        
        try:
            payload = jwt.decode(token, secret, algorithms=["HS256"])
            return payload
        except jwt.InvalidTokenError:
            return None
            
    except Exception:
        return None

async def get_current_user(request: Request) -> Dict[str, Any]:
    """Get current user from request."""
    # For now, return a mock user
    # Will be implemented with proper JWT validation
    return {
        "tenant_id": "test_tenant",
        "user_id": "test_user",
        "role": "user"
    }

async def get_current_user_optional(request: Request) -> Optional[Dict[str, Any]]:
    """Get current user from request (optional)."""
    try:
        return await get_current_user(request)
    except:
        return None

def require_auth() -> bool:
    """Check if authentication is required."""
    return os.getenv("REQUIRE_AUTH", "false").lower() == "true"
