"""Feedback schemas."""

from typing import Optional

from pydantic import BaseModel


class FeedbackCreate(BaseModel):
    """Feedback creation request."""

    answer_id: str
    rating: int  # 1-5 scale
    reason: Optional[str] = None
    selected_citation_ids: list[int] = []


class FeedbackResponse(BaseModel):
    """Feedback response."""

    id: int
    answer_id: str
    tenant_id: str
    user_id: Optional[str] = None
    rating: int
    reason: Optional[str] = None
    selected_citation_ids: list[int] = []
    created_at: str

    class Config:
        from_attributes = True


class FeedbackStats(BaseModel):
    """Statistics for feedback."""

    total_feedback: int
    positive_feedback: int
    negative_feedback: int
    positive_rate: float
