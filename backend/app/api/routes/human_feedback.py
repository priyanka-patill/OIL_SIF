from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.human_feedback import (
    HumanFeedbackCreate,
    HumanFeedbackResponse,
    FeedbackStatsResponse
)
from app.services.feedback_service import FeedbackService

router = APIRouter(prefix="/feedback", tags=["Human Expert Feedback"])


@router.post("", response_model=HumanFeedbackResponse)
def submit_human_feedback(
    payload: HumanFeedbackCreate,
    db: Session = Depends(get_db)
):
    """
    Submit human review feedback (CORRECT, INCORRECT, PARTIALLY_CORRECT, NOT_USEFUL)
    for an AI safety assessment or barrier evaluation. Stored separately from source data.
    """
    return FeedbackService.submit_feedback(db, payload)


@router.get("", response_model=List[HumanFeedbackResponse])
def list_human_feedbacks(
    report_id: Optional[str] = Query(None, description="Filter by report ID"),
    rating: Optional[str] = Query(None, description="Filter by rating"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List recorded human feedback entries.
    """
    return FeedbackService.list_feedbacks(db, report_id=report_id, rating=rating, limit=limit, offset=offset)


@router.get("/stats", response_model=FeedbackStatsResponse)
def get_feedback_statistics(
    db: Session = Depends(get_db)
):
    """
    Retrieve aggregate statistics on human agreement rates and feedback categories.
    """
    return FeedbackService.get_feedback_stats(db)
