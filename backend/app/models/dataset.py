import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_name: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    sheet_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    dataset_type: Mapped[str] = mapped_column(String(50), default="single_factor")  # single_factor, multi_factor, high_potential, summary, general
    factor_count: Mapped[int] = mapped_column(Integer, default=0)
    factor_names: Mapped[list] = mapped_column(JSON, default=list)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    upload_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    column_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="ready")  # uploaded, processing, ready, failed
    data_quality_status: Mapped[str] = mapped_column(String(50), default="PASSED")
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0)
    is_derived_dataset: Mapped[bool] = mapped_column(Boolean, default=False)
    is_summary_dataset: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_dataset: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    columns: Mapped[list["DatasetColumn"]] = relationship(
        "DatasetColumn", back_populates="dataset", cascade="all, delete-orphan", lazy="selectin"
    )
    reports: Mapped[list["SafetyReport"]] = relationship(
        "SafetyReport", back_populates="dataset", cascade="all, delete-orphan", lazy="select"
    )
    quality_summary: Mapped["DataQualitySummary | None"] = relationship(
        "DataQualitySummary", back_populates="dataset", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )
