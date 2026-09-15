from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DemoStatusResponse(BaseModel):
    demo_mode_active: bool
    status_label: str = "SIMULATION MODE ACTIVE"
    current_simulated_time: str
    simulated_time_offset_minutes: int
    active_scenario: Optional[str] = None
    loaded_report_id: Optional[str] = None
    loaded_action_id: Optional[str] = None
    loaded_hold_id: Optional[str] = None
    external_notifications_suppressed: bool = True


class DemoToggleRequest(BaseModel):
    enabled: bool


class DemoLoadScenarioRequest(BaseModel):
    scenario_type: str = Field(description="NORMAL, MINOR_PRECURSOR, MULTI_FACTOR_CONVERGENCE, HIGH_SIF_PRECURSOR, CRITICAL_SIF_PRECURSOR")
    refinery_unit: Optional[str] = None


class DemoTimeTravelRequest(BaseModel):
    advance_minutes: int = Field(ge=1, le=1440, description="Minutes to fast forward virtual simulation time")
    action_id: Optional[str] = None


class DemoSimulateStepRequest(BaseModel):
    step: str = Field(description="ACKNOWLEDGE, CONTAIN, VERIFY, CLOSE, ESCALATE, TRIGGER_BREACH")
    action_id: Optional[str] = None
    actor_name: str = "Safety Officer"
    actor_role: str = "Safety Officer"
    notes: Optional[str] = None


class DemoPipelineStepItem(BaseModel):
    step_number: int
    step_key: str
    step_title: str
    status: str  # COMPLETED, ACTIVE, PENDING, SKIPPED
    summary: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str


class DemoScenarioExecutionResponse(BaseModel):
    scenario_type: str
    status: str
    summary: str
    report_id: str
    action_id: Optional[str] = None
    hold_id: Optional[str] = None
    bdi_score: float
    sif_status: str
    severity: str
    pipeline_steps: List[DemoPipelineStepItem]
    email_preview: Optional[Dict[str, Any]] = None
    sla_info: Optional[Dict[str, Any]] = None
