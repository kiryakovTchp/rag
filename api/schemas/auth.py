"""Authentication schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    """User registration request."""

    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """User login request."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"


class UserInfo(BaseModel):
    """User information response."""

    id: int
    email: str
    tenant_id: Optional[str] = None
    role: str
    created_at: datetime


# Existing API key schemas
class APIKeyCreate(BaseModel):
    """API key creation request."""

    role: Optional[str] = "user"


class APIKeyResponse(BaseModel):
    """API key response."""

    id: int
    key: str
    tenant_id: str
    role: str
    created_at: datetime


class APIKeyList(BaseModel):
    """API key list item."""

    id: int
    tenant_id: str
    role: str
    created_at: datetime
