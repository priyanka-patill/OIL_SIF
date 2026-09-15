from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func, distinct

from app.database.session import get_db
from app.schemas.metadata import MetadataFieldsResponse, FilterFieldOption, CanonicalFieldDefinition
from app.models.safety_report import SafetyReport
from app.models.dataset import Dataset
from app.models.dataset_column import DatasetColumn
from app.utils.constants import CANONICAL_FIELDS

router = APIRouter(prefix="/metadata", tags=["Metadata & Dynamic Fields"])


@router.get("/fields", response_model=MetadataFieldsResponse)
def get_metadata_fields(db: Session = Depends(get_db)):
    """
    Dynamically discover available filter fields, distinct categorical options 
    present in the loaded data, and full canonical field specifications.
    """
    total_active_datasets = db.scalar(select(func.count(Dataset.id)).where(Dataset.is_active == True)) or 0

    # Collect distinct values from active database reports
    def get_distinct(column):
        rows = db.execute(select(distinct(column)).where(column != None).order_by(column)).scalars().all()
        return [r for r in rows if r is not None and str(r).strip() != ""]

    filter_candidates = [
        ("refinery_unit", "Refinery Unit", "STRING", SafetyReport.refinery_unit),
        ("department", "Department", "STRING", SafetyReport.department),
        ("work_type", "Work Type", "STRING", SafetyReport.work_type),
        ("risk_level", "Risk Level", "STRING", SafetyReport.risk_level),
        ("immediate_cause", "Immediate Cause", "STRING", SafetyReport.immediate_cause),
        ("potential_consequence", "Potential Consequence", "STRING", SafetyReport.potential_consequence),
        ("action_status", "Action Status", "STRING", SafetyReport.action_status),
        ("equipment", "Equipment ID", "STRING", SafetyReport.equipment),
    ]

    available_filters: List[FilterFieldOption] = []
    for field_name, display_name, data_type, col_attr in filter_candidates:
        distinct_vals = get_distinct(col_attr)
        # Constant field detection on the filter level
        is_const = len(distinct_vals) == 1
        if distinct_vals:
            available_filters.append(FilterFieldOption(
                field_name=field_name,
                display_name=display_name,
                data_type=data_type,
                distinct_values=distinct_vals,
                is_constant=is_const
            ))

    # Canonical schema metadata
    canonical_schema = [
        CanonicalFieldDefinition(
            name=fname,
            description=fmeta["description"],
            data_type=fmeta["type"],
            is_required=False
        )
        for fname, fmeta in CANONICAL_FIELDS.items()
    ]

    return MetadataFieldsResponse(
        available_filters=available_filters,
        canonical_schema=canonical_schema,
        total_active_datasets=total_active_datasets
    )
