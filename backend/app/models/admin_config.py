import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, JSON, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class AdminConfig(Base):
    """
    Persistent platform governance configurations:
    - BDI thresholds & methodology
    - SIF precursor thresholds
    - SLA durations and escalation roles
    - Notification channels & mock delivery mode
    - Demo / Simulation Mode state
    - AI Engine / Model version
    """
    __tablename__ = "admin_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    config_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    config_value: Mapped[dict] = mapped_column(JSON, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by: Mapped[str] = mapped_column(String(100), default="Administrator")
