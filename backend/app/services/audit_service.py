import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc

from app.models.system_audit_log import SystemAuditLog
from app.schemas.audit_trail import (
    SystemAuditLogCreate,
    AuditTimelineEvent,
    AuditTimelineResponse,
    AuditStatsResponse
)


class AuditService:
    """
    Service for writing and reading immutable platform audit logs.
    Captures complete lifecycle transitions from detection through closure & human feedback.
    """

    EVENT_TITLES = {
        "DETECTION": "Safety Observation Ingested / Detected",
        "CORRELATION": "Multi-Factor Correlation Evaluated",
        "BARRIER_ASSESSMENT": "Swiss Cheese Barrier Defense Evaluated",
        "BDI_CALCULATION": "Barrier Degradation Index Calculated",
        "SIF_ESCALATION": "SIF Precursor Escalation Analyzed",
        "ACTION_CREATION": "Safety Action Response Package Generated",
        "APPROVAL": "Action Review & Approval Status Updated",
        "NOTIFICATION": "Context-Aware Notification Dispatched",
        "SAFETY_HOLD": "Digital Safety Hold Requested / Updated",
        "SLA_REMINDER": "SLA Progress Reminder Notification Sent",
        "SLA_WARNING": "SLA Approaching Deadline Warning Triggered",
        "SLA_BREACH": "SLA Window Breached",
        "ESCALATION": "Multi-Tier Supervisor Escalation Triggered",
        "ACKNOWLEDGEMENT": "Action Responsibility Acknowledged",
        "CONTAINMENT": "Immediate Field Containment Completed",
        "VERIFICATION": "Physical Walkdown Verification Logged",
        "CLOSURE": "Safety Action Item Formally Closed",
        "HUMAN_FEEDBACK": "Human Expert Feedback Submitted",
        "ADMIN_CONFIG_UPDATE": "Platform Governance Settings Updated",
        "DEMO_SIMULATION": "Simulation Scenario Executed"
    }

    @classmethod
    def log_event(
        cls,
        db: Session,
        event_type: str,
        trigger: str,
        report_id: Optional[str] = None,
        dataset_id: Optional[str] = None,
        action_id: Optional[str] = None,
        hold_id: Optional[str] = None,
        evidence: Optional[Dict[str, Any]] = None,
        bdi: Optional[float] = None,
        sif_status: Optional[str] = None,
        severity: Optional[str] = None,
        recommended_action: Optional[str] = None,
        human_decision: Optional[str] = None,
        notification_status: Optional[str] = None,
        escalation_level: Optional[int] = None,
        final_resolution: Optional[str] = None,
        actor: str = "AI Safety Engine",
        is_simulated: bool = False,
        client_host: Optional[str] = None
    ) -> SystemAuditLog:
        """
        Appends an immutable audit event record into system_audit_logs.
        """
        audit_entry = SystemAuditLog(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            report_id=str(report_id) if report_id else None,
            dataset_id=str(dataset_id) if dataset_id else None,
            action_id=str(action_id) if action_id else None,
            hold_id=str(hold_id) if hold_id else None,
            event_type=event_type,
            engine_version="2.0.0-phase8",
            trigger=trigger,
            evidence=evidence or {},
            bdi=bdi,
            sif_status=sif_status,
            severity=severity,
            recommended_action=recommended_action,
            human_decision=human_decision,
            notification_status=notification_status,
            escalation_level=escalation_level,
            final_resolution=final_resolution,
            actor=actor,
            is_simulated=is_simulated,
            client_host=client_host
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        return audit_entry

    @classmethod
    def log_action(
        cls,
        db: Session,
        action_type: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        client_host: Optional[str] = None,
        actor: Optional[str] = None
    ) -> SystemAuditLog:
        """Backward-compatible audit action logger."""
        return cls.log_event(
            db=db,
            event_type="DETECTION" if action_type == "DATASET_INGESTION_COMPLETED" else action_type,
            trigger=f"Action: {action_type} on {entity_type or 'Entity'} ({entity_id or 'N/A'})",
            dataset_id=entity_id if entity_type == "DATASET" else None,
            report_id=entity_id if entity_type == "REPORT" else None,
            action_id=entity_id if entity_type == "ACTION" else None,
            evidence=details,
            actor=actor or "System Ingestion Worker",
            client_host=client_host
        )

    @classmethod
    def get_timeline_for_report(cls, db: Session, report_id: str) -> AuditTimelineResponse:
        """
        Retrieves complete chronological timeline of all events associated with a report or its actions/holds.
        """
        stmt = (
            select(SystemAuditLog)
            .where(SystemAuditLog.report_id == str(report_id))
            .order_by(SystemAuditLog.timestamp.asc())
        )
        logs = list(db.scalars(stmt).all())

        timeline_events: List[AuditTimelineEvent] = []
        for l in logs:
            title = cls.EVENT_TITLES.get(l.event_type, l.event_type.replace("_", " ").title())
            desc_text = l.trigger
            if l.bdi is not None:
                desc_text += f" • BDI: {l.bdi:.1f}"
            if l.sif_status:
                desc_text += f" • SIF: {l.sif_status}"
            if l.human_decision:
                desc_text += f" • Decision: {l.human_decision}"

            timeline_events.append(
                AuditTimelineEvent(
                    event_id=l.event_id,
                    timestamp=l.timestamp,
                    formatted_time=l.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    event_type=l.event_type,
                    title=title,
                    description=desc_text,
                    actor=l.actor,
                    severity=l.severity,
                    bdi=l.bdi,
                    sif_status=l.sif_status,
                    is_simulated=l.is_simulated,
                    evidence=l.evidence
                )
            )

        first_at = logs[0].timestamp if logs else None
        last_at = logs[-1].timestamp if logs else None

        return AuditTimelineResponse(
            report_id=str(report_id),
            total_events=len(timeline_events),
            events=timeline_events,
            first_event_at=first_at,
            last_event_at=last_at
        )

    @classmethod
    def get_timeline_for_action(cls, db: Session, action_id: str) -> AuditTimelineResponse:
        """
        Retrieves chronological timeline for a specific action lifecycle.
        """
        stmt = (
            select(SystemAuditLog)
            .where(SystemAuditLog.action_id == str(action_id))
            .order_by(SystemAuditLog.timestamp.asc())
        )
        logs = list(db.scalars(stmt).all())

        timeline_events: List[AuditTimelineEvent] = []
        for l in logs:
            title = cls.EVENT_TITLES.get(l.event_type, l.event_type.replace("_", " ").title())
            timeline_events.append(
                AuditTimelineEvent(
                    event_id=l.event_id,
                    timestamp=l.timestamp,
                    formatted_time=l.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    event_type=l.event_type,
                    title=title,
                    description=l.trigger,
                    actor=l.actor,
                    severity=l.severity,
                    bdi=l.bdi,
                    sif_status=l.sif_status,
                    is_simulated=l.is_simulated,
                    evidence=l.evidence
                )
            )

        first_at = logs[0].timestamp if logs else None
        last_at = logs[-1].timestamp if logs else None

        return AuditTimelineResponse(
            report_id=logs[0].report_id if logs else None,
            total_events=len(timeline_events),
            events=timeline_events,
            first_event_at=first_at,
            last_event_at=last_at
        )

    @classmethod
    def get_audit_stats(cls, db: Session) -> AuditStatsResponse:
        """
        Computes summary statistics for governance dashboards.
        """
        total = db.scalar(select(func.count(SystemAuditLog.event_id))) or 0
        simulated = db.scalar(select(func.count(SystemAuditLog.event_id)).where(SystemAuditLog.is_simulated == True)) or 0
        real = total - simulated

        # Types breakdown
        type_rows = db.execute(
            select(SystemAuditLog.event_type, func.count(SystemAuditLog.event_id))
            .group_by(SystemAuditLog.event_type)
        ).all()
        types_map = {row[0]: row[1] for row in type_rows}

        # Actors breakdown
        actor_rows = db.execute(
            select(SystemAuditLog.actor, func.count(SystemAuditLog.event_id))
            .group_by(SystemAuditLog.actor)
        ).all()
        actors_map = {row[0]: row[1] for row in actor_rows}

        last_ts = db.scalar(select(func.max(SystemAuditLog.timestamp)))

        return AuditStatsResponse(
            total_events=total,
            real_events=real,
            simulated_events=simulated,
            event_types_breakdown=types_map,
            actors_breakdown=actors_map,
            last_event_timestamp=last_ts
        )
