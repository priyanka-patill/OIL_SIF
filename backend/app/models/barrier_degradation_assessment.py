import uuid
from datetime import datetime
from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class BarrierDegradationAssessment(Base):
    """
    Normalized Barrier Degradation Index (BDI) assessment model.
    Stores the analytical score (0-100), classification (MINIMAL, LOW, MODERATE, HIGH, SEVERE),
    component point contributions, and structured explainability without claiming accident prediction.
    """
    __tablename__ = "barrier_degradation_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("safety_reports.id", ondelete="CASCADE"), nullable=True, index=True)
    dataset_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=True, index=True)

    # Dimensional anchors
    refinery_unit: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    equipment: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # BDI Core Scores & Classification
    bdi_score: Mapped[float] = mapped_column(Float, nullable=False, index=True, default=0.0)
    classification: Mapped[str] = mapped_column(String(50), nullable=False, index=True, default="MINIMAL")

    # Transparent Component Breakdown
    component_scores: Mapped[dict] = mapped_column(JSON, default=dict)
    contributing_factors: Mapped[list] = mapped_column(JSON, default=list)
    barrier_states_summary: Mapped[dict] = mapped_column(JSON, default=dict)

    # Explainability & Evidence
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    source_report_ids: Mapped[list] = mapped_column(JSON, default=list)

    calculation_version: Mapped[str] = mapped_column(String(50), default="v3.0.0")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    report: Mapped["SafetyReport"] = relationship("SafetyReport", foreign_keys=[report_id])
