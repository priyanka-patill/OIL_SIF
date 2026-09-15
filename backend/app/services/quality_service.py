from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.data_quality import DataQualitySummary
from app.models.dataset import Dataset
from app.models.dataset_column import DatasetColumn


class QualityService:
    @staticmethod
    def get_quality_by_dataset_id(db: Session, dataset_id: str) -> Optional[Dict[str, Any]]:
        dataset = db.scalar(select(Dataset).where(Dataset.id == dataset_id))
        if not dataset:
            return None

        quality = db.scalar(select(DataQualitySummary).where(DataQualitySummary.dataset_id == dataset_id))
        if not quality:
            return None

        columns = list(db.scalars(
            select(DatasetColumn).where(DatasetColumn.dataset_id == dataset_id)
        ).all())

        constant_fields = [col.original_name for col in columns if col.is_constant]

        # Generate contextual quality notes
        notes: List[str] = []
        if quality.missing_values_count == 0:
            notes.append("Zero missing values detected across all columns (100% complete dataset).")
        else:
            notes.append(f"{quality.missing_values_count} total missing cell values detected.")

        if quality.duplicate_ids_count == 0:
            notes.append("All record identifiers are unique.")
        else:
            notes.append(f"{quality.duplicate_ids_count} duplicate record identifiers found.")

        if constant_fields:
            notes.append(f"{len(constant_fields)} constant columns detected ({', '.join(constant_fields)}). These contain only 1 unique value across all records.")

        if quality.invalid_dates_count == 0:
            notes.append("All timestamp/date entries successfully parsed.")
        else:
            notes.append(f"{quality.invalid_dates_count} invalid date records detected.")

        return {
            "id": quality.id,
            "dataset_id": dataset.id,
            "dataset_name": dataset.dataset_name,
            "calculated_at": quality.calculated_at,
            "total_rows": quality.total_rows,
            "total_columns": quality.total_columns,
            "valid_records_count": quality.valid_records_count,
            "missing_values_count": quality.missing_values_count,
            "duplicate_ids_count": quality.duplicate_ids_count,
            "invalid_dates_count": quality.invalid_dates_count,
            "constant_fields_count": quality.constant_fields_count,
            "empty_columns_count": quality.empty_columns_count,
            "data_quality_score": quality.data_quality_score,
            "date_range_start": quality.date_range_start,
            "date_range_end": quality.date_range_end,
            "column_metrics": quality.column_metrics or {},
            "constant_fields": constant_fields,
            "summary_notes": notes
        }
