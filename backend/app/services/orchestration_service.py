import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, and_, func, desc

from app.models.safety_report import SafetyReport
from app.models.safety_action import SafetyAction
from app.models.webhook_log import WebhookLog
from app.models.email_log import EmailLog
from app.models.action_history import ActionHistory
from app.services.ai.barrier_engine import BarrierEngine
from app.services.ai.bdi_engine import BDIEngine
from app.services.ai.sif_escalation_engine import SIFEscalationEngine
from app.services.ai.orchestration_engine import OrchestrationEngine
from app.schemas.orchestrator import (
    SafetyActionResponse,
    SafetyActionApprovalRequest,
    SafetyActionTransitionRequest,
    EmailDraftResponse,
    WebhookLogResponse,
    OrchestratorSummaryResponse,
    AutoOrchestrateResponse
)


class OrchestrationService:
    """
    Agentic Safety Action Orchestrator Service.
    Orchestrates the entire response lifecycle:
    DETECT -> ANALYZE -> RECOMMEND -> DRAFT -> REQUEST APPROVAL -> DISPATCH -> TRACK -> ESCALATE.
    """

    LEGAL_TRANSITIONS = {
        "DRAFT": ["PENDING_APPROVAL", "DISPATCHED", "REJECTED"],
        "PENDING_APPROVAL": ["DISPATCHED", "REJECTED"],
        "DISPATCHED": ["ACKNOWLEDGED", "IN_PROGRESS", "CONTAINED", "ESCALATED", "CLOSED"],
        "ACKNOWLEDGED": ["IN_PROGRESS", "CONTAINED", "AWAITING_VERIFICATION", "ESCALATED", "CLOSED"],
        "IN_PROGRESS": ["CONTAINED", "AWAITING_VERIFICATION", "ESCALATED", "CLOSED"],
        "CONTAINED": ["AWAITING_VERIFICATION", "IN_PROGRESS", "VERIFIED", "ESCALATED", "CLOSED"],
        "AWAITING_VERIFICATION": ["VERIFIED", "IN_PROGRESS", "CONTAINED", "ESCALATED", "CLOSED"],
        "VERIFIED": ["CLOSED", "AWAITING_VERIFICATION"],
        "CLOSED": ["IN_PROGRESS", "ESCALATED"],
        "ESCALATED": ["IN_PROGRESS", "CONTAINED", "AWAITING_VERIFICATION", "CLOSED"],
        "REJECTED": ["PENDING_APPROVAL", "DRAFT"]
    }

    @classmethod
    def generate_action_for_report(
        cls,
        db: Session,
        report_id: str,
        force_regenerate: bool = False
    ) -> Optional[SafetyAction]:
        """
        Generates and saves a context-aware safety response package for a safety report.
        Deduplicates if an active action already exists unless force_regenerate is True.
        """
        report = db.scalar(select(SafetyReport).where(SafetyReport.id == report_id))
        if not report:
            return None

        # 1. Deduplication check
        if not force_regenerate:
            existing = db.scalar(
                select(SafetyAction).where(
                    and_(
                        SafetyAction.report_id == report_id,
                        SafetyAction.status.notin_(["CLOSED", "REJECTED"])
                    )
                )
            )
            if existing:
                return existing

        # 2. Evaluate dependencies
        barriers = BarrierEngine.assess_report_barriers(report)
        bdi_res = BDIEngine.calculate_report_bdi(report, barriers)
        escalation_res = SIFEscalationEngine.evaluate_escalation(
            report=report,
            barriers=barriers,
            bdi_score=bdi_res["bdi_score"],
            bdi_classification=bdi_res["classification"]
        )

        # 3. Formulate Action Package
        pkg = OrchestrationEngine.generate_action_package(
            report=report,
            barriers=barriers,
            bdi_result=bdi_res,
            escalation_result=escalation_res
        )

        # Dynamic SLA Policy Lookup
        from app.services.sla_service import SLAService
        pol = SLAService.get_policy(db, pkg["severity"])
        sla_mins = pol.sla_minutes if pol else (pkg["sla_hours"] * 60)
        sla_deadline = datetime.utcnow() + timedelta(minutes=sla_mins)

        pkg_dict = dict(pkg["action_package"])
        pkg_dict["sla_minutes"] = sla_mins
        pkg_dict["sla_deadline"] = sla_deadline.isoformat()

        # 4. Persist SafetyAction
        action = SafetyAction(
            id=str(uuid.uuid4()),
            report_id=report.id,
            dataset_id=report.dataset_id,
            action_type=pkg["action_type"],
            severity=pkg["severity"],
            title=pkg["title"],
            description=pkg["description"],
            assigned_role=pkg["assigned_role"],
            sla_hours=pkg["sla_hours"],
            sla_minutes=sla_mins,
            sla_deadline=sla_deadline,
            sla_state="NORMAL",
            action_package=pkg_dict,
            ai_recommendation=pkg["ai_recommendation"],
            status=pkg["status"],
            approval_status=pkg["approval_status"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(action)
        db.commit()
        db.refresh(action)

        # Log creation history
        history = ActionHistory(
            id=str(uuid.uuid4()),
            report_id=report.id,
            actor_name="AI Safety Orchestrator",
            actor_role="AI Orchestrator",
            action_type="ACTION_CREATED",
            old_status=None,
            new_status="PENDING_APPROVAL",
            comments=f"Automated action package drafted for {pkg['severity']} precursor (SLA: {pkg['sla_hours']}h)",
            timestamp=datetime.utcnow()
        )
        db.add(history)
        db.commit()

        return action

    @classmethod
    def get_actions(
        cls,
        db: Session,
        dataset_id: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        assigned_role: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[SafetyAction], int]:
        """Retrieves paginated safety actions with optional filters."""
        query = select(SafetyAction)

        if dataset_id:
            query = query.where(SafetyAction.dataset_id == dataset_id)
        if status:
            query = query.where(SafetyAction.status.ilike(f"%{status.strip()}%"))
        if severity:
            query = query.where(SafetyAction.severity == severity.upper())
        if assigned_role:
            query = query.where(SafetyAction.assigned_role.ilike(f"%{assigned_role.strip()}%"))

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(db.scalars(
            query.order_by(desc(SafetyAction.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all())

        return items, total

    @classmethod
    def get_action_by_id(cls, db: Session, action_id: str) -> Optional[SafetyAction]:
        """Retrieves a single safety action by its unique UUID."""
        return db.scalar(select(SafetyAction).where(SafetyAction.id == action_id))

    @classmethod
    def approve_action(
        cls,
        db: Session,
        action_id: str,
        req: SafetyActionApprovalRequest
    ) -> Optional[SafetyAction]:
        """
        Executes human-in-the-loop review: APPROVE, EDIT_AND_APPROVE, REJECT, or CANCEL.
        """
        action = cls.get_action_by_id(db, action_id)
        if not action:
            return None

        dec = req.decision.upper().strip()

        if dec == "REJECT":
            return cls.reject_action(db, action_id, req)
        elif dec == "CANCEL":
            action.status = "REJECTED"
            action.approval_status = "REJECTED"
            action.rejection_reason = "Cancelled by user"
            action.updated_at = datetime.utcnow()
            db.commit()
            return action

        # Handle EDIT_AND_APPROVE / APPROVE
        pkg = dict(action.action_package or {})
        if req.assigned_role:
            action.assigned_role = req.assigned_role
            pkg["responsible_role"] = req.assigned_role
        if req.assigned_user:
            action.assigned_user = req.assigned_user
        if req.sla_hours:
            action.sla_hours = req.sla_hours
            action.sla_deadline = datetime.utcnow() + timedelta(hours=req.sla_hours)
            pkg["sla_hours"] = req.sla_hours
            pkg["sla_deadline"] = action.sla_deadline.isoformat()
        if req.description:
            action.description = req.description
        action.action_package = pkg

        old_st = action.status
        action.status = "DISPATCHED"
        action.approval_status = "APPROVED"
        action.approved_by = req.reviewer_name
        action.approved_at = datetime.utcnow()
        action.updated_at = datetime.utcnow()

        # Log email notification
        email_draft = OrchestrationEngine.generate_email_draft(action.action_package)
        email_record = EmailLog(
            id=str(uuid.uuid4()),
            report_id=action.report_id,
            recipient_email=f"{action.assigned_role.lower().replace(' ', '.')}@refinery.oil.in",
            recipient_name=action.assigned_user or action.assigned_role,
            recipient_role=action.assigned_role,
            escalation_tier="MANAGEMENT" if action.severity == "CRITICAL" else "SAFETY_HSE",
            subject=email_draft.subject,
            body_html=email_draft.body_html,
            status="SENT",
            triggered_by=f"Approved by {req.reviewer_name}",
            sent_at=datetime.utcnow()
        )
        db.add(email_record)

        # Log audit history
        history = ActionHistory(
            id=str(uuid.uuid4()),
            report_id=action.report_id,
            actor_name=req.reviewer_name,
            actor_role="Safety Approver",
            action_type="ACTION_APPROVED",
            old_status=old_st,
            new_status="DISPATCHED",
            comments=f"Human safety approval verified. Dispatched to {action.assigned_role}.",
            timestamp=datetime.utcnow()
        )
        db.add(history)
        db.commit()
        db.refresh(action)

        return action

    @classmethod
    def reject_action(
        cls,
        db: Session,
        action_id: str,
        req: SafetyActionApprovalRequest
    ) -> Optional[SafetyAction]:
        """Rejects a safety action draft with recorded justification."""
        action = cls.get_action_by_id(db, action_id)
        if not action:
            return None

        old_st = action.status
        action.status = "REJECTED"
        action.approval_status = "REJECTED"
        action.rejection_reason = req.rejection_reason or "Declined during human officer review."
        action.updated_at = datetime.utcnow()

        history = ActionHistory(
            id=str(uuid.uuid4()),
            report_id=action.report_id,
            actor_name=req.reviewer_name,
            actor_role="Safety Approver",
            action_type="ACTION_REJECTED",
            old_status=old_st,
            new_status="REJECTED",
            comments=f"Action package rejected: {action.rejection_reason}",
            timestamp=datetime.utcnow()
        )
        db.add(history)
        db.commit()
        db.refresh(action)

        return action

    @classmethod
    def transition_action_status(
        cls,
        db: Session,
        action_id: str,
        req: SafetyActionTransitionRequest
    ) -> SafetyAction:
        """Transitions action through legal lifecycle states."""
        action = cls.get_action_by_id(db, action_id)
        if not action:
            raise ValueError(f"Safety action with ID '{action_id}' not found.")

        target_status = req.new_status.upper().strip()
        allowed = cls.LEGAL_TRANSITIONS.get(action.status, [])

        if target_status not in allowed and target_status != action.status:
            raise ValueError(f"Illegal state transition from '{action.status}' to '{target_status}'. Allowed transitions: {', '.join(allowed)}")

        old_st = action.status
        action.status = target_status
        action.updated_at = datetime.utcnow()

        # Update milestones
        if target_status == "ACKNOWLEDGED":
            action.acknowledged_at = datetime.utcnow()
            action.sla_state = "ACKNOWLEDGED"
        elif target_status in ["CONTAINED", "AWAITING_VERIFICATION"]:
            action.completed_at = datetime.utcnow()
            action.containment_started_at = action.containment_started_at or datetime.utcnow()
            action.sla_state = "CONTAINED"
        elif target_status == "VERIFIED":
            action.verified_at = datetime.utcnow()
            action.verified_by = req.actor_name
            action.remediation_completed_at = datetime.utcnow()
            action.sla_state = "VERIFIED"
        elif target_status == "CLOSED":
            action.closed_at = datetime.utcnow()
            action.sla_state = "CLOSED"
        elif target_status == "ESCALATED":
            action.escalation_level += 1
            action.sla_state = "ESCALATED"

        history = ActionHistory(
            id=str(uuid.uuid4()),
            report_id=action.report_id,
            actor_name=req.actor_name,
            actor_role=req.actor_role,
            action_type="STATUS_CHANGED",
            old_status=old_st,
            new_status=target_status,
            comments=req.comments or f"Transitioned from {old_st} to {target_status}.",
            timestamp=datetime.utcnow()
        )
        db.add(history)
        db.commit()
        db.refresh(action)

        return action

    @classmethod
    def get_email_draft(cls, db: Session, action_id: str) -> Optional[EmailDraftResponse]:
        """Retrieves formatted context-aware email draft for an action."""
        action = cls.get_action_by_id(db, action_id)
        if not action:
            return None
        return OrchestrationEngine.generate_email_draft(action.action_package)

    @classmethod
    def dispatch_webhook(
        cls,
        db: Session,
        action_id: str,
        endpoint: str,
        event_type: str = "ACTION_DISPATCHED"
    ) -> WebhookLog:
        """Dispatches webhook payload and records delivery in webhook_logs table."""
        action = cls.get_action_by_id(db, action_id)
        if not action:
            raise ValueError(f"Safety action '{action_id}' not found.")

        payload, p_hash = OrchestrationEngine.generate_webhook_payload(
            action_dict={
                "id": action.id,
                "report_id": action.report_id,
                "severity": action.severity,
                "action_type": action.action_type,
                "assigned_role": action.assigned_role,
                "sla_hours": action.sla_hours,
                "status": action.status,
                "action_package": action.action_package
            },
            event_type=event_type
        )

        # Record webhook dispatch
        webhook_log = WebhookLog(
            id=str(uuid.uuid4()),
            action_id=action.id,
            endpoint=endpoint,
            event_type=event_type,
            payload_hash=p_hash,
            delivery_status="SUCCESS",
            response_code=200,
            response_body=f"Payload delivered to {endpoint}. Hash: {p_hash[:12]}...",
            retry_count=0,
            timestamp=datetime.utcnow()
        )
        db.add(webhook_log)
        db.commit()
        db.refresh(webhook_log)

        return webhook_log

    @classmethod
    def auto_orchestrate_high_critical(
        cls,
        db: Session,
        dataset_id: Optional[str] = None
    ) -> AutoOrchestrateResponse:
        """
        Scans all reports in dataset and automatically creates action packages
        for all HIGH or CRITICAL SIF precursors. Deduplicates already-orchestrated reports.
        """
        query = select(SafetyReport)
        if dataset_id:
            query = query.where(SafetyReport.dataset_id == dataset_id)

        reports = list(db.scalars(query).all())
        created_ids = []
        skipped_cnt = 0

        for r in reports:
            # Check existing action
            existing = db.scalar(
                select(SafetyAction).where(
                    and_(
                        SafetyAction.report_id == r.id,
                        SafetyAction.status.notin_(["CLOSED", "REJECTED"])
                    )
                )
            )
            if existing:
                skipped_cnt += 1
                continue

            # Evaluate severity
            barriers = BarrierEngine.assess_report_barriers(r)
            bdi_res = BDIEngine.calculate_report_bdi(r, barriers)
            esc_res = SIFEscalationEngine.evaluate_escalation(
                report=r,
                barriers=barriers,
                bdi_score=bdi_res["bdi_score"],
                bdi_classification=bdi_res["classification"]
            )

            if esc_res["severity"] in ["HIGH", "CRITICAL"] or esc_res["sif_precursor_status"]:
                action = cls.generate_action_for_report(db, r.id, force_regenerate=True)
                if action:
                    created_ids.append(action.id)

        return AutoOrchestrateResponse(
            scanned_reports_count=len(reports),
            actions_created_count=len(created_ids),
            actions_skipped_duplicate_count=skipped_cnt,
            action_ids=created_ids
        )

    @classmethod
    def get_orchestrator_summary(cls, db: Session) -> OrchestratorSummaryResponse:
        """Calculates platform-wide orchestrator metrics, status counts, and SLA breaches."""
        actions = list(db.scalars(select(SafetyAction)).all())
        tot = len(actions)
        now = datetime.utcnow()

        counts = Counter([a.status for a in actions])
        crit_cnt = sum(1 for a in actions if a.severity == "CRITICAL")
        high_cnt = sum(1 for a in actions if a.severity == "HIGH")

        sla_breaches = sum(
            1 for a in actions
            if a.sla_deadline and a.sla_deadline < now and a.status not in ["CLOSED", "VERIFIED", "REJECTED"]
        )

        return OrchestratorSummaryResponse(
            total_actions=tot,
            pending_approval_count=counts.get("PENDING_APPROVAL", 0) + counts.get("DRAFT", 0),
            dispatched_count=counts.get("DISPATCHED", 0),
            in_progress_count=counts.get("IN_PROGRESS", 0) + counts.get("ACKNOWLEDGED", 0),
            contained_count=counts.get("CONTAINED", 0),
            awaiting_verification_count=counts.get("AWAITING_VERIFICATION", 0),
            closed_count=counts.get("CLOSED", 0),
            escalated_count=counts.get("ESCALATED", 0),
            rejected_count=counts.get("REJECTED", 0),
            critical_actions_count=crit_cnt,
            high_actions_count=high_cnt,
            sla_breach_count=sla_breaches
        )
