from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


class SafetyReportBase(BaseModel):
    original_id: Optional[str] = None
    report_date: Optional[datetime] = None
    location: Optional[str] = None
    refinery_unit: Optional[str] = None
    equipment: Optional[str] = None
    work_type: Optional[str] = None
    department: Optional[str] = None
    report_type: Optional[str] = None
    description: Optional[str] = None
    hazard: Optional[str] = None
    unsafe_act: Optional[str] = None
    unsafe_condition: Optional[str] = None
    ppe_issue: Optional[bool] = None
    immediate_cause: Optional[str] = None
    potential_consequence: Optional[str] = None
    risk_level: Optional[str] = None
    sif_precursor: Optional[bool] = None
    high_potential: Optional[bool] = None
    previous_similar_reports: Optional[int] = None
    repeated_issue: Optional[bool] = None
    supervisor_factor: Optional[bool] = None
    maintenance_factor: Optional[bool] = None
    corrective_action: Optional[str] = None
    action_status: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_department: Optional[str] = None
    due_date: Optional[datetime] = None
    source_dataset: Optional[str] = None
    analysis_status: Optional[str] = "COMPLETED"
    submitting_user: Optional[str] = None
    submitting_role: Optional[str] = None


class SafetyReportCreate(BaseModel):
    description: str
    report_type: Optional[str] = "Unsafe Act"
    report_date: Optional[datetime] = None
    location: Optional[str] = None
    refinery_unit: Optional[str] = None
    equipment: Optional[str] = None
    work_type: Optional[str] = None
    department: Optional[str] = None
    hazard: Optional[str] = None
    unsafe_act: Optional[str] = None
    unsafe_condition: Optional[str] = None
    ppe_issue: Optional[bool] = False
    supervisor_factor: Optional[bool] = False
    maintenance_factor: Optional[bool] = False
    repeated_issue: Optional[bool] = False
    immediate_cause: Optional[str] = None
    potential_consequence: Optional[str] = None
    risk_level: Optional[str] = None
    corrective_action: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_department: Optional[str] = None
    due_date: Optional[datetime] = None
    dataset_id: Optional[str] = None
    submitting_user: Optional[str] = "Supervisor"
    submitting_role: Optional[str] = "Supervisor"


class SafetyReportUpdate(BaseModel):
    report_type: Optional[str] = None
    report_date: Optional[datetime] = None
    location: Optional[str] = None
    refinery_unit: Optional[str] = None
    equipment: Optional[str] = None
    work_type: Optional[str] = None
    department: Optional[str] = None
    description: Optional[str] = None
    hazard: Optional[str] = None
    unsafe_act: Optional[str] = None
    unsafe_condition: Optional[str] = None
    ppe_issue: Optional[bool] = None
    supervisor_factor: Optional[bool] = None
    maintenance_factor: Optional[bool] = None
    repeated_issue: Optional[bool] = None
    immediate_cause: Optional[str] = None
    potential_consequence: Optional[str] = None
    risk_level: Optional[str] = None
    corrective_action: Optional[str] = None
    action_status: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_department: Optional[str] = None
    due_date: Optional[datetime] = None
    analysis_status: Optional[str] = None


class SafetyReportResponse(SafetyReportBase):
    id: str
    dataset_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SafetyReportDetailResponse(SafetyReportResponse):
    raw_data: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class ReportCountResponse(BaseModel):
    total_reports: int
    by_risk_level: Dict[str, int] = {}
    by_department: Dict[str, int] = {}
    by_refinery_unit: Dict[str, int] = {}
    by_action_status: Dict[str, int] = {}
    by_work_type: Dict[str, int] = {}
