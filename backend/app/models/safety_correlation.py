import uuid
from datetime import datetime
from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class SafetyCorrelation(Base):
    """
    Normalized multi-factor safety correlation table.
    Stores evidence-based relationships between safety reports without claiming causation.
    """
    __tablename__ = "safety_correlations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_report_id: Mapped[str] = mapped_column(String(36), ForeignKey("safety_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    related_report_id: Mapped[str] = mapped_column(String(36), ForeignKey("safety_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Relationship categorization
    relationship_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    correlation_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    correlation_method: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Structured evidence & metadata
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    convergence_factors: Mapped[list] = mapped_column(JSON, default=list)
    
    # Cross-dataset provenance
    is_cross_dataset: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    source_dataset_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    related_dataset_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    engine_version: Mapped[str] = mapped_column(String(50), default="v1.0.0")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    source_report: Mapped["SafetyReport"] = relationship("SafetyReport", foreign_keys=[source_report_id])
    related_report: Mapped["SafetyReport"] = relationship("SafetyReport", foreign_keys=[related_report_id])
