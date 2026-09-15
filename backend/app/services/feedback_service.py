import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc

from app.models.human_feedback import HumanFeedback
from app.schemas.human_feedback import (
    HumanFeedbackCreate,
    HumanFeedbackResponse,
    FeedbackStatsResponse
)
from app.services.audit_service import AuditService


class FeedbackService:
    """
    Service for capturing human feedback on AI models, barrier assessments, and SIF precursors.
    Maintains strict separation of human corrections from raw observational source data.
    """

    @classmethod
    def submit_feedback(cls, db: Session, payload: HumanFeedbackCreate) -> HumanFeedbackResponse:
        feedback = HumanFeedback(
            id=str(uuid.uuid4()),
            report_id=str(payload.report_id),
            analysis_id=str(payload.analysis_id) if payload.analysis_id else None,
            action_id=str(payload.action_id) if payload.action_id else None,
            reviewer_name=payload.reviewer_name,
            reviewer_role=payload.reviewer_role,
            rating=payload.rating.upper(),
            feedback_category=payload.feedback_category.upper(),
            human_risk_level=payload.human_risk_level,
            human_sif_status=payload.human_sif_status,
            comments=payload.comments,
            is_simulated=payload.is_simulated,
            submitted_at=datetime.utcnow()
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        # Log audit trail event
        AuditService.log_event(
            db=db,
            event_type="HUMAN_FEEDBACK",
            trigger=f"Human Reviewer ({payload.reviewer_name}) rated assessment: {payload.rating}",
            report_id=payload.report_id,
            action_id=payload.action_id,
            human_decision=payload.rating,
            actor=f"{payload.reviewer_name} ({payload.reviewer_role})",
            is_simulated=payload.is_simulated,
            evidence={
                "category": payload.feedback_category,
                "human_risk_level": payload.human_risk_level,
                "human_sif_status": payload.human_sif_status,
                "comments": payload.comments
            }
        )

        return HumanFeedbackResponse.model_validate(feedback)

    @classmethod
    def list_feedbacks(
        cls,
        db: Session,
        report_id: Optional[str] = None,
        rating: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[HumanFeedbackResponse]:
        stmt = select(HumanFeedback)
        if report_id:
            stmt = stmt.where(HumanFeedback.report_id == str(report_id))
        if rating:
            stmt = stmt.where(HumanFeedback.rating == rating.upper())
        
        stmt = stmt.order_by(desc(HumanFeedback.submitted_at)).offset(offset).limit(limit)
        items = list(db.scalars(stmt).all())
        return [HumanFeedbackResponse.model_validate(i) for i in items]

    @classmethod
    def get_feedback_stats(cls, db: Session) -> FeedbackStatsResponse:
        total = db.scalar(select(func.count(HumanFeedback.id))) or 0

        # Ratings breakdown
        rating_rows = db.execute(
            select(HumanFeedback.rating, func.count(HumanFeedback.id))
            .group_by(HumanFeedback.rating)
        ).all()
        ratings_map = {row[0]: row[1] for row in rating_rows}

        # Categories breakdown
        cat_rows = db.execute(
            select(HumanFeedback.feedback_category, func.count(HumanFeedback.id))
            .group_by(HumanFeedback.feedback_category)
        ).all()
        cats_map = {row[0]: row[1] for row in cat_rows}

        # Agreement rate
        correct_count = ratings_map.get("CORRECT", 0)
        partially_count = ratings_map.get("PARTIALLY_CORRECT", 0)
        agreement_rate = 0.0
        if total > 0:
            agreement_rate = round(((correct_count + 0.5 * partially_count) / total) * 100.0, 1)

        recent = cls.list_feedbacks(db, limit=10)

        return FeedbackStatsResponse(
            total_feedback_count=total,
            agreement_rate_percentage=agreement_rate,
            ratings_breakdown=ratings_map,
            categories_breakdown=cats_map,
            recent_feedbacks=recent
        )
