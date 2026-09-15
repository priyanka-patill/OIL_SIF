from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict


class CorrelationEvidence(BaseModel):
    matched_fields: List[str] = []
    matched_values: Dict[str, Any] = {}
    factors_combined: List[str] = []
    days_apart: Optional[int] = None
    similarity_score: Optional[float] = None
    unresolved_actions: Optional[bool] = None
    notes: Optional[str] = None


class SafetyCorrelationItem(BaseModel):
    id: str
    source_report_id: str
    related_report_id: str
    dataset_id: str
    relationship_type: str
    correlation_score: float
    correlation_method: str
    evidence: Dict[str, Any]
    convergence_factors: List[str] = []
    is_cross_dataset: bool = False
    source_dataset_name: Optional[str] = None
    related_dataset_name: Optional[str] = None
    engine_version: str = "v1.0.0"
    created_at: datetime
    
    # Optional report summaries
    related_report_original_id: Optional[str] = None
    related_report_unit: Optional[str] = None
    related_report_equipment: Optional[str] = None
    related_report_risk_level: Optional[str] = None
    related_report_factors: List[str] = []

    model_config = ConfigDict(from_attributes=True)


class ReportCorrelationResponse(BaseModel):
    report_id: str
    original_id: Optional[str] = None
    has_correlations: bool
    total_correlations: int
    single_report_factors: List[str] = []
    converged_factors: List[str] = []
    compound_risk_score: float
    evidence_statement: str
    correlations: List[SafetyCorrelationItem] = []


class UnitCorrelationsResponse(BaseModel):
    refinery_unit: str
    total_correlated_reports: int
    high_potential_clusters_count: int
    top_convergent_equipment: List[Dict[str, Any]] = []
    correlations: List[SafetyCorrelationItem] = []


class HighRiskCorrelationsResponse(BaseModel):
    total_high_risk_correlations: int
    critical_convergence_count: int
    correlations: List[SafetyCorrelationItem] = []


class RecurringCorrelationsResponse(BaseModel):
    total_recurring_correlations: int
    equipment_clusters: List[Dict[str, Any]] = []
    correlations: List[SafetyCorrelationItem] = []


class ConvergenceCluster(BaseModel):
    cluster_key: str
    dimension_type: str  # EQUIPMENT, REFINERY_UNIT, WORK_TYPE
    dimension_value: str
    report_count: int
    converged_factor_count: int
    converged_factors: List[str]
    high_risk_count: int
    high_potential_count: int
    unresolved_action_count: int
    is_cross_dataset: bool
    participating_datasets: List[str]
    sample_report_ids: List[str]
    danger_level: str  # LOW, MODERATE, HIGH, CRITICAL
    evidence_summary: str


class MultiFactorConvergenceResponse(BaseModel):
    total_convergence_clusters: int
    cross_dataset_convergences_count: int
    two_factor_clusters_count: int
    three_factor_clusters_count: int
    four_plus_factor_clusters_count: int
    clusters: List[ConvergenceCluster] = []


class CorrelationSummaryResponse(BaseModel):
    total_correlations: int
    cross_dataset_correlations: int
    single_report_multi_factor_count: int
    cross_report_multi_factor_count: int
    top_convergent_equipment: List[Dict[str, Any]] = []
    top_convergent_units: List[Dict[str, Any]] = []
    factor_co_occurrence_matrix: Dict[str, Dict[str, int]] = {}
    two_factor_combinations: List[Dict[str, Any]] = []
    three_factor_combinations: List[Dict[str, Any]] = []
    four_factor_combinations: List[Dict[str, Any]] = []
    dataset_provenance: List[Dict[str, Any]] = []
    engine_version: str = "v1.0.0"
