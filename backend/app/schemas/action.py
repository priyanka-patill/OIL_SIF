from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class ActionUpdateRequest(BaseModel):
    action_status: Optional[str] = Field(None, description="OPEN, ACKNOWLEDGED, IN_PROGRESS, COMPLETED, VERIFIED, REJECTED, OVERDUE")
    assigned_to: Optional[str] = Field(None, description="Responsible person or role (Supervisor, HSE Officer, Unit In-Charge, HSE Head, Management)")
    assigned_department: Optional[str] = Field(None, description="Responsible department")
    due_date: Optional[datetime] = Field(None, description="Target completion due date")
    completion_date: Optional[datetime] = Field(None, description="Actual completion date")
    closure_verified_by: Optional[str] = Field(None, description="Safety Officer or Supervisor verifying closure")
    closure_verified_at: Optional[datetime] = Field(None, description="Verification timestamp")
    action_comments: Optional[str] = Field(None, description="Notes, field updates, or justification")
    evidence_text: Optional[str] = Field(None, description="Textual description of evidence provided")
    evidence_photo_url: Optional[str] = Field(None, description="Photo attachment URL or path")
    evidence_document_url: Optional[str] = Field(None, description="Document attachment URL or path")
    actor_name: str = Field("Safety Officer", description="Name of the person making the change")
    actor_role: str = Field("Safety Officer", description="Role of the person making the change (Supervisor, HSE Officer, Unit In-Charge, HSE Head, Management)")


class ActionHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    report_id: str
    actor_name: str
    actor_role: str
    action_type: str
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    comments: Optional[str] = None
    timestamp: datetime


class ActionItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    report_id: str
    original_id: Optional[str] = None
    problem: Optional[str] = None
    risk_level: Optional[str] = None
    corrective_action: Optional[str] = None
    refinery_unit: Optional[str] = None
    department: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_department: Optional[str] = None
    action_status: str
    due_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    closure_verified_by: Optional[str] = None
    closure_verified_at: Optional[datetime] = None
    action_comments: Optional[str] = None
    evidence_text: Optional[str] = None
    evidence_photo_url: Optional[str] = None
    evidence_document_url: Optional[str] = None
    is_overdue: bool = False
    days_overdue: Optional[int] = None
    history_count: int = 0


class ActionStatsResponse(BaseModel):
    total_actions: int
    open_count: int
    in_progress_count: int
    closed_count: int
    overdue_count: int
    unassigned_count: int
