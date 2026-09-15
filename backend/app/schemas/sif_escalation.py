from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict


class EscalationStageItem(BaseModel):
    stage_number: int
    stage_name: str
    description: str
    barrier_or_factor_involved: Optional[str] = None


class PreventiveIntelligencePayload(BaseModel):
    current_condition: str
    hazard_exposure: str
    control_failure: str
    immediate_containment: str
    preventive_control: str
    potential_escalation: str


class ReportSIFEscalationResponse(BaseModel):
    report_id: str
    original_id: Optional[str] = None
    refinery_unit: Optional[str] = None
    equipment: Optional[str] = None
    severity: str  # NORMAL, WATCH, ELEVATED, HIGH, CRITICAL
    severity_color: str  # green, cyan, amber, orange, red
    sif_precursor_status: bool
    sif_category: Optional[str] = None
    bdi_score: float
    bdi_classification: str

    # Direct Structured Explanations
    why_escalated: str
    which_barriers: List[str] = []
    which_factors: List[str] = []
    which_reports: List[str] = []
    what_exposure: str
    what_potential_consequence: str
    what_remains_unresolved: List[str] = []
    what_could_happen: str

    barrier_summary: Dict[str, int] = {}
    contributing_factors: List[str] = []
    escalation_scenario: List[EscalationStageItem] = []
    preventive_intelligence: Optional[PreventiveIntelligencePayload] = None

    recommended_immediate_action: str
    recommended_preventive_action: str
    confidence: float = 0.85
    engine_version: str = "v4.0.0"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EscalationItem(BaseModel):
    report_id: str
    original_id: Optional[str] = None
    refinery_unit: Optional[str] = None
    equipment: Optional[str] = None
    severity: str
    sif_category: Optional[str] = None
    bdi_score: float
    primary_precursor_hazard: str
    top_compromised_barriers: List[str] = []
    escalation_scenario_summary: str
    immediate_containment: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CriticalEscalationsResponse(BaseModel):
    total_critical_count: int
    items: List[EscalationItem] = []


class HighEscalationsResponse(BaseModel):
    total_high_count: int
    items: List[EscalationItem] = []


class SIFEscalationSummaryResponse(BaseModel):
    total_reports_evaluated: int
    normal_count: int
    watch_count: int
    elevated_count: int
    high_count: int
    critical_count: int
    sif_precursor_rate: float
    top_escalation_categories: List[Dict[str, Any]] = []
    top_vulnerable_units: List[Dict[str, Any]] = []
    engine_version: str = "v4.0.0"


class UnitSIFEscalationResponse(BaseModel):
    refinery_unit: str
    unit_escalation_level: str
    unit_escalation_color: str
    total_reports: int
    critical_reports_count: int
    high_reports_count: int
    average_bdi: float
    dominant_sif_hazards: List[Dict[str, Any]] = []
    dominant_compromised_barriers: List[Dict[str, Any]] = []
    unit_preventive_imperative: str
