from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class SystemAuditLogBase(BaseModel):
    report_id: Optional[str] = None
    dataset_id: Optional[str] = None
    action_id: Optional[str] = None
    hold_id: Optional[str] = None
    event_type: str
    engine_version: str = "2.0.0-phase8"
    trigger: str
    evidence: Optional[Dict[str, Any]] = None
    bdi: Optional[float] = None
    sif_status: Optional[str] = None
    severity: Optional[str] = None
    recommended_action: Optional[str] = None
    human_decision: Optional[str] = None
    notification_status: Optional[str] = None
    escalation_level: Optional[int] = None
    final_resolution: Optional[str] = None
    actor: str = "AI Safety Engine"
    is_simulated: bool = False
    client_host: Optional[str] = None


class SystemAuditLogCreate(SystemAuditLogBase):
    pass


class SystemAuditLogResponse(SystemAuditLogBase):
    event_id: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditTimelineEvent(BaseModel):
    event_id: str
    timestamp: datetime
    formatted_time: str
    event_type: str
    title: str
    description: str
    actor: str
    severity: Optional[str] = None
    bdi: Optional[float] = None
    sif_status: Optional[str] = None
    is_simulated: bool = False
    evidence: Optional[Dict[str, Any]] = None


class AuditTimelineResponse(BaseModel):
    report_id: Optional[str] = None
    total_events: int
    events: List[AuditTimelineEvent]
    first_event_at: Optional[datetime] = None
    last_event_at: Optional[datetime] = None


class AuditStatsResponse(BaseModel):
    total_events: int
    real_events: int
    simulated_events: int
    event_types_breakdown: Dict[str, int]
    actors_breakdown: Dict[str, int]
    last_event_timestamp: Optional[datetime] = None
