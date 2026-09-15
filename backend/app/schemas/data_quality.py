from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


class ColumnQualityMetric(BaseModel):
    name: str
    detected_type: str
    semantic_type: str
    null_count: int
    null_percentage: float
    unique_count: int
    is_constant: bool
    constant_value: Optional[str] = None
    sample_values: List[Any] = []
    issues: List[str] = []


class DataQualityResponse(BaseModel):
    id: str
    dataset_id: str
    dataset_name: Optional[str] = None
    calculated_at: datetime
    total_rows: int
    total_columns: int
    valid_records_count: int
    missing_values_count: int
    duplicate_ids_count: int
    invalid_dates_count: int
    constant_fields_count: int
    empty_columns_count: int
    data_quality_score: float
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    column_metrics: Dict[str, Any] = {}
    constant_fields: List[str] = []
    summary_notes: List[str] = []

    model_config = ConfigDict(from_attributes=True)
