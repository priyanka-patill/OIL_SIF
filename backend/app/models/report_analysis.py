import uuid
from datetime import datetime
from sqlalchemy import String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class ReportAnalysis(Base):
    __tablename__ = "report_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id: Mapped[str] = mapped_column(String(36), ForeignKey("safety_reports.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    model_version: Mapped[str] = mapped_column(String(50), default="sif-nlp-v2.0")

    # NLP Extracted Entities & Context
    observed_problem: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_ppe_items: Mapped[list] = mapped_column(JSON, default=list)
    extracted_ppe_issue_type: Mapped[str] = mapped_column(String(50), default="NONE")  # MISSING_PPE, DAMAGED_PPE, IMPROPER_PPE, BYPASS_PPE, NONE
    hazard_identified: Mapped[str] = mapped_column(Text, nullable=False)
    exposure_target: Mapped[str] = mapped_column(Text, nullable=False)
    immediate_cause: Mapped[str | None] = mapped_column(String(255), nullable=True)
    potential_consequence: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Risk Assessment (Recorded Risk vs AI Predicted Risk Separation)
    recorded_risk_level: Mapped[str] = mapped_column(String(50), nullable=False)  # Preserved from source record
    ai_risk_level: Mapped[str] = mapped_column(String(50), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    sif_precursor: Mapped[str] = mapped_column(String(50), nullable=False)  # YES, NO, UNCERTAIN
    sif_category: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.85)

    # Explainable AI & IOGP Life-Saving Rules
    reasoning: Mapped[list] = mapped_column(JSON, default=list)
    iogp_rule: Mapped[str] = mapped_column(String(100), default="No clear Life-Saving Rule match")
    secondary_iogp_rules: Mapped[list] = mapped_column(JSON, default=list)
    iogp_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    iogp_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    barrier_failure: Mapped[str | None] = mapped_column(Text, nullable=True)
    missing_control: Mapped[str | None] = mapped_column(Text, nullable=True)
    existing_barrier: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Recurrence & Systemic Risk
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_score: Mapped[float] = mapped_column(Float, default=0.0)
    recurrence_details: Mapped[dict] = mapped_column(JSON, default=dict)

    # Preventive & Action Intelligence
    immediate_action_recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    preventive_action_recommendation: Mapped[str] = mapped_column(Text, nullable=False)

    # 6-Stage Risk Escalation Scenario
    escalation_scenario: Mapped[dict] = mapped_column(JSON, default=dict)

    # Human / Organizational Factors Analyzed
    organizational_factors: Mapped[list] = mapped_column(JSON, default=list)

    # Human Review & Overrides
    human_overridden: Mapped[bool] = mapped_column(Boolean, default=False)
    human_risk_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    human_sif_precursor: Mapped[str | None] = mapped_column(String(50), nullable=True)
    human_feedback_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    report: Mapped["SafetyReport"] = relationship("SafetyReport", lazy="joined")
    feedback: Mapped[list["AIFeedback"]] = relationship("AIFeedback", back_populates="analysis", cascade="all, delete-orphan", lazy="selectin")

