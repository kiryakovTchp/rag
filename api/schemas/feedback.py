"""Feedback API schemas."""

from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class FeedbackRequest(BaseModel):
    """Request schema for feedback submission."""
    answer_id: str
    rating: str  # 'up' or 'down'
    reason: Optional[str] = None
    selected_citation_ids: Optional[List[int]] = None


class FeedbackResponse(BaseModel):
    """Response schema for feedback submission."""
    id: int
    answer_id: str
    rating: str
    reason: Optional[str] = None
    selected_citation_ids: Optional[List[int]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackStats(BaseModel):
    """Statistics for feedback."""
    total_feedback: int
    positive_feedback: int
    negative_feedback: int
    positive_rate: float
