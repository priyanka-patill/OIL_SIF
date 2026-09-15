from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class HumanFeedbackCreate(BaseModel):
    report_id: str
    analysis_id: Optional[str] = None
    action_id: Optional[str] = None
    reviewer_name: str = Field(default="Safety Officer")
    reviewer_role: str = Field(default="Safety Officer")
    rating: str = Field(description="CORRECT, INCORRECT, PARTIALLY_CORRECT, NOT_USEFUL")
    feedback_category: str = Field(default="SIF_PRECURSOR", description="BDI_SCORING, BARRIER_CLASSIFICATION, SIF_PRECURSOR, ACTION_RECOMMENDATION, CORRELATION")
    human_risk_level: Optional[str] = None
    human_sif_status: Optional[str] = None
    comments: Optional[str] = None
    is_simulated: bool = False


class HumanFeedbackResponse(BaseModel):
    id: str
    report_id: str
    analysis_id: Optional[str] = None
    action_id: Optional[str] = None
    reviewer_name: str
    reviewer_role: str
    rating: str
    feedback_category: str
    human_risk_level: Optional[str] = None
    human_sif_status: Optional[str] = None
    comments: Optional[str] = None
    is_simulated: bool
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeedbackStatsResponse(BaseModel):
    total_feedback_count: int
    agreement_rate_percentage: float
    ratings_breakdown: Dict[str, int]
    categories_breakdown: Dict[str, int]
    recent_feedbacks: List[HumanFeedbackResponse]
