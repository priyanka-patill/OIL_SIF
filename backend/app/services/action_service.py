from datetime import datetime, timezone
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_, and_, desc

from app.models.safety_report import SafetyReport
from app.models.action_history import ActionHistory
from app.models.audit_log import AuditLog
from app.schemas.action import ActionUpdateRequest, ActionItemResponse, ActionStatsResponse, ActionHistoryResponse


class ActionService:
    @staticmethod
    def get_actions(
        db: Session,
        dataset_id: Optional[str] = None,
        status: Optional[str] = None,
        department: Optional[str] = None,
        risk_level: Optional[str] = None,
        assigned_to: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[ActionItemResponse], int]:
        query = select(SafetyReport)

        if dataset_id:
            query = query.where(SafetyReport.dataset_id == dataset_id)

        if status:
            if status.lower() == "overdue":
                query = query.where(func.lower(SafetyReport.action_status) == "overdue")
            elif status.lower() == "open":
                query = query.where(
                    or_(
                        func.lower(SafetyReport.action_status) == "open",
                        SafetyReport.action_status == None
                    )
                )
            else:
                query = query.where(func.lower(SafetyReport.action_status) == status.lower())

        if department:
            query = query.where(
                or_(
                    func.lower(SafetyReport.department) == department.lower(),
                    func.lower(SafetyReport.assigned_department) == department.lower()
                )
            )

        if risk_level:
            query = query.where(func.lower(SafetyReport.risk_level) == risk_level.lower())

        if assigned_to:
            query = query.where(func.lower(SafetyReport.assigned_to).like(f"%{assigned_to.lower()}%"))

        if search:
            pattern = f"%{search.strip().lower()}%"
            query = query.where(
                or_(
                    func.lower(SafetyReport.original_id).like(pattern),
                    func.lower(SafetyReport.description).like(pattern),
                    func.lower(SafetyReport.corrective_action).like(pattern),
                    func.lower(SafetyReport.assigned_to).like(pattern),
                    func.lower(SafetyReport.refinery_unit).like(pattern)
                )
            )

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        offset = (page - 1) * page_size
        reports = list(db.scalars(query.offset(offset).limit(page_size)).all())

        now = datetime.now(timezone.utc)
        items: List[ActionItemResponse] = []

        for r in reports:
            # Check overdue condition
            is_overdue = False
            days_overdue = None
            if r.due_date:
                # Convert timezone if needed
                due = r.due_date if r.due_date.tzinfo else r.due_date.replace(tzinfo=timezone.utc)
                if (r.action_status or "").lower() != "closed" and due < now:
                    is_overdue = True
                    days_overdue = (now - due).days
            elif (r.action_status or "").lower() == "overdue":
                is_overdue = True

            hist_count = db.scalar(
                select(func.count(ActionHistory.id)).where(ActionHistory.report_id == r.id)
            ) or 0

            items.append(ActionItemResponse(
                report_id=r.id,
                original_id=r.original_id,
                problem=r.description,
                risk_level=r.risk_level,
                corrective_action=r.corrective_action,
                refinery_unit=r.refinery_unit,
                department=r.department,
                assigned_to=r.assigned_to,
                assigned_department=r.assigned_department or r.department,
                action_status=r.action_status or "Open",
                due_date=r.due_date,
                completion_date=r.completion_date,
                closure_verified_by=r.closure_verified_by,
                closure_verified_at=r.closure_verified_at,
                action_comments=r.action_comments,
                is_overdue=is_overdue,
                days_overdue=days_overdue,
                history_count=hist_count
            ))

        return items, total

    @staticmethod
    def get_action_stats(db: Session, dataset_id: Optional[str] = None) -> ActionStatsResponse:
        base_query = select(SafetyReport)
        if dataset_id:
            base_query = base_query.where(SafetyReport.dataset_id == dataset_id)

        total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0
        
        q_open = select(func.count(SafetyReport.id)).where(
            or_(
                func.lower(SafetyReport.action_status) == "open",
                SafetyReport.action_status == None
            )
        )
        q_prog = select(func.count(SafetyReport.id)).where(func.lower(SafetyReport.action_status) == "in progress")
        q_closed = select(func.count(SafetyReport.id)).where(func.lower(SafetyReport.action_status) == "closed")
        q_overdue = select(func.count(SafetyReport.id)).where(func.lower(SafetyReport.action_status) == "overdue")
        q_unassigned = select(func.count(SafetyReport.id)).where(
            or_(
                SafetyReport.assigned_to == None,
                SafetyReport.assigned_to == ""
            )
        )

        if dataset_id:
            q_open = q_open.where(SafetyReport.dataset_id == dataset_id)
            q_prog = q_prog.where(SafetyReport.dataset_id == dataset_id)
            q_closed = q_closed.where(SafetyReport.dataset_id == dataset_id)
            q_overdue = q_overdue.where(SafetyReport.dataset_id == dataset_id)
            q_unassigned = q_unassigned.where(SafetyReport.dataset_id == dataset_id)

        return ActionStatsResponse(
            total_actions=total,
            open_count=db.scalar(q_open) or 0,
            in_progress_count=db.scalar(q_prog) or 0,
            closed_count=db.scalar(q_closed) or 0,
            overdue_count=db.scalar(q_overdue) or 0,
            unassigned_count=db.scalar(q_unassigned) or 0
        )

    @staticmethod
    def update_action(
        db: Session,
        report_id: str,
        req: ActionUpdateRequest
    ) -> ActionItemResponse:
        report = db.scalar(select(SafetyReport).where(SafetyReport.id == report_id))
        if not report:
            raise ValueError(f"Report {report_id} not found")

        old_status = report.action_status or "Open"
        new_status = req.action_status if req.action_status is not None else old_status

        action_type = "STATUS_CHANGED"
        if req.assigned_to is not None and req.assigned_to != report.assigned_to:
            action_type = "ASSIGNED"
        elif new_status.lower() == "closed" and old_status.lower() != "closed":
            action_type = "COMPLETED"
        elif req.closure_verified_by is not None:
            action_type = "VERIFIED"
        elif req.action_comments and not req.action_status:
            action_type = "COMMENT_ADDED"

        # Apply updates
        if req.action_status is not None:
            report.action_status = req.action_status
        if req.assigned_to is not None:
            report.assigned_to = req.assigned_to
        if req.assigned_department is not None:
            report.assigned_department = req.assigned_department
        if req.due_date is not None:
            report.due_date = req.due_date
        if req.completion_date is not None:
            report.completion_date = req.completion_date
        elif new_status.upper() in ["CLOSED", "COMPLETED", "VERIFIED"] and not report.completion_date:
            report.completion_date = datetime.now(timezone.utc)
        if req.closure_verified_by is not None:
            report.closure_verified_by = req.closure_verified_by
            report.closure_verified_at = req.closure_verified_at or datetime.now(timezone.utc)
        if req.action_comments is not None:
            report.action_comments = req.action_comments

        # Also sync to linked SafetyAction if present
        from app.models.safety_action import SafetyAction
        sec_action = db.scalar(select(SafetyAction).where(SafetyAction.report_id == report_id))
        if sec_action:
            if req.action_status:
                sec_action.status = req.action_status.upper()
            if req.assigned_to:
                sec_action.assigned_user = req.assigned_to
            if req.closure_verified_by:
                sec_action.verified_by = req.closure_verified_by
                sec_action.verified_at = req.closure_verified_at or datetime.now(timezone.utc)

        # Store evidence info in AuditLog / raw_data
        evidence_dict = {}
        if req.evidence_text: evidence_dict["evidence_text"] = req.evidence_text
        if req.evidence_photo_url: evidence_dict["evidence_photo_url"] = req.evidence_photo_url
        if req.evidence_document_url: evidence_dict["evidence_document_url"] = req.evidence_document_url

        # Add ActionHistory record
        history = ActionHistory(
            report_id=report.id,
            actor_name=req.actor_name,
            actor_role=req.actor_role,
            action_type=action_type,
            old_status=old_status,
            new_status=new_status,
            comments=req.action_comments or (f"Evidence submitted: {req.evidence_text}" if req.evidence_text else None),
            timestamp=datetime.now(timezone.utc)
        )
        db.add(history)

        # Add AuditLog record
        audit = AuditLog(
            action_type="ACTION_UPDATED",
            entity_type="REPORT_ACTION",
            entity_id=report.id,
            details={
                "report_original_id": report.original_id,
                "actor_name": req.actor_name,
                "actor_role": req.actor_role,
                "old_status": old_status,
                "new_status": new_status,
                "assigned_to": report.assigned_to,
                "assigned_department": report.assigned_department,
                "action_type": action_type,
                "comments": req.action_comments,
                "evidence": evidence_dict
            }
        )
        db.add(audit)

        db.commit()
        db.refresh(report)

        hist_count = db.scalar(
            select(func.count(ActionHistory.id)).where(ActionHistory.report_id == report.id)
        ) or 0

        return ActionItemResponse(
            report_id=report.id,
            original_id=report.original_id,
            problem=report.description,
            risk_level=report.risk_level,
            corrective_action=report.corrective_action,
            refinery_unit=report.refinery_unit,
            department=report.department,
            assigned_to=report.assigned_to,
            assigned_department=report.assigned_department,
            action_status=report.action_status or "Open",
            due_date=report.due_date,
            completion_date=report.completion_date,
            closure_verified_by=report.closure_verified_by,
            closure_verified_at=report.closure_verified_at,
            action_comments=report.action_comments,
            evidence_text=req.evidence_text,
            evidence_photo_url=req.evidence_photo_url,
            evidence_document_url=req.evidence_document_url,
            is_overdue=(report.action_status or "").lower() == "overdue",
            history_count=hist_count
        )

    @staticmethod
    def get_action_history(db: Session, report_id: str) -> List[ActionHistoryResponse]:
        records = list(db.scalars(
            select(ActionHistory)
            .where(ActionHistory.report_id == report_id)
            .order_by(desc(ActionHistory.timestamp))
        ).all())
        return [ActionHistoryResponse.model_validate(r) for r in records]
