import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # DATASET_UPLOAD, DATASET_DELETE, SCHEMA_DETECTED, etc.
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)  # DATASET, REPORT, SCHEMA
    entity_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    client_host: Mapped[str | None] = mapped_column(String(100), nullable=True)
