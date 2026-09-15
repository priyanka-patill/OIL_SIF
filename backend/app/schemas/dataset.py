from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict


class DatasetColumnResponse(BaseModel):
    id: str
    dataset_id: str
    column_index: int
    original_name: str
    sanitized_name: str
    detected_data_type: str
    semantic_type: str
    is_nullable: bool
    null_count: int
    unique_count: int
    is_constant: bool
    constant_value: Optional[str] = None
    sample_values: Optional[Any] = None
    mapped_canonical_field: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DatasetBase(BaseModel):
    dataset_name: str
    original_filename: str
    sheet_name: Optional[str] = None
    file_type: str
    dataset_type: str = "single_factor"
    factor_count: int = 0
    factor_names: List[str] = []
    file_size_bytes: int = 0
    row_count: int = 0
    column_count: int = 0
    data_quality_status: str = "PASSED"
    duplicate_count: int = 0
    is_derived_dataset: bool = False
    is_summary_dataset: bool = False
    parent_dataset: Optional[str] = None
    description: Optional[str] = None


class DatasetResponse(DatasetBase):
    id: str
    upload_timestamp: datetime
    status: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DatasetDetailResponse(DatasetResponse):
    columns: List[DatasetColumnResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


class DatasetSchemaResponse(BaseModel):
    dataset_id: str
    dataset_name: str
    row_count: int
    column_count: int
    columns: List[DatasetColumnResponse]
    constant_fields: List[DatasetColumnResponse]
    mapped_fields_count: int
    unmapped_fields_count: int

    model_config = ConfigDict(from_attributes=True)
