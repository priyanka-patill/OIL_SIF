import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, JSON, Text, Float, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class SystemAuditLog(Base):
    """
    Immutable, comprehensive audit trail table for all platform lifecycle events:
    Detection, Correlation, Barrier assessment, BDI calculation, SIF escalation,
    Action creation, Approval, Notification, Safety hold, SLA reminder, SLA breach,
    Escalation, Acknowledgement, Containment, Verification, Closure, and Human feedback.
    """
    __tablename__ = "system_audit_logs"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    report_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    dataset_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    action_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    hold_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    
    # Event Classification
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    engine_version: Mapped[str] = mapped_column(String(50), default="2.0.0-phase8")
    trigger: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Structured Analytical Payloads
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    bdi: Mapped[float | None] = mapped_column(Float, nullable=True)
    sif_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    severity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Operational Action & Governance States
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    human_decision: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notification_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    escalation_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    final_resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Audit Meta
    actor: Mapped[str] = mapped_column(String(100), default="AI Safety Engine")
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    client_host: Mapped[str | None] = mapped_column(String(100), nullable=True)
