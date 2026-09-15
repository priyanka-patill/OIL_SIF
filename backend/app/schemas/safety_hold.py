from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class SafetyHoldCreateRequest(BaseModel):
    report_id: Optional[str] = None
    action_id: Optional[str] = None
    permit_id: Optional[str] = None
    jsa_id: Optional[str] = None
    refinery_unit: Optional[str] = None
    equipment: Optional[str] = None
    trigger: str = "CRITICAL SIF Precursor"
    reason: str
    bdi: Optional[float] = None
    sif_status: Optional[str] = "YES"
    requested_by: str = "Unit In-Charge"


class SafetyHoldReviewRequest(BaseModel):
    decision: str  # "APPROVE", "REJECT", "REQUEST_INFO"
    reviewer_name: str
    reviewer_role: str = "Safety Officer"
    comments: Optional[str] = None


class SafetyHoldReassessRequest(BaseModel):
    actor_name: str
    actor_role: str = "HSE Inspector"
    reassessment_notes: str


class SafetyHoldReleaseRequest(BaseModel):
    requester_name: str
    requester_role: str = "Unit In-Charge"
    justification: str


class SafetyHoldVerifyReleaseRequest(BaseModel):
    verifier_name: str
    verifier_role: str = "Safety Officer"
    walkdown_notes: str
    permit_reauthorized: bool = True


class SafetyHoldResponse(BaseModel):
    id: str
    report_id: Optional[str] = None
    action_id: Optional[str] = None
    permit_id: Optional[str] = None
    jsa_id: Optional[str] = None
    refinery_unit: Optional[str] = None
    equipment: Optional[str] = None
    trigger: str
    reason: str
    bdi: Optional[float] = None
    sif_status: Optional[str] = None
    status: str
    requested_by: str
    reviewed_by: Optional[str] = None
    approved_by: Optional[str] = None
    released_by: Optional[str] = None
    verified_by: Optional[str] = None
    verification_notes: Optional[str] = None
    created_at: datetime
    approved_at: Optional[datetime] = None
    released_at: Optional[datetime] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SafetyHoldListResponse(BaseModel):
    total: int
    items: List[SafetyHoldResponse]
    page: int = 1
    page_size: int = 20
