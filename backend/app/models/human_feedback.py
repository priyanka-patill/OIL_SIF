import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class HumanFeedback(Base):
    """
    Dedicated, separate table for storing human expert ratings and feedback
    on AI safety assessments, barrier analyses, BDI scores, and action plans.
    Maintains strict separation between original source data and feedback.
    """
    __tablename__ = "human_feedbacks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    analysis_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    action_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    
    # Reviewer info
    reviewer_name: Mapped[str] = mapped_column(String(100), default="Safety Officer")
    reviewer_role: Mapped[str] = mapped_column(String(100), default="Safety Officer")
    
    # Rating: CORRECT, INCORRECT, PARTIALLY_CORRECT, NOT_USEFUL
    rating: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Category: BDI_SCORING, BARRIER_CLASSIFICATION, SIF_PRECURSOR, ACTION_RECOMMENDATION, CORRELATION
    feedback_category: Mapped[str] = mapped_column(String(100), default="SIF_PRECURSOR")
    
    # Detailed feedback & corrections
    human_risk_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    human_sif_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Metadata
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
