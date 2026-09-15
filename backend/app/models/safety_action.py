import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey, JSON, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class SafetyAction(Base):
    """
    Normalized Agentic Safety Action model.
    Stores context-aware safety response packages, role assignments, SLA deadlines,
    human-in-the-loop approval statuses, and lifecycle state transitions.
    """
    __tablename__ = "safety_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id: Mapped[str] = mapped_column(String(36), ForeignKey("safety_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=True, index=True)

    # Action Classification & Type
    action_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, default="CONTAINMENT"
    )  # CONTAINMENT, CORRECTIVE_ACTION, PREVENTIVE_ACTION, SAFETY_HOLD_REQUEST, MANAGEMENT_ESCALATION, VERIFICATION
    severity: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, default="HIGH"
    )  # NORMAL, WATCH, ELEVATED, HIGH, CRITICAL

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Structured AI Recommendations & Full 19-Field Action Package
    ai_recommendation: Mapped[dict] = mapped_column(JSON, default=dict)
    action_package: Mapped[dict] = mapped_column(JSON, default=dict)

    # Role-Based Assignment
    assigned_role: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # Unit In-Charge, Safety Officer, HSE Head, Department Head, Plant Management, Executive Management, Administrator
    assigned_user: Mapped[str | None] = mapped_column(String(100), nullable=True, default="Unassigned")

    # SLA & Escalation
    sla_hours: Mapped[int] = mapped_column(Integer, default=24)
    sla_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True, default=1440)
    sla_deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sla_state: Mapped[str] = mapped_column(
        String(50), default="NORMAL"
    )  # NORMAL, APPROACHING_DEADLINE, BREACHED, ESCALATED, ACKNOWLEDGED, CONTAINED, VERIFIED, CLOSED
    escalation_level: Mapped[int] = mapped_column(Integer, default=0)

    # Action State Machine
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, default="PENDING_APPROVAL"
    )  # DRAFT, PENDING_APPROVAL, DISPATCHED, ACKNOWLEDGED, IN_PROGRESS, CONTAINED, AWAITING_VERIFICATION, VERIFIED, CLOSED, ESCALATED, REJECTED

    # Human Approval Governance
    approval_status: Mapped[str] = mapped_column(
        String(50), default="PENDING"
    )  # PENDING, APPROVED, REJECTED, AUTO_APPROVED
    approved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Lifecycle Milestones
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    containment_started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    remediation_completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    verified_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    report: Mapped["SafetyReport"] = relationship("SafetyReport", foreign_keys=[report_id])
    webhook_logs: Mapped[list["WebhookLog"]] = relationship("WebhookLog", back_populates="action", cascade="all, delete-orphan")
    escalation_logs: Mapped[list["EscalationLog"]] = relationship("EscalationLog", back_populates="action", cascade="all, delete-orphan")
