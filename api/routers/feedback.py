"""Feedback API router."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_db
from api.auth import get_current_user
from api.schemas.feedback import FeedbackRequest, FeedbackResponse, FeedbackStats
from db.models import AnswerFeedback

router = APIRouter()


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
) -> FeedbackResponse:
    """Submit feedback for an answer."""
    # Validate rating
    if request.rating not in ['up', 'down']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be 'up' or 'down'"
        )
    
    # Get user info
    tenant_id = user.get("tenant_id")
    user_id = user.get("user_id")
    
    # Create feedback record
    feedback = AnswerFeedback(
        answer_id=request.answer_id,
        tenant_id=tenant_id,
        user_id=user_id,
        rating=request.rating,
        reason=request.reason,
        selected_citation_ids=request.selected_citation_ids
    )
    
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    
    return FeedbackResponse(
        id=feedback.id,
        answer_id=feedback.answer_id,
        rating=feedback.rating,
        reason=feedback.reason,
        selected_citation_ids=feedback.selected_citation_ids,
        created_at=feedback.created_at
    )


@router.get("/feedback/{answer_id}", response_model=List[FeedbackResponse])
async def get_feedback_for_answer(
    answer_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
) -> List[FeedbackResponse]:
    """Get feedback for a specific answer."""
    tenant_id = user.get("tenant_id")
    
    feedback_list = db.query(AnswerFeedback).filter(
        AnswerFeedback.answer_id == answer_id,
        AnswerFeedback.tenant_id == tenant_id
    ).all()
    
    return [
        FeedbackResponse(
            id=feedback.id,
            answer_id=feedback.answer_id,
            rating=feedback.rating,
            reason=feedback.reason,
            selected_citation_ids=feedback.selected_citation_ids,
            created_at=feedback.created_at
        )
        for feedback in feedback_list
    ]


@router.get("/feedback/stats", response_model=FeedbackStats)
async def get_feedback_stats(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
) -> FeedbackStats:
    """Get feedback statistics for the tenant."""
    tenant_id = user.get("tenant_id")
    
    # Get total feedback count
    total_feedback = db.query(AnswerFeedback).filter(
        AnswerFeedback.tenant_id == tenant_id
    ).count()
    
    # Get positive feedback count
    positive_feedback = db.query(AnswerFeedback).filter(
        AnswerFeedback.tenant_id == tenant_id,
        AnswerFeedback.rating == 'up'
    ).count()
    
    # Calculate negative feedback
    negative_feedback = total_feedback - positive_feedback
    
    # Calculate positive rate
    positive_rate = positive_feedback / total_feedback if total_feedback > 0 else 0.0
    
    return FeedbackStats(
        total_feedback=total_feedback,
        positive_feedback=positive_feedback,
        negative_feedback=negative_feedback,
        positive_rate=positive_rate
    )
