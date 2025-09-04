"""JWT utilities for authentication."""

import os
import time
from typing import Optional

import jwt

from api.config import get_settings


def _get_secret() -> str:
    """Return JWT secret key.

    Priority: JWT_SECRET_KEY, then NEXTAUTH_SECRET (for backward compatibility).
    """
    settings = get_settings()
    return (
        settings.jwt_secret_key
        or settings.nextauth_secret
        or os.getenv("JWT_SECRET_KEY")
        or os.getenv("NEXTAUTH_SECRET")
        or "dev_local_secret_change_me"
    )


def create_access_token(
    user_id: int,
    email: str,
    tenant_id: Optional[str] = None,
    role: str = "user",
    expires_delta: Optional[int] = None,
) -> str:
    """Create JWT access token.

    Args:
        user_id: User ID
        email: User email
        tenant_id: Tenant ID
        role: User role
        expires_delta: Token expiration time in seconds

    Returns:
        Encoded JWT token
    """
    to_encode = {
        "sub": str(user_id),
        "email": email,
        "tenant_id": tenant_id,
        "role": role,
    }

    expire = time.time() + (expires_delta or 3600)
    to_encode.update({"exp": expire})

    secret = _get_secret()
    encoded_jwt = jwt.encode(to_encode, secret, algorithm="HS256")
    return str(encoded_jwt)


def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token and return payload or None."""
    try:
        secret = _get_secret()
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        return None


def decode_token(token: str) -> Optional[dict]:
    """Decode JWT token (alias for verify_token)."""
    return verify_token(token)
