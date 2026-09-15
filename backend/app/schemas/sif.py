from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class EscalationScenarioSchema(BaseModel):
    current_condition: str
    continued_exposure: str
    loss_of_control: str
    incident_event: str
    serious_consequence: str
    potential_fatal_consequence: str


class ReportAnalysisResponse(BaseModel):
    id: str
    report_id: str
    dataset_id: str
    analysis_timestamp: datetime
    model_version: str

    # Extracted Context
    observed_problem: str
    extracted_ppe_items: List[str]
    extracted_ppe_issue_type: str
    hazard_identified: str
    exposure_target: str
    immediate_cause: Optional[str] = None
    potential_consequence: Optional[str] = None

    # Risk Assessment (Recorded vs AI Predicted)
    recorded_risk_level: str
    ai_risk_level: str
    sif_precursor: str
    sif_category: str
    confidence_score: float

    # Explainable AI
    reasoning: List[str]

    # IOGP Life-Saving Rules
    iogp_rule: Optional[str] = None
    secondary_iogp_rules: Optional[List[str]] = Field(default_factory=list)
    iogp_confidence: Optional[float] = None
    iogp_reasoning: Optional[str] = None

    # Barrier / Control Analysis
    barrier_failure: Optional[str] = None
    missing_control: Optional[str] = None
    existing_barrier: Optional[str] = None

    # Recurrence
    is_recurring: bool
    recurrence_score: float
    recurrence_details: Dict[str, Any]

    # Action Recommendations
    immediate_action_recommendation: str
    preventive_action_recommendation: str

    # Escalation Scenario
    escalation_scenario: EscalationScenarioSchema

    # Organizational Factors
    organizational_factors: List[str]

    # Human Review & Overrides
    human_overridden: Optional[bool] = False
    human_risk_level: Optional[str] = None
    human_sif_precursor: Optional[str] = None
    human_feedback_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)



class AIFeedbackCreate(BaseModel):
    report_id: str
    reviewer_name: str = "Safety Officer"
    agrees_with_ai: bool
    human_risk_level: Optional[str] = None  # Low, Medium, High, Critical
    human_sif_precursor: Optional[str] = None  # YES, NO, UNCERTAIN
    feedback_reason: str = Field(..., min_length=3, description="Justification for human safety assessment")


class AIFeedbackResponse(BaseModel):
    id: str
    report_id: str
    analysis_id: str
    reviewer_name: str
    agrees_with_ai: bool
    human_risk_level: Optional[str] = None
    human_sif_precursor: Optional[str] = None
    feedback_reason: str
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SIFSummaryResponse(BaseModel):
    total_analyzed: int
    sif_precursors_detected: int
    sif_precursor_rate_percentage: float
    by_sif_precursor: Dict[str, int]  # YES, NO, UNCERTAIN
    by_ai_risk_level: Dict[str, int]  # CRITICAL, HIGH, MEDIUM, LOW
    by_recorded_risk_level: Dict[str, int]
    risk_level_upgrades: int  # Cases where AI flagged higher risk than recorded
    by_sif_category: Dict[str, int]
    by_ppe_issue_type: Dict[str, int]
    top_recurring_units: List[Dict[str, Any]]
    top_recurring_equipment: List[Dict[str, Any]]


class RecurringIssueItem(BaseModel):
    category: str
    identifier: str
    count: int
    sif_precursor_count: int
    high_risk_count: int
    sample_descriptions: List[str]
    sample_report_ids: List[str]


class RecurringIssuesResponse(BaseModel):
    total_recurring_clusters: int
    by_equipment: List[RecurringIssueItem]
    by_refinery_unit: List[RecurringIssueItem]
    by_department: List[RecurringIssueItem]
    by_work_type: List[RecurringIssueItem]


class BatchAnalysisResponse(BaseModel):
    status: str
    dataset_id: str
    total_reports: int
    analyzed_count: int
    sif_precursor_count: int
    high_risk_count: int
