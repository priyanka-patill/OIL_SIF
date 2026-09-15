from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, ConfigDict


class BDIComponentContribution(BaseModel):
    component_name: str
    category: str
    points_added: float
    max_possible_points: float
    description: str
    evidence_detail: Dict[str, Any] = {}


class BDIExplainability(BaseModel):
    why_summary: str
    classification_rationale: str
    top_contributors: List[str] = []
    component_breakdown: List[BDIComponentContribution] = []
    remediation_guidance: str


class IndependentMetrics(BaseModel):
    recorded_risk_level: Optional[str] = None
    ai_risk_level: Optional[str] = None
    bdi_score: float
    bdi_classification: str
    sif_precursor_status: Optional[bool] = None
    high_potential_status: Optional[bool] = None


class ReportBDIResponse(BaseModel):
    report_id: str
    original_id: Optional[str] = None
    refinery_unit: Optional[str] = None
    equipment: Optional[str] = None
    bdi_score: float
    classification: str  # MINIMAL, LOW, MODERATE, HIGH, SEVERE
    classification_color: str  # green, cyan, amber, orange, red
    independent_metrics: IndependentMetrics
    component_contributions: List[BDIComponentContribution] = []
    barrier_states_summary: Dict[str, int] = {}
    explainability: BDIExplainability
    source_reports_count: int = 1
    source_report_ids: List[str] = []
    calculation_version: str = "v3.0.0"
    calculated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UnitBDIResponse(BaseModel):
    refinery_unit: str
    unit_bdi_score: float
    classification: str
    classification_color: str
    data_adequacy_status: str  # SUFFICIENT, INSUFFICIENT
    total_contributing_reports: int
    dominant_degraded_barriers: List[Dict[str, Any]] = []
    dominant_factors: List[Dict[str, Any]] = []
    high_bdi_equipment_count: int
    calculation_methodology_note: str
    trend_direction: Optional[str] = None  # INCREASING, STABLE, DECREASING


class HighBDIItem(BaseModel):
    report_id: str
    original_id: Optional[str] = None
    refinery_unit: Optional[str] = None
    equipment: Optional[str] = None
    bdi_score: float
    classification: str
    top_contributors: List[str] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HighBDIResponse(BaseModel):
    total_high_bdi_count: int
    severe_count: int
    high_count: int
    items: List[HighBDIItem] = []


class BDISummaryResponse(BaseModel):
    total_reports_analyzed: int
    average_bdi: float
    minimal_count: int
    low_count: int
    moderate_count: int
    high_count: int
    severe_count: int
    top_degraded_units: List[Dict[str, Any]] = []
    top_degraded_equipment: List[Dict[str, Any]] = []
    active_weights: Dict[str, float] = {}
    active_thresholds: Dict[str, Any] = {}
    calculation_version: str = "v3.0.0"


class BDITrendPoint(BaseModel):
    period: str
    refinery_unit: Optional[str] = None
    average_bdi: float
    max_bdi: float
    report_count: int
    severe_count: int


class BDITrendsResponse(BaseModel):
    monthly_trends: List[BDITrendPoint] = []
    unit_trends: Dict[str, List[BDITrendPoint]] = {}


class BDIConfigResponse(BaseModel):
    weights: Dict[str, float]
    thresholds: Dict[str, List[float]]
    version: str
    documentation: Dict[str, str]
