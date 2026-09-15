import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class NotificationConfig(Base):
    __tablename__ = "notification_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tier: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # SAFETY_HSE, DEPT_HEAD, MANAGEMENT
    role_name: Mapped[str] = mapped_column(String(100), nullable=False)        # e.g., "Safety / HSE Lead", "Operations Head"
    department: Mapped[str | None] = mapped_column(String(100), nullable=True) # e.g., "Operations", "Mechanical", "All"
    email_address: Mapped[str] = mapped_column(String(255), nullable=False)
    notify_on_high_risk: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_on_overdue: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_on_assignment: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
