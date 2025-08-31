"""Feedback schemas."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class FeedbackCreate(BaseModel):
    """Schema for creating feedback."""
    answer_id: str
    rating: str  # 'up' or 'down'
    reason: Optional[str] = None
    selected_citation_ids: Optional[List[int]] = None


class FeedbackResponse(BaseModel):
    """Schema for feedback response."""
    id: int
    answer_id: str
    tenant_id: str
    user_id: Optional[str]
    rating: str
    reason: Optional[str]
    selected_citation_ids: Optional[List[int]]
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackStats(BaseModel):
    """Statistics for feedback."""
    total_feedback: int
    positive_feedback: int
    negative_feedback: int
    positive_rate: float
