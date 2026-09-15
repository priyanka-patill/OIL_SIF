import uuid
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc, and_

from app.models.safety_hold import SafetyHold
from app.models.safety_action import SafetyAction
from app.models.safety_report import SafetyReport
from app.models.action_history import ActionHistory
from app.schemas.safety_hold import (
    SafetyHoldCreateRequest,
    SafetyHoldReviewRequest,
    SafetyHoldReassessRequest,
    SafetyHoldReleaseRequest,
    SafetyHoldVerifyReleaseRequest
)


class SafetyHoldService:
    """
    Service managing the application-level Digital Safety Hold workflow:
    NORMAL -> SAFETY_HOLD_REQUESTED -> SAFETY_OFFICER_REVIEW -> HOLD_APPROVED -> WORKFLOW_BLOCKED -> REASSESSMENT -> RELEASE_REQUESTED -> VERIFIED -> RELEASED.
    """

    @classmethod
    def request_safety_hold(cls, db: Session, req: SafetyHoldCreateRequest) -> SafetyHold:
        """Creates an application-level safety hold request."""
        # Extract permit/JSA if report_id provided and not in req
        permit_id = req.permit_id
        jsa_id = req.jsa_id
        unit = req.refinery_unit
        equipment = req.equipment

        if req.report_id:
            rep = db.scalar(select(SafetyReport).where(SafetyReport.id == req.report_id))
            if rep:
                unit = unit or rep.refinery_unit
                equipment = equipment or rep.equipment
                if not permit_id and isinstance(rep.raw_data, dict):
                    permit_id = rep.raw_data.get("permit_id") or rep.raw_data.get("permit_number")
                if not jsa_id and isinstance(rep.raw_data, dict):
                    jsa_id = rep.raw_data.get("jsa_id") or rep.raw_data.get("jsa_number")

        hold = SafetyHold(
            id=str(uuid.uuid4()),
            report_id=req.report_id,
            action_id=req.action_id,
            permit_id=permit_id,
            jsa_id=jsa_id,
            refinery_unit=unit,
            equipment=equipment,
            trigger=req.trigger,
            reason=req.reason,
            bdi=req.bdi,
            sif_status=req.sif_status,
            status="SAFETY_HOLD_REQUESTED",
            requested_by=req.requested_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(hold)

        # Update associated SafetyAction if linked
        if req.action_id:
            act = db.scalar(select(SafetyAction).where(SafetyAction.id == req.action_id))
            if act:
                act.status = "CONTAINED"
                act.containment_started_at = datetime.utcnow()

        db.commit()
        db.refresh(hold)

        # Audit History
        history = ActionHistory(
            id=str(uuid.uuid4()),
            report_id=req.report_id or (req.action_id or "HOLD-EVENT"),
            actor_name=req.requested_by,
            actor_role="Safety Requester",
            action_type="SAFETY_HOLD_REQUESTED",
            old_status="NORMAL",
            new_status="SAFETY_HOLD_REQUESTED",
            comments=f"Safety hold requested: {req.reason} (Trigger: {req.trigger})",
            timestamp=datetime.utcnow()
        )
        db.add(history)
        db.commit()

        return hold

    @classmethod
    def get_safety_holds(
        cls,
        db: Session,
        status: Optional[str] = None,
        refinery_unit: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[SafetyHold], int]:
        """Retrieves paginated safety holds with optional filters."""
        query = select(SafetyHold)
        if status:
            query = query.where(SafetyHold.status.ilike(f"%{status.strip()}%"))
        if refinery_unit:
            query = query.where(SafetyHold.refinery_unit.ilike(f"%{refinery_unit.strip()}%"))

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(db.scalars(
            query.order_by(desc(SafetyHold.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all())

        return items, total

    @classmethod
    def get_safety_hold_by_id(cls, db: Session, hold_id: str) -> Optional[SafetyHold]:
        """Retrieves a single safety hold by UUID."""
        return db.scalar(select(SafetyHold).where(SafetyHold.id == hold_id))

    @classmethod
    def review_safety_hold(cls, db: Session, hold_id: str, req: SafetyHoldReviewRequest) -> SafetyHold:
        """Reviews and approves/rejects safety hold, freezing digital workflow if approved."""
        hold = cls.get_safety_hold_by_id(db, hold_id)
        if not hold:
            raise ValueError(f"Safety hold '{hold_id}' not found.")

        dec = req.decision.upper().strip()
        old_st = hold.status

        if dec in ["APPROVE", "APPROVED"]:
            hold.status = "WORKFLOW_BLOCKED"
            hold.approved_by = req.reviewer_name
            hold.approved_at = datetime.utcnow()
            hold.reviewed_by = req.reviewer_name
        else:
            hold.status = "NORMAL"
            hold.reviewed_by = req.reviewer_name

        hold.updated_at = datetime.utcnow()

        history = ActionHistory(
            id=str(uuid.uuid4()),
            report_id=hold.report_id or hold.id,
            actor_name=req.reviewer_name,
            actor_role=req.reviewer_role,
            action_type="HOLD_REVIEWED",
            old_status=old_st,
            new_status=hold.status,
            comments=req.comments or f"Safety hold review decision: {dec}",
            timestamp=datetime.utcnow()
        )
        db.add(history)
        db.commit()
        db.refresh(hold)

        return hold

    @classmethod
    def reassess_safety_hold(cls, db: Session, hold_id: str, req: SafetyHoldReassessRequest) -> SafetyHold:
        """Transitions safety hold into active reassessment phase."""
        hold = cls.get_safety_hold_by_id(db, hold_id)
        if not hold:
            raise ValueError(f"Safety hold '{hold_id}' not found.")

        old_st = hold.status
        hold.status = "REASSESSMENT"
        hold.verification_notes = req.reassessment_notes
        hold.updated_at = datetime.utcnow()

        history = ActionHistory(
            id=str(uuid.uuid4()),
            report_id=hold.report_id or hold.id,
            actor_name=req.actor_name,
            actor_role=req.actor_role,
            action_type="HOLD_REASSESSMENT",
            old_status=old_st,
            new_status="REASSESSMENT",
            comments=req.reassessment_notes,
            timestamp=datetime.utcnow()
        )
        db.add(history)
        db.commit()
        db.refresh(hold)

        return hold

    @classmethod
    def request_release(cls, db: Session, hold_id: str, req: SafetyHoldReleaseRequest) -> SafetyHold:
        """Submits request to release safety hold with remediation justification."""
        hold = cls.get_safety_hold_by_id(db, hold_id)
        if not hold:
            raise ValueError(f"Safety hold '{hold_id}' not found.")

        old_st = hold.status
        hold.status = "RELEASE_REQUESTED"
        hold.released_by = req.requester_name
        hold.updated_at = datetime.utcnow()

        history = ActionHistory(
            id=str(uuid.uuid4()),
            report_id=hold.report_id or hold.id,
            actor_name=req.requester_name,
            actor_role=req.requester_role,
            action_type="HOLD_RELEASE_REQUESTED",
            old_status=old_st,
            new_status="RELEASE_REQUESTED",
            comments=req.justification,
            timestamp=datetime.utcnow()
        )
        db.add(history)
        db.commit()
        db.refresh(hold)

        return hold

    @classmethod
    def verify_and_release(cls, db: Session, hold_id: str, req: SafetyHoldVerifyReleaseRequest) -> SafetyHold:
        """Conducts physical walkdown verification and unblocks the safety hold workflow."""
        hold = cls.get_safety_hold_by_id(db, hold_id)
        if not hold:
            raise ValueError(f"Safety hold '{hold_id}' not found.")

        old_st = hold.status
        hold.status = "RELEASED"
        hold.verified_by = req.verifier_name
        hold.verification_notes = f"Verified: {req.walkdown_notes}. Permit re-authorized: {req.permit_reauthorized}"
        hold.released_at = datetime.utcnow()
        hold.updated_at = datetime.utcnow()

        # Update linked action if any
        if hold.action_id:
            act = db.scalar(select(SafetyAction).where(SafetyAction.id == hold.action_id))
            if act:
                act.status = "VERIFIED"
                act.verified_at = datetime.utcnow()
                act.verified_by = req.verifier_name

        history = ActionHistory(
            id=str(uuid.uuid4()),
            report_id=hold.report_id or hold.id,
            actor_name=req.verifier_name,
            actor_role=req.verifier_role,
            action_type="HOLD_VERIFIED_RELEASED",
            old_status=old_st,
            new_status="RELEASED",
            comments=hold.verification_notes,
            timestamp=datetime.utcnow()
        )
        db.add(history)
        db.commit()
        db.refresh(hold)

        return hold
