import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class DataQualitySummary(Base):
    __tablename__ = "data_quality_summaries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    calculated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    total_columns: Mapped[int] = mapped_column(Integer, default=0)
    valid_records_count: Mapped[int] = mapped_column(Integer, default=0)
    missing_values_count: Mapped[int] = mapped_column(Integer, default=0)
    duplicate_ids_count: Mapped[int] = mapped_column(Integer, default=0)
    invalid_dates_count: Mapped[int] = mapped_column(Integer, default=0)
    constant_fields_count: Mapped[int] = mapped_column(Integer, default=0)
    empty_columns_count: Mapped[int] = mapped_column(Integer, default=0)
    data_quality_score: Mapped[float] = mapped_column(Float, default=100.0)  # Percentage score 0 - 100
    
    date_range_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    date_range_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Detailed per-column health breakdown
    column_metrics: Mapped[dict] = mapped_column(JSON, default=dict)

    # Relationships
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="quality_summary")
