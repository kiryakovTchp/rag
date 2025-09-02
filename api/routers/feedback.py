"""Feedback API router."""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies.auth import get_current_user
from api.dependencies.db import get_db_lazy
from api.schemas.feedback import FeedbackCreate, FeedbackResponse

router = APIRouter()


@router.post("/feedback", response_model=FeedbackResponse)
async def create_feedback(
    feedback_data: FeedbackCreate,
    current_user: Any = Depends(get_current_user),  # noqa: B008
    db: Session = Depends(get_db_lazy),  # noqa: B008
):
    """Create feedback for an answer."""
    # Validate that the answer belongs to the user's tenant
    # Note: In a real implementation, you'd want to verify the answer_id exists
    # and belongs to the current tenant

    # Create feedback record
    from db.models import AnswerFeedback

    feedback = AnswerFeedback(
        answer_id=feedback_data.answer_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id if not current_user.id.startswith("api_") else None,
        rating=feedback_data.rating,
        reason=feedback_data.reason,
        selected_citation_ids=feedback_data.selected_citation_ids,
    )

    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return FeedbackResponse(
        id=feedback.id,
        answer_id=feedback.answer_id,
        tenant_id=feedback.tenant_id,
        user_id=feedback.user_id,
        rating=feedback_data.rating,
        reason=feedback_data.reason,
        selected_citation_ids=feedback_data.selected_citation_ids,
        created_at=feedback.created_at,
    )


@router.get("/feedback/{answer_id}", response_model=list[FeedbackResponse])
async def get_feedback_for_answer(
    answer_id: str,
    current_user: Any = Depends(get_current_user),  # noqa: B008
    db: Session = Depends(get_db_lazy),  # noqa: B008
):
    """Get all feedback for a specific answer."""
    from db.models import AnswerFeedback

    feedback_list = (
        db.query(AnswerFeedback)
        .filter(
            AnswerFeedback.answer_id == answer_id,
            AnswerFeedback.tenant_id == current_user.tenant_id,
        )
        .all()
    )

    return [
        FeedbackResponse(
            id=feedback.id,
            answer_id=feedback.answer_id,
            tenant_id=feedback.tenant_id,
            user_id=feedback.user_id,
            rating=feedback.rating,
            reason=feedback.reason,
            selected_citation_ids=feedback.selected_citation_ids,
            created_at=feedback.created_at,
        )
        for feedback in feedback_list
    ]


@router.get("/feedback", response_model=list[FeedbackResponse])
async def get_feedback_summary(
    current_user: Any = Depends(get_current_user),  # noqa: B008
    db: Session = Depends(get_db_lazy),  # noqa: B008
    limit: int = 100,
    offset: int = 0,
):
    """Get feedback summary for the current tenant."""
    from db.models import AnswerFeedback

    feedback_list = (
        db.query(AnswerFeedback)
        .filter(AnswerFeedback.tenant_id == current_user.tenant_id)
        .order_by(AnswerFeedback.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        FeedbackResponse(
            id=feedback.id,
            answer_id=feedback.answer_id,
            tenant_id=feedback.tenant_id,
            user_id=feedback.user_id,
            rating=feedback.rating,
            reason=feedback.reason,
            selected_citation_ids=feedback.selected_citation_ids,
            created_at=feedback.created_at,
        )
        for feedback in feedback_list
    ]
