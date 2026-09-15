from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict


class FactorMetric(BaseModel):
    factor_name: str
    display_name: str
    total_count: int
    percentage: float
    high_risk_count: int
    critical_count: int
    high_potential_count: int
    recurring_count: int
    top_consequence: Optional[str] = None
    top_refinery_unit: Optional[str] = None


class FactorSummaryResponse(BaseModel):
    total_reports_analyzed: int
    active_dataset_count: int
    single_factor_reports_count: int
    multi_factor_reports_count: int
    high_potential_reports_count: int
    factors: List[FactorMetric]


class FactorCombinationItem(BaseModel):
    combination_key: str
    factor_names: List[str]
    factor_count: int
    report_count: int
    high_risk_count: int
    critical_count: int
    high_potential_count: int
    high_risk_ratio: float
    danger_score: float
    danger_level: str  # LOW, MODERATE, HIGH, CRITICAL
    top_consequences: List[str]
    top_causes: List[str]
    sample_report_ids: List[str]


class FactorCombinationsResponse(BaseModel):
    total_reports_analyzed: int
    level_1_count: int  # 1 factor
    level_2_count: int  # 2 factors
    level_3_count: int  # 3 factors
    level_4_count: int  # 4 factors
    combinations: List[FactorCombinationItem]
    danger_ranked_combinations: List[FactorCombinationItem]


class MetricComparison(BaseModel):
    metric_name: str
    dataset_a_value: Any
    dataset_b_value: Any
    variance: Optional[float] = None
    notes: Optional[str] = None


class DatasetComparisonResponse(BaseModel):
    dataset_a: Dict[str, Any]
    dataset_b: Dict[str, Any]
    total_reports_a: int
    total_reports_b: int
    risk_distribution_comparison: List[Dict[str, Any]]
    factor_presence_comparison: List[Dict[str, Any]]
    top_consequences_a: List[Dict[str, Any]]
    top_consequences_b: List[Dict[str, Any]]
    top_causes_a: List[Dict[str, Any]]
    top_causes_b: List[Dict[str, Any]]
    high_potential_count_a: int
    high_potential_count_b: int
    open_actions_count_a: int
    open_actions_count_b: int
    comparative_insights: List[str]


class HighPotentialPatternItem(BaseModel):
    pattern_name: str
    incident_count: int
    factor_combination: List[str]
    immediate_causes: List[str]
    potential_consequences: List[str]
    affected_units: List[str]
    severity_rating: str


class HighPotentialIntelligenceResponse(BaseModel):
    total_high_potential_incidents: int
    critical_risk_count: int
    high_risk_count: int
    multi_barrier_failure_count: int
    repeated_issue_co_occurrence_count: int
    top_potential_consequences: List[Dict[str, Any]]
    top_immediate_causes: List[Dict[str, Any]]
    top_refinery_units: List[Dict[str, Any]]
    key_failure_patterns: List[HighPotentialPatternItem]
    preventive_imperatives: List[str]
