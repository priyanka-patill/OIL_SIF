from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ExportFilterParams(BaseModel):
    dataset_id: Optional[str] = None
    risk_level: Optional[str] = None
    department: Optional[str] = None
    refinery_unit: Optional[str] = None
    report_type: Optional[str] = None
    action_status: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class ExportPreviewResponse(BaseModel):
    total_matching_reports: int
    by_risk_level: Dict[str, int]
    by_department: Dict[str, int]
    by_refinery_unit: Dict[str, int]
    by_action_status: Dict[str, int]
    sif_precursor_count: int
    overdue_count: int
    available_export_formats: List[str] = ["PDF", "EXCEL", "CSV"]
    active_filters_applied: Dict[str, Any]
