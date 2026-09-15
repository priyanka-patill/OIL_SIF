import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class SafetyReport(Base):
    __tablename__ = "safety_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    original_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    
    # 100% untouched raw source data representation
    raw_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Canonical Internal Model Fields (All strictly optional/nullable)
    report_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    refinery_unit: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    equipment: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    work_type: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    report_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    hazard: Mapped[str | None] = mapped_column(Text, nullable=True)
    unsafe_act: Mapped[str | None] = mapped_column(Text, nullable=True)
    unsafe_condition: Mapped[str | None] = mapped_column(Text, nullable=True)
    ppe_issue: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    immediate_cause: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    potential_consequence: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    risk_level: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    sif_precursor: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    high_potential: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    previous_similar_reports: Mapped[int | None] = mapped_column(Integer, nullable=True)
    repeated_issue: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    supervisor_factor: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    maintenance_factor: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    corrective_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_status: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    
    # Action Assignment & Tracking Fields
    assigned_to: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    assigned_department: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    completion_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closure_verified_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    closure_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    action_comments: Mapped[str | None] = mapped_column(Text, nullable=True)

    source_dataset: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Direct Supervisor & Submission Metadata
    analysis_status: Mapped[str] = mapped_column(String(50), default="COMPLETED", index=True)  # PENDING, IN_PROGRESS, COMPLETED, FAILED
    submitting_user: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    submitting_role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Factor Breakdown & Relationship Graph
    detected_factors: Mapped[list] = mapped_column(JSON, default=list)
    factor_count: Mapped[int] = mapped_column(Integer, default=0, index=True)
    relationship_type: Mapped[str] = mapped_column(String(50), default="independent_observation", index=True)
    related_report_ids: Mapped[list] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="reports")
