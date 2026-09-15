from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict


class SLAPolicyResponse(BaseModel):
    id: str
    severity: str
    sla_minutes: int
    reminder_minutes: int
    warning_minutes: int
    escalation_interval_minutes: int
    escalation_level_0_role: str
    escalation_level_1_role: str
    escalation_level_2_role: str
    escalation_level_3_role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SLAPolicyUpdateRequest(BaseModel):
    sla_minutes: Optional[int] = None
    reminder_minutes: Optional[int] = None
    warning_minutes: Optional[int] = None
    escalation_interval_minutes: Optional[int] = None
    escalation_level_0_role: Optional[str] = None
    escalation_level_1_role: Optional[str] = None
    escalation_level_2_role: Optional[str] = None
    escalation_level_3_role: Optional[str] = None
    is_active: Optional[bool] = None


class SLACountdownResponse(BaseModel):
    action_id: str
    report_id: str
    severity: str
    action_type: str
    assigned_role: str
    assigned_user: Optional[str] = "Unassigned"
    sla_minutes: int
    sla_deadline: Optional[datetime] = None
    time_remaining_seconds: int
    formatted_countdown: str  # e.g., "00:37:21 remaining" or "BREACHED by 00:05:12"
    percentage_elapsed: float
    sla_state: str  # NORMAL, APPROACHING_DEADLINE, BREACHED, ESCALATED, ACKNOWLEDGED, CONTAINED, VERIFIED, CLOSED
    current_escalation_level: int
    is_acknowledged: bool
    is_breached: bool


class SLAActionItemResponse(BaseModel):
    action_id: str
    report_id: str
    severity: str
    title: str
    status: str
    sla_state: str
    assigned_role: str
    assigned_user: Optional[str] = None
    sla_deadline: Optional[datetime] = None
    time_remaining_seconds: int
    formatted_countdown: str
    escalation_level: int
    created_at: datetime
    acknowledged_at: Optional[datetime] = None


class SLADashboardResponse(BaseModel):
    critical_open: int
    awaiting_acknowledgement: int
    approaching_sla: int
    sla_breached: int
    escalated: int
    contained: int
    awaiting_verification: int
    closed: int
    total_active_actions: int
    active_actions: List[SLAActionItemResponse]


class SLAAcknowledgeRequest(BaseModel):
    actor_name: str
    actor_role: str = "Unit In-Charge"
    comments: Optional[str] = None
