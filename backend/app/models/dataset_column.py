import uuid
from sqlalchemy import String, Integer, Boolean, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class DatasetColumn(Base):
    __tablename__ = "dataset_columns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    column_index: Mapped[int] = mapped_column(Integer, default=0)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sanitized_name: Mapped[str] = mapped_column(String(255), nullable=False)
    detected_data_type: Mapped[str] = mapped_column(String(50), nullable=False)  # STRING, INTEGER, FLOAT, BOOLEAN, DATETIME, TEXT
    semantic_type: Mapped[str] = mapped_column(String(50), default="UNKNOWN")  # ID, DATE, LOCATION, EQUIPMENT, WORK_TYPE, etc.
    is_nullable: Mapped[bool] = mapped_column(Boolean, default=False)
    null_count: Mapped[int] = mapped_column(Integer, default=0)
    unique_count: Mapped[int] = mapped_column(Integer, default=0)
    is_constant: Mapped[bool] = mapped_column(Boolean, default=False)
    constant_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    sample_values: Mapped[list | dict | None] = mapped_column(JSON, nullable=True)
    mapped_canonical_field: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="columns")
