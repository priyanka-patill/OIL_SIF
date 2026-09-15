from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict


class ActionPackageSchema(BaseModel):
    report_id: str
    dataset_id: Optional[str] = None
    refinery_unit: Optional[str] = None
    equipment: Optional[str] = None
    work_type: Optional[str] = None
    observed_condition: str
    safety_factors: List[str] = []
    barrier_status: Dict[str, Any] = {}
    bdi_score: float
    bdi_classification: str
    recorded_risk: str
    ai_risk: str
    severity: Optional[str] = None
    sif_status: str
    potential_consequence: str
    immediate_containment_recommendation: str
    corrective_action: str
    preventive_action: str
    verification_requirement: str
    responsible_role: str
    sla_hours: int
    sla_deadline: Optional[datetime] = None


class SafetyActionResponse(BaseModel):
    id: str
    report_id: str
    dataset_id: Optional[str] = None
    action_type: str
    severity: str
    title: str
    description: str
    ai_recommendation: Dict[str, Any] = {}
    action_package: Dict[str, Any] = {}
    assigned_role: str
    assigned_user: Optional[str] = "Unassigned"
    sla_hours: int
    sla_deadline: Optional[datetime] = None
    escalation_level: int = 0
    status: str
    approval_status: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SafetyActionApprovalRequest(BaseModel):
    decision: str  # APPROVE, EDIT_AND_APPROVE, REJECT, CANCEL
    assigned_role: Optional[str] = None
    assigned_user: Optional[str] = None
    sla_hours: Optional[int] = None
    description: Optional[str] = None
    rejection_reason: Optional[str] = None
    reviewer_name: str = "Safety Duty Officer"


class SafetyActionTransitionRequest(BaseModel):
    new_status: str  # ACKNOWLEDGED, IN_PROGRESS, CONTAINED, AWAITING_VERIFICATION, VERIFIED, CLOSED, ESCALATED
    comments: Optional[str] = None
    actor_name: str = "Field Engineer"
    actor_role: str = "Unit In-Charge"


class EmailDraftResponse(BaseModel):
    subject: str
    body_text: str
    body_html: str
    source_data_summary: Dict[str, Any]
    ai_recommendations_summary: Dict[str, Any]
    sla_deadline: Optional[datetime] = None
    assigned_role: str


class WebhookDispatchRequest(BaseModel):
    endpoint: str
    event_type: Optional[str] = "ACTION_DISPATCHED"


class WebhookLogResponse(BaseModel):
    id: str
    action_id: str
    endpoint: str
    event_type: str
    payload_hash: str
    delivery_status: str
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    retry_count: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class OrchestratorSummaryResponse(BaseModel):
    total_actions: int
    pending_approval_count: int
    dispatched_count: int
    in_progress_count: int
    contained_count: int
    awaiting_verification_count: int
    closed_count: int
    escalated_count: int
    rejected_count: int
    critical_actions_count: int
    high_actions_count: int
    sla_breach_count: int


class AutoOrchestrateResponse(BaseModel):
    scanned_reports_count: int
    actions_created_count: int
    actions_skipped_duplicate_count: int
    action_ids: List[str] = []
