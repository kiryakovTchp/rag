"""JWT token utilities."""

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt

# JWT configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALG", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MIN", "60"))


def create_access_token(
    user_id: int, email: str, tenant_id: Optional[str] = None, role: str = "user"
) -> str:
    """Create a JWT access token.

    Args:
        user_id: User ID from database
        email: User email
        tenant_id: Optional tenant ID
        role: User role

    Returns:
        JWT token string

    Raises:
        ValueError: If JWT_SECRET_KEY is not configured
    """
    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY not configured")

    # Token payload
    payload = {
        "sub": str(user_id),
        "email": email,
        "tenant_id": tenant_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES),
        "iat": datetime.now(timezone.utc),
    }

    # Create token
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return str(token)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        Token payload if valid, None if invalid

    Raises:
        ValueError: If JWT_SECRET_KEY is not configured
    """
    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY not configured")

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.InvalidTokenError:
        return None
