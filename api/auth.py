"""Authentication and authorization utilities."""

import hashlib
import os
from typing import Any, Optional

import jwt
from fastapi import Depends, HTTPException, Request, WebSocket, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from api.dependencies.db import get_db_lazy

security = HTTPBearer(auto_error=False)


async def get_current_user_ws(websocket: WebSocket) -> Optional[dict[str, Any]]:
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

        # Try JWT first, then API key
        user = await validate_jwt_token(token)
        if user:
            return user

        # Try API key with proper DB session
        try:
            from api.dependencies.db import get_db_lazy

            db_gen = get_db_lazy()
            try:
                db = next(db_gen)
                user = await validate_api_key(token, db)
                if user:
                    return user
            finally:
                try:
                    next(db_gen)
                except StopIteration:
                    pass
        except Exception:
            pass

        return None

    except Exception:
        return None


async def get_current_user_dict(
    request: Request, db: Session = Depends(get_db_lazy)
) -> dict[str, Any]:
    """Get current user from request as dictionary.

    Returns:
        Dict with keys: tenant_id, user_id, role, email

    Note: This function returns a dictionary and is used by ingest routes and websockets.
    For SQLAlchemy User objects, use get_current_user from api.dependencies.auth.
    """
    if not require_auth():
        return {"tenant_id": "anonymous", "user_id": "anonymous", "role": "user"}

    # Get authorization header
    auth_header = request.headers.get("authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
        )

    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )

    token = auth_header[7:]

    # Try JWT first
    user = await validate_jwt_token(token)
    if user:
        return user

    # Try API key
    user = await validate_api_key(token, db)
    if user:
        return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token or API key"
    )


async def get_current_user_optional(
    request: Request, db: Session = Depends(get_db_lazy)
) -> Optional[dict[str, Any]]:
    """Get current user from request (optional)."""
    if not require_auth():
        return {"tenant_id": "anonymous", "user_id": "anonymous", "role": "user"}

    try:
        return await get_current_user_dict(request, db)
    except HTTPException:
        return None


async def validate_jwt_token(token: str) -> Optional[dict[str, Any]]:
    """Validate JWT token."""
    secret = os.getenv("NEXTAUTH_SECRET")
    if not secret:
        return None

    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return {
            "tenant_id": payload.get("tenant_id"),
            "user_id": payload.get("user_id"),
            "role": payload.get("role", "user"),
        }
    except jwt.InvalidTokenError:
        return None


async def validate_api_key(api_key: str, db: Session) -> Optional[dict[str, Any]]:
    """Validate API key."""
    # Hash the API key
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    # Check if key exists and is not revoked
    try:
        from db.models import APIKey

        db_key = (
            db.query(APIKey)
            .filter(APIKey.key_hash == key_hash, APIKey.revoked_at.is_(None))
            .first()
        )

        if not db_key:
            return None

        return {
            "tenant_id": db_key.tenant_id,
            "user_id": f"api_key_{db_key.id}",
            "role": db_key.role,
        }
    except Exception:
        return None


def require_auth() -> bool:
    """Check if authentication is required.

    Defaults to true to ensure secure API access.
    Set REQUIRE_AUTH=false to disable authentication for development/testing.
    """
    return os.getenv("REQUIRE_AUTH", "true").lower() == "true"
