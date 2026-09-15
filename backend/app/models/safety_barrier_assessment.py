import uuid
from datetime import datetime
from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class SafetyBarrierAssessment(Base):
    """
    Normalized barrier assessment model inspired by James Reason's Swiss Cheese Model.
    Tracks barrier defense layers, discrete states (INTACT, DEGRADED, FAILED, UNKNOWN),
    and structured evidence without claiming accident prediction or causation.
    """
    __tablename__ = "safety_barrier_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("safety_reports.id", ondelete="CASCADE"), nullable=True, index=True)
    dataset_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=True, index=True)

    # Dimensional anchors
    refinery_unit: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    equipment: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # Barrier metadata
    barrier_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    barrier_category: Mapped[str] = mapped_column(String(100), nullable=False)
    layer_index: Mapped[int] = mapped_column(Integer, default=1)

    # Discrete State: INTACT, DEGRADED, FAILED, UNKNOWN
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)

    # Structured Evidence & Provenance
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    source_report_ids: Mapped[list] = mapped_column(JSON, default=list)
    source_fields: Mapped[list] = mapped_column(JSON, default=list)
    is_cross_report: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    engine_version: Mapped[str] = mapped_column(String(50), default="v2.0.0")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    report: Mapped["SafetyReport"] = relationship("SafetyReport", foreign_keys=[report_id])
