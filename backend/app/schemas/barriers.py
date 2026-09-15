from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict


class BarrierExplainability(BaseModel):
    why: str
    what_data_supports_this: str
    which_reports_support_this: List[str] = []


class BarrierAssessmentItem(BaseModel):
    id: str
    barrier_id: str
    barrier_name: str
    barrier_category: str
    layer_index: int = 1
    status: str  # INTACT, DEGRADED, FAILED, UNKNOWN
    confidence: float = 1.0
    evidence: Dict[str, Any] = {}
    explainability: BarrierExplainability
    source_report_ids: List[str] = []
    source_fields: List[str] = []
    is_cross_report: bool = False
    engine_version: str = "v2.0.0"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SwissCheeseLayer(BaseModel):
    layer_index: int
    barrier_id: str
    barrier_name: str
    barrier_category: str
    status: str  # INTACT, DEGRADED, FAILED, UNKNOWN
    status_color: str  # green, amber, red, gray
    hole_present: bool
    hole_severity: str  # NONE, MODERATE, CRITICAL
    explainability: BarrierExplainability
    source_report_ids: List[str] = []


class SwissCheeseVisualization(BaseModel):
    exposure_target: str
    hazard_energy: Optional[str] = None
    total_layers: int
    intact_count: int
    degraded_count: int
    failed_count: int
    unknown_count: int
    holes_aligned_count: int
    convergence_level: str  # NONE, MINOR, ELEVATED, CRITICAL_CONVERGENCE
    layers: List[SwissCheeseLayer] = []
    escalation_pathway: List[str] = []
    preventive_barrier_imperative: str


class ReportBarrierResponse(BaseModel):
    report_id: str
    original_id: Optional[str] = None
    refinery_unit: Optional[str] = None
    equipment: Optional[str] = None
    barriers: List[BarrierAssessmentItem] = []
    swiss_cheese: SwissCheeseVisualization
    cross_report_convergence_present: bool = False
    related_reports_contributing: List[str] = []


class UnitBarrierResponse(BaseModel):
    refinery_unit: str
    total_assessments: int
    degraded_barriers_count: int
    failed_barriers_count: int
    barrier_health_scores: Dict[str, float] = {}
    critical_equipment_convergences: List[Dict[str, Any]] = []
    recent_assessments: List[BarrierAssessmentItem] = []


class CriticalBarrierConvergenceItem(BaseModel):
    cluster_key: str
    dimension_type: str  # EQUIPMENT or REFINERY_UNIT
    dimension_value: str
    refinery_unit: str
    holes_aligned_count: int
    failed_barriers: List[str] = []
    degraded_barriers: List[str] = []
    participating_reports_count: int
    participating_report_ids: List[str] = []
    danger_level: str  # LOW, MODERATE, HIGH, CRITICAL
    swiss_cheese_diagram: SwissCheeseVisualization


class CriticalBarriersResponse(BaseModel):
    total_critical_convergences: int
    convergences: List[CriticalBarrierConvergenceItem] = []


class BarrierSummaryResponse(BaseModel):
    total_reports_analyzed: int
    total_barrier_assessments: int
    intact_percentage: float
    degraded_percentage: float
    failed_percentage: float
    unknown_percentage: float
    barrier_breakdown: List[Dict[str, Any]] = []
    top_weakened_barriers: List[Dict[str, Any]] = []
    multi_barrier_convergence_count: int
    engine_version: str = "v2.0.0"


class BarrierConvergenceResponse(BaseModel):
    total_convergence_clusters: int
    critical_clusters_count: int
    clusters: List[CriticalBarrierConvergenceItem] = []
