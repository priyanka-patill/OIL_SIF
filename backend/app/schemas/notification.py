from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class NotificationConfigBase(BaseModel):
    tier: str = Field(..., description="SAFETY_HSE, DEPT_HEAD, MANAGEMENT")
    role_name: str = Field(..., description="E.g., Safety Lead, Operations Head, Plant Manager")
    department: Optional[str] = Field("All", description="Target department or 'All'")
    email_address: str = Field(..., description="Configured recipient email address")
    notify_on_high_risk: bool = Field(True, description="Notify when high risk report is logged/analyzed")
    notify_on_overdue: bool = Field(True, description="Notify when action becomes overdue")
    notify_on_assignment: bool = Field(True, description="Notify when action is assigned to department/person")
    is_active: bool = Field(True, description="Whether recipient is active")


class NotificationConfigCreate(NotificationConfigBase):
    pass


class NotificationConfigUpdate(BaseModel):
    tier: Optional[str] = None
    role_name: Optional[str] = None
    department: Optional[str] = None
    email_address: Optional[str] = None
    notify_on_high_risk: Optional[bool] = None
    notify_on_overdue: Optional[bool] = None
    notify_on_assignment: Optional[bool] = None
    is_active: Optional[bool] = None


class NotificationConfigResponse(NotificationConfigBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime


class EmailPreviewRequest(BaseModel):
    report_id: str
    notification_type: str = Field("HIGH_RISK", description="HIGH_RISK, ACTION_ASSIGNMENT, OVERDUE_ACTION, MANAGEMENT_ESCALATION")
    target_tier: Optional[str] = Field(None, description="Optional override tier: SAFETY_HSE, DEPT_HEAD, MANAGEMENT")
    custom_notes: Optional[str] = None


class EmailRecipientPreview(BaseModel):
    tier: str
    role_name: str
    email_address: str
    department: Optional[str] = None


class EmailRecordedInfo(BaseModel):
    report_id: str
    original_id: Optional[str] = None
    observed_problem: str
    recorded_risk_level: str
    refinery_unit: Optional[str] = None
    department: Optional[str] = None
    work_type: Optional[str] = None
    equipment: Optional[str] = None
    immediate_cause: Optional[str] = None
    potential_consequence: Optional[str] = None
    corrective_action: Optional[str] = None
    action_status: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_department: Optional[str] = None
    due_date: Optional[str] = None
    report_date: Optional[str] = None


class EmailAIRecommendations(BaseModel):
    ai_risk_level: str
    sif_precursor: str
    sif_category: Optional[str] = None
    confidence_score: float
    immediate_action_recommendation: str
    preventive_action_recommendation: str
    escalation_consequence: Optional[str] = None
    reasoning: List[str] = []


class EmailPreviewResponse(BaseModel):
    notification_type: str
    subject: str
    recipients: List[EmailRecipientPreview]
    recorded_information: EmailRecordedInfo
    ai_recommendations: EmailAIRecommendations
    rendered_html: str
    rendered_plain_text: str


class SendEmailRequest(BaseModel):
    report_id: str
    notification_type: str
    recipient_emails: List[str]
    subject: str
    body_html: str
    triggered_by: str = "Safety Officer"
    escalation_tier: Optional[str] = "SAFETY_HSE"


class SendEmailResponse(BaseModel):
    success: bool
    message: str
    email_log_id: str
    recipients_count: int
    sent_at: datetime


class EmailLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    report_id: Optional[str] = None
    recipient_email: str
    recipient_name: Optional[str] = None
    recipient_role: Optional[str] = None
    escalation_tier: Optional[str] = None
    subject: str
    body_html: str
    status: str
    triggered_by: Optional[str] = None
    sent_at: datetime
