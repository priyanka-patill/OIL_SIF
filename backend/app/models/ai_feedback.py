import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class AIFeedback(Base):
    __tablename__ = "ai_feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id: Mapped[str] = mapped_column(String(36), ForeignKey("safety_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_id: Mapped[str] = mapped_column(String(36), ForeignKey("report_analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_name: Mapped[str] = mapped_column(String(100), default="Safety Officer")
    agrees_with_ai: Mapped[bool] = mapped_column(Boolean, default=True)
    human_risk_level: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Low, Medium, High, Critical
    human_sif_precursor: Mapped[str | None] = mapped_column(String(50), nullable=True)  # YES, NO, UNCERTAIN
    feedback_reason: Mapped[str] = mapped_column(Text, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    analysis: Mapped["ReportAnalysis"] = relationship("ReportAnalysis", back_populates="feedback")
