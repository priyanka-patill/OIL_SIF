import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class SLAPolicy(Base):
    """
    Configurable SLA Policy model.
    Stores dynamic SLA durations, warning/reminder intervals, and role escalation hierarchy.
    Demonstration default for CRITICAL is 60 minutes.
    """
    __tablename__ = "sla_policies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    severity: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)  # CRITICAL, HIGH, ELEVATED, WATCH, NORMAL

    # SLA Durations (in minutes)
    sla_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    reminder_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    warning_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    escalation_interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)

    # Configurable Escalation Hierarchy Roles
    escalation_level_0_role: Mapped[str] = mapped_column(String(100), default="Unit In-Charge")
    escalation_level_1_role: Mapped[str] = mapped_column(String(100), default="HSE Head")
    escalation_level_2_role: Mapped[str] = mapped_column(String(100), default="Plant Management")
    escalation_level_3_role: Mapped[str] = mapped_column(String(100), default="Executive Management")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
