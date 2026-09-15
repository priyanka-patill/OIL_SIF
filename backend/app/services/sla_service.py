import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc, and_

from app.models.safety_action import SafetyAction
from app.models.sla_policy import SLAPolicy
from app.models.escalation_log import EscalationLog
from app.models.email_log import EmailLog
from app.models.action_history import ActionHistory
from app.services.ai.sla_engine import SLAEngine
from app.schemas.sla import (
    SLAPolicyResponse,
    SLAPolicyUpdateRequest,
    SLACountdownResponse,
    SLAActionItemResponse,
    SLADashboardResponse,
    SLAAcknowledgeRequest
)


class SLAService:
    """
    SLA Monitoring and Escalation Management Service.
    Handles dynamic SLA policies, countdown calculations, human acknowledgements,
    multi-level escalation triggers, and dashboard metrics.
    """

    @classmethod
    def get_or_create_policies(cls, db: Session) -> List[SLAPolicy]:
        """Ensures default SLA policies exist in database and returns all active policies."""
        existing = list(db.scalars(select(SLAPolicy)).all())
        existing_map = {p.severity.upper(): p for p in existing}

        for sev, def_data in SLAEngine.DEFAULT_POLICIES.items():
            if sev not in existing_map:
                policy = SLAPolicy(
                    id=str(uuid.uuid4()),
                    severity=sev,
                    sla_minutes=def_data["sla_minutes"],
                    reminder_minutes=def_data["reminder_minutes"],
                    warning_minutes=def_data["warning_minutes"],
                    escalation_interval_minutes=def_data["escalation_interval_minutes"],
                    escalation_level_0_role=def_data["level_0"],
                    escalation_level_1_role=def_data["level_1"],
                    escalation_level_2_role=def_data["level_2"],
                    escalation_level_3_role=def_data["level_3"],
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(policy)
                existing.append(policy)

        db.commit()
        return existing

    @classmethod
    def get_policy(cls, db: Session, severity: str) -> Optional[SLAPolicy]:
        """Retrieves a single SLA policy by severity name."""
        cls.get_or_create_policies(db)
        return db.scalar(select(SLAPolicy).where(SLAPolicy.severity == severity.upper()))

    @classmethod
    def update_policy(cls, db: Session, severity: str, req: SLAPolicyUpdateRequest) -> SLAPolicy:
        """Updates an existing SLA policy."""
        cls.get_or_create_policies(db)
        policy = db.scalar(select(SLAPolicy).where(SLAPolicy.severity == severity.upper()))
        if not policy:
            raise ValueError(f"SLA policy for severity '{severity}' not found.")

        if req.sla_minutes is not None:
            policy.sla_minutes = req.sla_minutes
        if req.reminder_minutes is not None:
            policy.reminder_minutes = req.reminder_minutes
        if req.warning_minutes is not None:
            policy.warning_minutes = req.warning_minutes
        if req.escalation_interval_minutes is not None:
            policy.escalation_interval_minutes = req.escalation_interval_minutes
        if req.escalation_level_0_role is not None:
            policy.escalation_level_0_role = req.escalation_level_0_role
        if req.escalation_level_1_role is not None:
            policy.escalation_level_1_role = req.escalation_level_1_role
        if req.escalation_level_2_role is not None:
            policy.escalation_level_2_role = req.escalation_level_2_role
        if req.escalation_level_3_role is not None:
            policy.escalation_level_3_role = req.escalation_level_3_role
        if req.is_active is not None:
            policy.is_active = req.is_active

        policy.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(policy)
        return policy

    @classmethod
    def acknowledge_action(
        cls,
        db: Session,
        action_id: str,
        req: SLAAcknowledgeRequest,
        now: Optional[datetime] = None
    ) -> SafetyAction:
        """Records human acknowledgment, stopping SLA breach countdown."""
        curr = now or datetime.utcnow()
        action = db.scalar(select(SafetyAction).where(SafetyAction.id == action_id))
        if not action:
            raise ValueError(f"Safety action '{action_id}' not found.")

        old_st = action.status
        action.acknowledged_at = curr
        if action.status in ["DISPATCHED", "PENDING_APPROVAL"]:
            action.status = "ACKNOWLEDGED"
        action.sla_state = "ACKNOWLEDGED"
        action.updated_at = curr

        history = ActionHistory(
            id=str(uuid.uuid4()),
            report_id=action.report_id,
            actor_name=req.actor_name,
            actor_role=req.actor_role,
            action_type="ACTION_ACKNOWLEDGED",
            old_status=old_st,
            new_status=action.status,
            comments=req.comments or f"Acknowledged by {req.actor_name} ({req.actor_role})",
            timestamp=curr
        )
        db.add(history)
        db.commit()
        db.refresh(action)
        return action

    @classmethod
    def get_action_countdown(
        cls,
        db: Session,
        action_id: str,
        now: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Calculates live SLA countdown and state for a single safety action."""
        action = db.scalar(select(SafetyAction).where(SafetyAction.id == action_id))
        if not action:
            raise ValueError(f"Safety action '{action_id}' not found.")

        policy = cls.get_policy(db, action.severity)
        return SLAEngine.compute_countdown(action=action, policy=policy, now=now)

    @classmethod
    def get_sla_dashboard(cls, db: Session, now: Optional[datetime] = None) -> SLADashboardResponse:
        """Aggregates platform-wide SLA tracking metrics and active action countdowns."""
        curr = now or datetime.utcnow()
        policies_list = cls.get_or_create_policies(db)
        policy_map = {p.severity.upper(): p for p in policies_list}

        actions = list(db.scalars(
            select(SafetyAction).order_by(desc(SafetyAction.created_at))
        ).all())

        crit_open = 0
        awaiting_ack = 0
        approaching_sla = 0
        sla_breached = 0
        escalated = 0
        contained = 0
        awaiting_verif = 0
        closed = 0

        action_items = []

        for act in actions:
            pol = policy_map.get(act.severity.upper())
            cd = SLAEngine.compute_countdown(action=act, policy=pol, now=curr)

            # Update in-memory / persisted state
            state = cd["sla_state"]

            if act.severity == "CRITICAL" and act.status not in ["CLOSED", "VERIFIED", "REJECTED"]:
                crit_open += 1
            if not act.acknowledged_at and act.status not in ["CLOSED", "VERIFIED", "REJECTED"]:
                awaiting_ack += 1
            if state == "APPROACHING_DEADLINE":
                approaching_sla += 1
            elif state == "BREACHED":
                sla_breached += 1
            elif state == "ESCALATED" or act.escalation_level > 0:
                escalated += 1
            elif state == "CONTAINED":
                contained += 1
            elif act.status == "AWAITING_VERIFICATION":
                awaiting_verif += 1
            elif act.status in ["CLOSED", "VERIFIED"]:
                closed += 1

            if act.status not in ["CLOSED", "VERIFIED", "REJECTED"]:
                action_items.append(
                    SLAActionItemResponse(
                        action_id=act.id,
                        report_id=act.report_id,
                        severity=act.severity,
                        title=act.title,
                        status=act.status,
                        sla_state=state,
                        assigned_role=act.assigned_role,
                        assigned_user=act.assigned_user,
                        sla_deadline=cd["sla_deadline"],
                        time_remaining_seconds=cd["time_remaining_seconds"],
                        formatted_countdown=cd["formatted_countdown"],
                        escalation_level=act.escalation_level,
                        created_at=act.created_at,
                        acknowledged_at=act.acknowledged_at
                    )
                )

        return SLADashboardResponse(
            critical_open=crit_open,
            awaiting_acknowledgement=awaiting_ack,
            approaching_sla=approaching_sla,
            sla_breached=sla_breached,
            escalated=escalated,
            contained=contained,
            awaiting_verification=awaiting_verif,
            closed=closed,
            total_active_actions=len(action_items),
            active_actions=action_items
        )

    @classmethod
    def evaluate_and_escalate_actions(
        cls,
        db: Session,
        now: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Evaluates all active actions for SLA breaches and executes idempotent multi-level escalations.
        """
        curr = now or datetime.utcnow()
        policies = cls.get_or_create_policies(db)
        policy_map = {p.severity.upper(): p for p in policies}

        active_actions = list(db.scalars(
            select(SafetyAction).where(
                SafetyAction.status.notin_(["CLOSED", "VERIFIED", "REJECTED"])
            )
        ).all())

        escalated_count = 0
        reminded_count = 0
        evaluated_count = len(active_actions)

        for act in active_actions:
            pol = policy_map.get(act.severity.upper())
            cd = SLAEngine.compute_countdown(action=act, policy=pol, now=curr)
            act.sla_state = cd["sla_state"]

            # If unacknowledged, check for escalation
            if not act.acknowledged_at:
                target_level, target_role, reason = SLAEngine.evaluate_escalation_tier(
                    action=act, policy=pol, now=curr
                )

                if target_level > act.escalation_level and target_role:
                    # Idempotency Check: Verify if an escalation log for this exact level already exists
                    existing_esc = db.scalar(
                        select(EscalationLog).where(
                            and_(
                                EscalationLog.action_id == act.id,
                                EscalationLog.escalation_level == target_level
                            )
                        )
                    )

                    if not existing_esc:
                        old_level = act.escalation_level
                        act.escalation_level = target_level
                        act.assigned_role = target_role
                        act.status = "ESCALATED"
                        act.sla_state = "ESCALATED"
                        act.updated_at = curr

                        # Log notification in email_logs
                        email_id = str(uuid.uuid4())
                        email_log = EmailLog(
                            id=email_id,
                            report_id=act.report_id,
                            recipient_email=f"{target_role.lower().replace(' ', '.').replace('/', '.')}@refinery.oil.in",
                            recipient_name=target_role,
                            recipient_role=target_role,
                            escalation_tier=f"LEVEL_{target_level}",
                            subject=f" ESCALATION LEVEL {target_level} — SLA BREACH — {act.severity} SIF ACTION REQUIRED [{act.report_id}]",
                            body_html=f"<p>Action {act.id} has breached SLA. Escalated to {target_role}. Reason: {reason}</p>",
                            status="SENT",
                            triggered_by=f"Automated SLA Escalation Engine (Level {target_level})",
                            sent_at=curr
                        )
                        db.add(email_log)

                        # Create EscalationLog
                        esc_log = EscalationLog(
                            id=str(uuid.uuid4()),
                            action_id=act.id,
                            escalation_level=target_level,
                            previous_level=old_level,
                            recipient_role=target_role,
                            recipient_email=email_log.recipient_email,
                            reason=reason or f"SLA Breach Escalation Level {target_level}",
                            notification_id=email_id,
                            escalated_at=curr
                        )
                        db.add(esc_log)

                        # Audit History
                        history = ActionHistory(
                            id=str(uuid.uuid4()),
                            report_id=act.report_id,
                            actor_name="SLA Escalation Engine",
                            actor_role="Automated System",
                            action_type=f"ESCALATION_LEVEL_{target_level}",
                            old_status="DISPATCHED" if old_level == 0 else "ESCALATED",
                            new_status="ESCALATED",
                            comments=f"Escalated to Level {target_level} ({target_role}). Reason: {reason}",
                            timestamp=curr
                        )
                        db.add(history)
                        escalated_count += 1

        db.commit()

        return {
            "evaluated_count": evaluated_count,
            "escalated_count": escalated_count,
            "timestamp": curr.isoformat()
        }
