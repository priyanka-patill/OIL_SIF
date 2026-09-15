import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class WebhookLog(Base):
    """
    Normalized Webhook Delivery Log model.
    Stores dispatched webhook payloads, SHA-256 payload hashes, response codes,
    delivery statuses, and retry counts without exposing credentials.
    """
    __tablename__ = "webhook_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    action_id: Mapped[str] = mapped_column(String(36), ForeignKey("safety_actions.id", ondelete="CASCADE"), nullable=False, index=True)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)  # ACTION_CREATED, ACTION_DISPATCHED, SAFETY_HOLD, ESCALATION, STATUS_CHANGED
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256 hash for deduplication
    delivery_status: Mapped[str] = mapped_column(String(50), default="SUCCESS", index=True)  # SUCCESS, FAILED, PENDING
    response_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    action: Mapped["SafetyAction"] = relationship("SafetyAction", back_populates="webhook_logs")
