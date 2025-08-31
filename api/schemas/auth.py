"""Authentication schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class APIKeyCreate(BaseModel):
    """Schema for creating API key."""
    role: Optional[str] = "user"


class APIKeyResponse(BaseModel):
    """Schema for API key response (includes the key)."""
    id: int
    key: str  # Only returned once
    tenant_id: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class APIKeyList(BaseModel):
    """Schema for listing API keys (without the key)."""
    id: int
    tenant_id: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserInfo(BaseModel):
    """Schema for user information."""
    id: str
    email: str
    tenant_id: str
    role: str

    class Config:
        from_attributes = True
