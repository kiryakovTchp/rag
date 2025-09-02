"""Authentication dependencies."""

import os
from typing import Any, Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.websockets import WebSocket

# Lazy imports to prevent startup failures
# from db.models import User, APIKey
# from db.session import get_db

security = HTTPBearer(auto_error=False)

# Create dependency variables to avoid calling Depends in argument defaults
security_dep = security


async def get_current_user_ws(websocket: WebSocket) -> Optional[Any]:
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
        try:
            from api.utils.jwt import decode_token

            payload = decode_token(token)
            if not payload:
                return None

            user_id = payload.get("sub")
            tenant_id = payload.get("tenant_id")

            if not user_id:
                return None

            # Lazy import database models
            try:
                from db.models import User
            except ImportError:
                raise HTTPException(
                    status_code=503, detail="Database service temporarily unavailable"
                ) from None

            # Create user object
            user = User(
                id=int(user_id),
                tenant_id=tenant_id,
                email=payload.get("email", ""),
                role=payload.get("role", "user"),
            )
            return user

        except jwt.InvalidTokenError:
            return None

    except Exception:
        return None


async def get_current_user_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security_dep),  # noqa: B008
) -> Optional[Any]:
    """Get current user from API key."""
    if not credentials:
        return None

    api_key = credentials.credentials

    # Lazy import database dependencies
    try:
        from db.models import APIKey, User
        from db.session import get_db
    except ImportError:
        raise HTTPException(
            status_code=503, detail="Database service temporarily unavailable"
        ) from None

    # Get database session
    db = next(get_db())

    try:
        # Find API key in database
        db_api_key = (
            db.query(APIKey)
            .filter(
                APIKey.key_hash == APIKey.hash_key(api_key), APIKey.revoked_at.is_(None)
            )
            .first()
        )

        if not db_api_key:
            return None

        # Create user object
        user = User(
            id=f"api_{db_api_key.id}",
            tenant_id=db_api_key.tenant_id,
            email="",
            role=db_api_key.role,
        )
        return user

    except Exception:
        return None
    finally:
        db.close()


async def get_current_user_api_key_header(request: Request) -> Optional[Any]:
    """Get current user from X-API-Key header."""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return None

    # Lazy import database dependencies
    try:
        from db.models import APIKey, User
        from db.session import get_db
    except ImportError:
        raise HTTPException(
            status_code=503, detail="Database service temporarily unavailable"
        ) from None

    # Get database session
    db = next(get_db())

    try:
        # Find API key in database
        db_api_key = (
            db.query(APIKey)
            .filter(
                APIKey.key_hash == APIKey.hash_key(api_key), APIKey.revoked_at.is_(None)
            )
            .first()
        )

        if not db_api_key:
            return None

        # Create user object
        user = User(
            id=f"api_{db_api_key.id}",
            tenant_id=db_api_key.tenant_id,
            email="",
            role=db_api_key.role,
        )
        return user

    except Exception:
        return None
    finally:
        db.close()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security_dep),  # noqa: B008
) -> Any:
    """Get current user from JWT token or API key.

    Returns:
        SQLAlchemy User instance with attributes: id, tenant_id, email, role

    Note: This function returns a SQLAlchemy User object and is used by answer and auth routes.
    For dictionary users, use get_current_user_dict from api.auth.
    """
    # Try API key from Bearer token first
    user = await get_current_user_api_key(credentials)
    if user:
        return user

    # Try API key from X-API-Key header
    user = await get_current_user_api_key_header(request)
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
    try:
        from api.utils.jwt import decode_token

        payload = decode_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Lazy import database models
        try:
            from db.models import User
        except ImportError:
            raise HTTPException(
                status_code=503, detail="Database service temporarily unavailable"
            ) from None

        # Create user object
        user = User(
            id=int(user_id),
            tenant_id=tenant_id,
            email=payload.get("email", ""),
            role=payload.get("role", "user"),
        )
        return user

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None


def require_auth() -> bool:
    """Check if authentication is required.

    Defaults to true to ensure secure API access.
    Set REQUIRE_AUTH=false to disable authentication for development/testing.
    """
    return os.getenv("REQUIRE_AUTH", "true").lower() == "true"
