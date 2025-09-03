"""API models for authentication and events."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class User(BaseModel):
    """User model for authentication."""

    id: str
    tenant_id: str
    email: str
    role: str = "user"
    is_active: bool = True


class JobEvent(BaseModel):
    """Job event model for WebSocket messages."""

    event: str  # parse_started|parse_progress|parse_done|parse_failed|chunk_*|embed_*
    job_id: int
    document_id: int
    type: str  # parse|chunk|embed
    progress: int = 0  # 0..100
    ts: datetime
    error: Optional[str] = None
