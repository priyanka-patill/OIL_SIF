from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class FilterFieldOption(BaseModel):
    field_name: str
    display_name: str
    data_type: str
    distinct_values: List[Any]
    is_constant: bool = False


class CanonicalFieldDefinition(BaseModel):
    name: str
    description: str
    data_type: str
    is_required: bool = False
    example: Optional[str] = None


class MetadataFieldsResponse(BaseModel):
    available_filters: List[FilterFieldOption]
    canonical_schema: List[CanonicalFieldDefinition]
    total_active_datasets: int
