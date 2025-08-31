"""Authentication dependencies."""

import os
import jwt
from typing import Optional
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.websockets import WebSocket

from db.models import User, APIKey
from db.session import get_db
from sqlalchemy.orm import Session

security = HTTPBearer(auto_error=False)


async def get_current_user_ws(websocket: WebSocket) -> Optional[User]:
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
            raise HTTPException(status_code=500, detail="NEXTAUTH_SECRET not configured")
        
        try:
            payload = jwt.decode(token, secret, algorithms=["HS256"])
            user_id = payload.get("sub")
            tenant_id = payload.get("tenant_id")
            
            if not user_id or not tenant_id:
                return None
            
            # Create user object
            user = User(
                id=user_id,
                tenant_id=tenant_id,
                email=payload.get("email", ""),
                role=payload.get("role", "user")
            )
            return user
            
        except jwt.InvalidTokenError:
            return None
            
    except Exception:
        return None


async def get_current_user_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[User]:
    """Get current user from API key."""
    if not credentials:
        return None
    
    api_key = credentials.credentials
    
    # Get database session
    db = next(get_db())
    
    try:
        # Find API key in database
        db_api_key = db.query(APIKey).filter(
            APIKey.key_hash == APIKey.hash_key(api_key),
            APIKey.revoked_at.is_(None)
        ).first()
        
        if not db_api_key:
            return None
        
        # Create user object
        user = User(
            id=f"api_{db_api_key.id}",
            tenant_id=db_api_key.tenant_id,
            email="",
            role=db_api_key.role
        )
        return user
        
    except Exception:
        return None
    finally:
        db.close()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get current user from JWT token or API key."""
    # Try API key first
    user = await get_current_user_api_key(credentials)
    if user:
        return user
    
    # Try JWT token
    token = None
    if credentials:
        token = credentials.credentials
    else:
        # Try to get from headers
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validate JWT token
    secret = os.getenv("NEXTAUTH_SECRET")
    if not secret:
        raise HTTPException(status_code=500, detail="NEXTAUTH_SECRET not configured")
    
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        
        if not user_id or not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create user object
        user = User(
            id=user_id,
            tenant_id=tenant_id,
            email=payload.get("email", ""),
            role=payload.get("role", "user")
        )
        return user
        
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_auth() -> bool:
    """Check if authentication is required."""
    return os.getenv("REQUIRE_AUTH", "true").lower() == "true"
