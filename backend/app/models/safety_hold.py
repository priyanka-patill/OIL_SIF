import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class SafetyHold(Base):
    """
    Normalized Digital Safety Hold model.
    Implements an application-level permit/JSA freeze workflow:
    NORMAL -> SAFETY_HOLD_REQUESTED -> SAFETY_OFFICER_REVIEW -> HOLD_APPROVED -> WORKFLOW_BLOCKED -> REASSESSMENT -> RELEASE_REQUESTED -> VERIFIED -> RELEASED.
    Note: Does not directly operate refinery equipment or DCS unless an authorized external integration exists.
    """
    __tablename__ = "safety_holds"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("safety_reports.id", ondelete="CASCADE"), nullable=True, index=True)
    action_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("safety_actions.id", ondelete="CASCADE"), nullable=True, index=True)

    # Optional Permit & JSA Identifiers (never invented if not available in dataset/input)
    permit_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    jsa_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # Location & Equipment Context
    refinery_unit: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    equipment: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # Trigger & Precursor Indicators
    trigger: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g., "CRITICAL SIF Precursor", "Multiple Barrier Degradation", "Manual Hold Request"
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    bdi: Mapped[float | None] = mapped_column(Float, nullable=True)
    sif_status: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # State Machine: NORMAL, SAFETY_HOLD_REQUESTED, SAFETY_OFFICER_REVIEW, HOLD_APPROVED, WORKFLOW_BLOCKED, REASSESSMENT, RELEASE_REQUESTED, VERIFIED, RELEASED
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True, default="SAFETY_HOLD_REQUESTED")

    # Governance Actors
    requested_by: Mapped[str] = mapped_column(String(100), nullable=False)
    reviewed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    released_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    verified_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    verification_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Milestones
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    report: Mapped["SafetyReport"] = relationship("SafetyReport", foreign_keys=[report_id])
    action: Mapped["SafetyAction"] = relationship("SafetyAction", foreign_keys=[action_id])
