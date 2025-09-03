"""JWT utilities for authentication."""

import os
import time
from typing import Optional

import jwt

from db.models import User


def create_access_token(data: dict, expires_delta: Optional[int] = None) -> str:
    """Create JWT access token.

    Args:
        data: Data to encode in token
        expires_delta: Token expiration time in seconds

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = time.time() + expires_delta
    else:
        expire = time.time() + 3600  # 1 hour default

    to_encode.update({"exp": expire})

    secret = os.getenv("JWT_SECRET_KEY")
    if not secret:
        raise ValueError("JWT_SECRET_KEY environment variable required")

    encoded_jwt = jwt.encode(to_encode, secret, algorithm="HS256")
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token.

    Args:
        token: JWT token to verify

    Returns:
        Decoded token data or None if invalid
    """
    try:
        secret = os.getenv("JWT_SECRET_KEY")
        if not secret:
            return None

        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        return None


def decode_token(token: str) -> Optional[dict]:
    """Decode JWT token (alias for verify_token).

    Args:
        token: JWT token to decode

    Returns:
        Decoded token data or None if invalid
    """
    return verify_token(token)


def create_user_token(user: User) -> str:
    """Create JWT token for user.

    Args:
        user: User object

    Returns:
        JWT token string
    """
    token_data = {
        "user_id": str(user.id),
        "tenant_id": user.tenant_id,
        "email": user.email,
        "role": user.role,
    }

    return create_access_token(token_data)
