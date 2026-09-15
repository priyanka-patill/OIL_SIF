import uuid
from datetime import datetime
from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey, JSON, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class SIFEscalationAssessment(Base):
    """
    Normalized SIF Precursor Escalation Assessment model.
    Stores multi-dimensional precursor severity (NORMAL, WATCH, ELEVATED, HIGH, CRITICAL),
    7-stage conceptual escalation scenario pathway, preventive intelligence, and explainability.
    Maintains complete separation from source SafetyReport records without claiming exact prediction.
    """
    __tablename__ = "sif_escalation_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("safety_reports.id", ondelete="CASCADE"), nullable=True, index=True)
    dataset_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=True, index=True)

    # Dimensional anchors
    refinery_unit: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    equipment: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # SIF Escalation Classification
    severity: Mapped[str] = mapped_column(String(50), nullable=False, index=True, default="NORMAL")  # NORMAL, WATCH, ELEVATED, HIGH, CRITICAL
    sif_precursor_status: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    sif_category: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Barrier & BDI Anchors
    bdi_score: Mapped[float] = mapped_column(Float, default=0.0)
    bdi_classification: Mapped[str] = mapped_column(String(50), default="MINIMAL")
    barrier_summary: Mapped[dict] = mapped_column(JSON, default=dict)

    # Multi-dimensional Reasoning & Evidence
    reasoning: Mapped[dict] = mapped_column(JSON, default=dict)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    contributing_factors: Mapped[list] = mapped_column(JSON, default=list)
    unresolved_items: Mapped[list] = mapped_column(JSON, default=list)

    # 7-Stage Escalation Scenario Pathway
    escalation_scenario: Mapped[list] = mapped_column(JSON, default=list)

    # Preventive Intelligence Payload (High / Critical)
    preventive_intelligence: Mapped[dict] = mapped_column(JSON, default=dict)

    # Recommended Actions
    immediate_actions: Mapped[list] = mapped_column(JSON, default=list)
    preventive_actions: Mapped[list] = mapped_column(JSON, default=list)

    confidence: Mapped[float] = mapped_column(Float, default=0.85)
    source_report_ids: Mapped[list] = mapped_column(JSON, default=list)
    engine_version: Mapped[str] = mapped_column(String(50), default="v4.0.0")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    report: Mapped["SafetyReport"] = relationship("SafetyReport", foreign_keys=[report_id])
