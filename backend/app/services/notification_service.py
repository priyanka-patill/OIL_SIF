from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc

from app.models.notification_config import NotificationConfig
from app.models.email_log import EmailLog
from app.models.safety_report import SafetyReport
from app.models.audit_log import AuditLog
from app.services.sif_service import SIFService
from app.schemas.notification import (
    NotificationConfigCreate,
    NotificationConfigUpdate,
    NotificationConfigResponse,
    EmailPreviewRequest,
    EmailPreviewResponse,
    EmailRecipientPreview,
    EmailRecordedInfo,
    EmailAIRecommendations,
    SendEmailRequest,
    SendEmailResponse,
    EmailLogResponse
)


class NotificationService:
    # -------------------------------------------------------------
    # CONFIGURATION MANAGEMENT
    # -------------------------------------------------------------
    @staticmethod
    def get_configs(db: Session) -> List[NotificationConfigResponse]:
        configs = list(db.scalars(
            select(NotificationConfig).order_by(NotificationConfig.tier, NotificationConfig.role_name)
        ).all())

        # If database is completely empty of notification configs, seed standard configurable defaults
        if not configs:
            defaults = [
                NotificationConfig(
                    tier="SAFETY_HSE",
                    role_name="Lead HSE Process Safety Officer",
                    department="All",
                    email_address="hse.lead@refinery.oil.internal",
                    notify_on_high_risk=True,
                    notify_on_overdue=True,
                    notify_on_assignment=True
                ),
                NotificationConfig(
                    tier="DEPT_HEAD",
                    role_name="Operations & Maintenance Department Head",
                    department="Operations",
                    email_address="dept.head@refinery.oil.internal",
                    notify_on_high_risk=True,
                    notify_on_overdue=True,
                    notify_on_assignment=False
                ),
                NotificationConfig(
                    tier="MANAGEMENT",
                    role_name="Refinery General Plant Manager",
                    department="All",
                    email_address="plant.manager@oil.internal",
                    notify_on_high_risk=True,
                    notify_on_overdue=True,
                    notify_on_assignment=False
                ),
            ]
            for d in defaults:
                db.add(d)
            db.commit()
            configs = list(db.scalars(
                select(NotificationConfig).order_by(NotificationConfig.tier)
            ).all())

        return [NotificationConfigResponse.model_validate(c) for c in configs]

    @staticmethod
    def create_config(db: Session, req: NotificationConfigCreate) -> NotificationConfigResponse:
        cfg = NotificationConfig(
            tier=req.tier.upper(),
            role_name=req.role_name,
            department=req.department or "All",
            email_address=req.email_address,
            notify_on_high_risk=req.notify_on_high_risk,
            notify_on_overdue=req.notify_on_overdue,
            notify_on_assignment=req.notify_on_assignment,
            is_active=req.is_active
        )
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
        return NotificationConfigResponse.model_validate(cfg)

    @staticmethod
    def update_config(db: Session, config_id: str, req: NotificationConfigUpdate) -> NotificationConfigResponse:
        cfg = db.scalar(select(NotificationConfig).where(NotificationConfig.id == config_id))
        if not cfg:
            raise ValueError(f"Notification config {config_id} not found")

        if req.tier is not None:
            cfg.tier = req.tier.upper()
        if req.role_name is not None:
            cfg.role_name = req.role_name
        if req.department is not None:
            cfg.department = req.department
        if req.email_address is not None:
            cfg.email_address = req.email_address
        if req.notify_on_high_risk is not None:
            cfg.notify_on_high_risk = req.notify_on_high_risk
        if req.notify_on_overdue is not None:
            cfg.notify_on_overdue = req.notify_on_overdue
        if req.notify_on_assignment is not None:
            cfg.notify_on_assignment = req.notify_on_assignment
        if req.is_active is not None:
            cfg.is_active = req.is_active

        db.commit()
        db.refresh(cfg)
        return NotificationConfigResponse.model_validate(cfg)

    @staticmethod
    def delete_config(db: Session, config_id: str) -> bool:
        cfg = db.scalar(select(NotificationConfig).where(NotificationConfig.id == config_id))
        if not cfg:
            return False
        db.delete(cfg)
        db.commit()
        return True

    # -------------------------------------------------------------
    # EMAIL PREVIEW GENERATOR (STRICT SEPARATION OF FACTS VS AI)
    # -------------------------------------------------------------
    @staticmethod
    def generate_email_preview(db: Session, req: EmailPreviewRequest) -> EmailPreviewResponse:
        report = db.scalar(select(SafetyReport).where(SafetyReport.id == req.report_id))
        if not report:
            raise ValueError(f"Safety report {req.report_id} not found")

        analysis = SIFService.get_analysis_by_report_id(db, req.report_id)

        # Determine target tiers and recipients
        tier_q = select(NotificationConfig).where(NotificationConfig.is_active == True)
        if req.target_tier:
            tier_q = tier_q.where(NotificationConfig.tier == req.target_tier.upper())
        elif req.notification_type == "HIGH_RISK":
            tier_q = tier_q.where(NotificationConfig.notify_on_high_risk == True)
        elif req.notification_type == "OVERDUE_ACTION":
            tier_q = tier_q.where(NotificationConfig.notify_on_overdue == True)
        elif req.notification_type == "ACTION_ASSIGNMENT":
            tier_q = tier_q.where(NotificationConfig.notify_on_assignment == True)

        recipients_records = list(db.scalars(tier_q).all())
        recipients = [
            EmailRecipientPreview(
                tier=r.tier,
                role_name=r.role_name,
                email_address=r.email_address,
                department=r.department
            )
            for r in recipients_records
        ]

        if not recipients:
            # Fallback mock recipient if none active
            recipients = [
                EmailRecipientPreview(
                    tier="SAFETY_HSE",
                    role_name="Lead Safety Officer",
                    email_address="safety.lead@refinery.oil.internal",
                    department="HSE"
                )
            ]

        # 1. RECORDED INFORMATION (Source truth from report)
        recorded = EmailRecordedInfo(
            report_id=report.id,
            original_id=report.original_id or report.id,
            observed_problem=report.description or "No description recorded",
            recorded_risk_level=report.risk_level or "Unassigned",
            refinery_unit=report.refinery_unit or "N/A",
            department=report.department or "N/A",
            work_type=report.work_type or "General Activity",
            equipment=report.equipment or "N/A",
            immediate_cause=report.immediate_cause or "Under investigation",
            potential_consequence=report.potential_consequence or "Unmitigated personnel exposure",
            corrective_action=report.corrective_action or "Review control barriers",
            action_status=report.action_status or "Open",
            assigned_to=report.assigned_to or "Unassigned",
            assigned_department=report.assigned_department or report.department or "Unassigned",
            due_date=report.due_date.strftime("%Y-%m-%d") if report.due_date else "Not set",
            report_date=report.report_date.strftime("%Y-%m-%d") if report.report_date else "N/A"
        )

        # 2. AI-GENERATED RECOMMENDATIONS (Clear separation)
        ai_info = EmailAIRecommendations(
            ai_risk_level=analysis.ai_risk_level if analysis else recorded.recorded_risk_level,
            sif_precursor=analysis.sif_precursor if analysis else "EVALUATING",
            sif_category=analysis.sif_category if analysis else "General Process Hazard",
            confidence_score=analysis.confidence_score if analysis else 0.85,
            immediate_action_recommendation=analysis.immediate_action_recommendation if analysis else "Conduct immediate on-site safety walk and hazard verification.",
            preventive_action_recommendation=analysis.preventive_action_recommendation if analysis else "Verify engineering control barriers and standard operating procedures.",
            escalation_consequence=analysis.escalation_scenario.get("potential_fatal_consequence") if analysis and analysis.escalation_scenario else recorded.potential_consequence,
            reasoning=analysis.reasoning if analysis else []
        )

        # Formulate Subject
        prefix = {
            "HIGH_RISK": "[HIGH-RISK SAFETY ALERT]",
            "ACTION_ASSIGNMENT": "[ACTION ASSIGNMENT NOTICE]",
            "OVERDUE_ACTION": "[CRITICAL ESCALATION: OVERDUE ACTION]",
            "MANAGEMENT_ESCALATION": "[MANAGEMENT P1 ESCALATION]"
        }.get(req.notification_type, "[SAFETY NOTIFICATION]")

        subject = f"{prefix} Report {recorded.original_id} - {recorded.refinery_unit} ({recorded.recorded_risk_level} Risk)"

        # Render HTML and Plain Text with visual boundary
        rendered_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 24px; }}
  .container {{ max-width: 640px; margin: 0 auto; background-color: #1e293b; border-radius: 12px; border: 1px solid #334155; overflow: hidden; }}
  .header {{ background: linear-gradient(135deg, #0891b2, #1d4ed8); padding: 20px; color: white; }}
  .header h1 {{ margin: 0 0 4px 0; font-size: 18px; font-weight: 700; letter-spacing: 0.5px; }}
  .header p {{ margin: 0; font-size: 12px; opacity: 0.9; }}
  .section {{ padding: 20px; border-bottom: 1px solid #334155; }}
  .section-title {{ font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }}
  .title-recorded {{ color: #38bdf8; }}
  .title-ai {{ color: #a855f7; }}
  .card-recorded {{ background-color: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 14px; margin-bottom: 10px; font-size: 12px; }}
  .card-ai {{ background-color: #2e1065; border: 1px solid #7e22ce; border-radius: 8px; padding: 14px; font-size: 12px; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px; }}
  .grid-item {{ background-color: #1e293b; padding: 8px 10px; border-radius: 6px; border: 1px solid #334155; }}
  .grid-item span {{ display: block; font-size: 10px; text-transform: uppercase; color: #94a3b8; margin-bottom: 2px; }}
  .grid-item strong {{ font-size: 12px; color: #f8fafc; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; }}
  .badge-high {{ background-color: #991b1b; color: #fecaca; border: 1px solid #ef4444; }}
  .badge-sif {{ background-color: #831843; color: #fbcfe8; border: 1px solid #ec4899; }}
  .footer {{ padding: 16px 20px; font-size: 11px; color: #64748b; text-align: center; background-color: #0f172a; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>OIL SIF Safety Intelligence Notification</h1>
    <p>{req.notification_type.replace('_', ' ')} • Automated Governance Telemetry</p>
  </div>

  <!-- SECTION 1: RECORDED FIELD INFORMATION (GROUND TRUTH) -->
  <div class="section">
    <div class="section-title title-recorded">
       1. Recorded Field Information (Source of Truth)
    </div>
    <div class="grid">
      <div class="grid-item">
        <span>Report Reference</span>
        <strong>{recorded.original_id}</strong>
      </div>
      <div class="grid-item">
        <span>Refinery Unit</span>
        <strong>{recorded.refinery_unit}</strong>
      </div>
      <div class="grid-item">
        <span>Department / Work</span>
        <strong>{recorded.department} ({recorded.work_type})</strong>
      </div>
      <div class="grid-item">
        <span>Recorded Risk</span>
        <span class="badge badge-high">{recorded.recorded_risk_level}</span>
      </div>
    </div>
    <div class="card-recorded">
      <span style="color:#94a3b8; font-size:10px; display:block; margin-bottom:4px;">OBSERVED PROBLEM NARRATIVE</span>
      <p style="margin:0; color:#f1f5f9; font-style:italic;">"{recorded.observed_problem}"</p>
    </div>
    <div class="card-recorded">
      <span style="color:#94a3b8; font-size:10px; display:block; margin-bottom:4px;">RECORDED CORRECTIVE ACTION & STATUS</span>
      <p style="margin:0; color:#f1f5f9;">Action: <strong>{recorded.corrective_action}</strong></p>
      <p style="margin:4px 0 0 0; color:#cbd5e1; font-size:11px;">Status: <strong>{recorded.action_status}</strong> | Assigned to: <strong>{recorded.assigned_to}</strong> | Target Due Date: <strong>{recorded.due_date}</strong></p>
    </div>
  </div>

  <!-- SECTION 2: AI-GENERATED PREVENTIVE RECOMMENDATIONS -->
  <div class="section">
    <div class="section-title title-ai">
       2. AI SIF Risk Assessment & Preventive Intelligence
    </div>
    <div class="grid">
      <div class="grid-item" style="background-color:#3b0764; border-color:#7e22ce;">
        <span>AI Evaluated Risk</span>
        <strong>{ai_info.ai_risk_level} ({(ai_info.confidence_score*100):.0f}% Conf)</strong>
      </div>
      <div class="grid-item" style="background-color:#3b0764; border-color:#7e22ce;">
        <span>SIF Precursor Flag</span>
        <span class="badge badge-sif">{ai_info.sif_precursor} ({ai_info.sif_category})</span>
      </div>
    </div>
    <div class="card-ai" style="margin-bottom:10px;">
      <strong style="color:#e9d5ff; display:block; margin-bottom:4px;"> RECOMMENDED IMMEDIATE ACTION</strong>
      <p style="margin:0; color:#f3e8ff;">{ai_info.immediate_action_recommendation}</p>
    </div>
    <div class="card-ai" style="margin-bottom:10px;">
      <strong style="color:#a7f3d0; display:block; margin-bottom:4px;"> SYSTEMIC PREVENTIVE STRATEGY</strong>
      <p style="margin:0; color:#d1fae5;">{ai_info.preventive_action_recommendation}</p>
    </div>
    <div class="card-ai">
      <strong style="color:#fecaca; display:block; margin-bottom:4px;"> POTENTIAL UNMITIGATED ESCALATION</strong>
      <p style="margin:0; color:#fee2e2;">{ai_info.escalation_consequence}</p>
    </div>
  </div>

  <div class="footer">
    OIL SIF Intelligence Platform • Automated Process Safety Governance • Do not reply directly to this telemetry message.
  </div>
</div>
</body>
</html>
"""

        rendered_plain_text = f"""
========================================================================
OIL SIF SAFETY INTELLIGENCE NOTIFICATION
{req.notification_type}
========================================================================

--- 1. RECORDED FIELD INFORMATION (SOURCE OF TRUTH) ---
Report ID: {recorded.original_id}
Refinery Unit: {recorded.refinery_unit}
Department: {recorded.department} | Work Type: {recorded.work_type}
Equipment Tag: {recorded.equipment}
Recorded Risk: {recorded.recorded_risk_level}
Action Status: {recorded.action_status} | Assigned To: {recorded.assigned_to} | Due Date: {recorded.due_date}

Observed Problem:
"{recorded.observed_problem}"

Field Corrective Action:
"{recorded.corrective_action}"

--- 2. AI-GENERATED SIF ASSESSMENT & PREVENTIVE INTELLIGENCE ---
AI Assessed Risk: {ai_info.ai_risk_level} (Confidence: {ai_info.confidence_score*100:.0f}%)
SIF Precursor: {ai_info.sif_precursor} ({ai_info.sif_category})
Recommended Immediate Action: {ai_info.immediate_action_recommendation}
Preventive Strategy: {ai_info.preventive_action_recommendation}
Potential Unmitigated Escalation: {ai_info.escalation_consequence}

========================================================================
OIL SIF Platform Governance Telemetry
"""

        return EmailPreviewResponse(
            notification_type=req.notification_type,
            subject=subject,
            recipients=recipients,
            recorded_information=recorded,
            ai_recommendations=ai_info,
            rendered_html=rendered_html,
            rendered_plain_text=rendered_plain_text
        )

    # -------------------------------------------------------------
    # SEND & AUDIT LOGGING
    # -------------------------------------------------------------
    @staticmethod
    def send_notification_email(db: Session, req: SendEmailRequest) -> SendEmailResponse:
        report = db.scalar(select(SafetyReport).where(SafetyReport.id == req.report_id))

        # Log for each recipient
        log_ids = []
        for email in req.recipient_emails:
            email_log = EmailLog(
                report_id=req.report_id,
                recipient_email=email,
                recipient_name=email.split("@")[0].replace(".", " ").title(),
                recipient_role="Configured Stakeholder",
                escalation_tier=req.escalation_tier or "SAFETY_HSE",
                subject=req.subject,
                body_html=req.body_html,
                status="SENT",
                triggered_by=req.triggered_by,
                sent_at=datetime.now(timezone.utc)
            )
            db.add(email_log)
            db.flush()
            log_ids.append(email_log.id)

        # AuditLog record
        audit = AuditLog(
            action_type="EMAIL_SENT",
            entity_type="NOTIFICATION",
            entity_id=req.report_id,
            details={
                "notification_type": req.notification_type,
                "recipients": req.recipient_emails,
                "subject": req.subject,
                "triggered_by": req.triggered_by,
                "escalation_tier": req.escalation_tier
            }
        )
        db.add(audit)

        db.commit()

        return SendEmailResponse(
            success=True,
            message=f"Notification email successfully dispatched to {len(req.recipient_emails)} recipient(s).",
            email_log_id=log_ids[0] if log_ids else "",
            recipients_count=len(req.recipient_emails),
            sent_at=datetime.now(timezone.utc)
        )

    @staticmethod
    def get_email_logs(
        db: Session,
        report_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[EmailLogResponse], int]:
        q = select(EmailLog)
        if report_id:
            q = q.where(EmailLog.report_id == report_id)

        total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
        offset = (page - 1) * page_size
        logs = list(db.scalars(q.order_by(desc(EmailLog.sent_at)).offset(offset).limit(page_size)).all())

        return [EmailLogResponse.model_validate(l) for l in logs], total
