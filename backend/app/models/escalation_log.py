import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class EscalationLog(Base):
    """
    Idempotent Escalation Log model.
    Tracks each escalation event (Level 0 -> 1 -> 2 -> 3), preventing duplicate notification storms.
    """
    __tablename__ = "escalation_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    action_id: Mapped[str] = mapped_column(String(36), ForeignKey("safety_actions.id", ondelete="CASCADE"), nullable=False, index=True)

    escalation_level: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, 3
    previous_level: Mapped[int] = mapped_column(Integer, default=0)
    recipient_role: Mapped[str] = mapped_column(String(100), nullable=False)
    recipient_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    notification_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    escalated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    action: Mapped["SafetyAction"] = relationship("SafetyAction", foreign_keys=[action_id])
