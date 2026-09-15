from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_, and_, desc, asc

from app.models.safety_report import SafetyReport
from app.models.dataset import Dataset
from app.schemas.report import SafetyReportCreate, SafetyReportUpdate
from app.utils.risk_classifier import normalize_risk_level


class ReportService:
    @staticmethod
    def create_report(db: Session, report_data: SafetyReportCreate) -> SafetyReport:
        desc_text = (report_data.description or "").strip()
        if not desc_text or len(desc_text) < 8:
            raise ValueError("Please describe what you observed, including the activity, hazard, exposure, or missing control.")

        vague_terms = {"unsafe", "problem", "issue", "bad", "danger", "incident", "hazard"}
        if desc_text.lower() in vague_terms or (len(desc_text.split()) == 1 and desc_text.lower() in vague_terms):
            raise ValueError("Please describe what you observed, including the activity, hazard, exposure, or missing control.")

        dataset_id = report_data.dataset_id
        if not dataset_id:
            first_ds = db.scalar(select(Dataset).where(Dataset.is_active == True))
            if first_ds:
                dataset_id = first_ds.id
            else:
                new_ds = Dataset(
                    dataset_name="Direct Supervisor Submissions",
                    original_filename="supervisor_submissions.csv",
                    file_type="direct_submission",
                    status="ready",
                    description="Central dataset for direct supervisor observations"
                )
                db.add(new_ds)
                db.flush()
                dataset_id = new_ds.id

        count_existing = db.scalar(select(func.count(SafetyReport.id))) or 0
        year_str = datetime.utcnow().strftime("%Y")
        generated_id = f"OIL-{year_str}-{(count_existing + 1):06d}"

        report_dt = report_data.report_date or datetime.utcnow()

        raw_data = {
            "Observation": desc_text,
            "ReportType": report_data.report_type or "Unsafe Act",
            "SubmittedBy": report_data.submitting_user or "Supervisor",
            "SubmittedRole": report_data.submitting_role or "Supervisor",
            "SubmissionTime": report_dt.isoformat(),
            "SiteLocation": report_data.location,
            "RefineryUnit": report_data.refinery_unit,
            "Equipment": report_data.equipment,
            "WorkType": report_data.work_type,
            "Department": report_data.department,
            "ImmediateCause": report_data.immediate_cause,
            "PotentialConsequence": report_data.potential_consequence,
            "CorrectiveAction": report_data.corrective_action,
        }

        calculated_risk = normalize_risk_level(report_data.risk_level, fallback_item=raw_data)
        raw_data["Risk_Level"] = calculated_risk

        report = SafetyReport(
            dataset_id=dataset_id,
            original_id=generated_id,
            raw_data=raw_data,
            report_date=report_dt,
            location=report_data.location,
            refinery_unit=report_data.refinery_unit,
            equipment=report_data.equipment,
            work_type=report_data.work_type,
            department=report_data.department,
            report_type=report_data.report_type or "Unsafe Act",
            description=desc_text,
            hazard=report_data.hazard,
            unsafe_act=report_data.unsafe_act,
            unsafe_condition=report_data.unsafe_condition,
            ppe_issue=report_data.ppe_issue,
            supervisor_factor=report_data.supervisor_factor,
            maintenance_factor=report_data.maintenance_factor,
            repeated_issue=report_data.repeated_issue,
            immediate_cause=report_data.immediate_cause,
            potential_consequence=report_data.potential_consequence,
            risk_level=calculated_risk,
            corrective_action=report_data.corrective_action,
            action_status="Open" if report_data.corrective_action else None,
            assigned_to=report_data.assigned_to,
            assigned_department=report_data.assigned_department or report_data.department,
            due_date=report_data.due_date,
            submitting_user=report_data.submitting_user or "Supervisor",
            submitting_role=report_data.submitting_role or "Supervisor",
            source_dataset="Direct Supervisor Input",
            analysis_status="IN_PROGRESS",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(report)
        db.commit()
        db.refresh(report)

        try:
            from app.models.system_audit_log import SystemAuditLog
            audit = SystemAuditLog(
                actor_user=report.submitting_user or "Supervisor",
                actor_role=report.submitting_role or "Supervisor",
                action_category="REPORT_SUBMISSION",
                event_name="Safety Report Created",
                resource_type="SafetyReport",
                resource_id=report.id,
                details={"original_id": report.original_id, "refinery_unit": report.refinery_unit}
            )
            db.add(audit)
            db.commit()
        except Exception:
            pass

        try:
            from app.services.sif_service import SIFService
            analysis = SIFService.analyze_report(db=db, report_id=report.id)
            report.analysis_status = "COMPLETED" if analysis else "COMPLETED"
            db.commit()
            db.refresh(report)
        except Exception:
            report.analysis_status = "FAILED"
            db.commit()
            db.refresh(report)

        return report

    @staticmethod
    def update_report(db: Session, report_id: str, update_data: SafetyReportUpdate) -> Optional[SafetyReport]:
        report = db.scalar(select(SafetyReport).where(SafetyReport.id == report_id))
        if not report:
            return None

        data_dict = update_data.model_dump(exclude_unset=True)
        for key, value in data_dict.items():
            if hasattr(report, key) and value is not None:
                setattr(report, key, value)

        report.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(report)

        try:
            from app.models.system_audit_log import SystemAuditLog
            audit = SystemAuditLog(
                actor_user=report.submitting_user or "Supervisor",
                actor_role=report.submitting_role or "Supervisor",
                action_category="REPORT_MODIFICATION",
                event_name="Safety Report Updated",
                resource_type="SafetyReport",
                resource_id=report.id,
                details={"updated_fields": list(data_dict.keys())}
            )
            db.add(audit)
            db.commit()
        except Exception:
            pass

        return report

    @staticmethod
    def get_reports(
        db: Session,
        dataset_id: Optional[str] = None,
        refinery_unit: Optional[str] = None,
        equipment: Optional[str] = None,
        work_type: Optional[str] = None,
        department: Optional[str] = None,
        risk_level: Optional[str] = None,
        action_status: Optional[str] = None,
        immediate_cause: Optional[str] = None,
        potential_consequence: Optional[str] = None,
        high_potential: Optional[bool] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        search: Optional[str] = None,
        sort_by: str = "report_date",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[SafetyReport], int]:
        query = select(SafetyReport)

        # Filters
        if dataset_id:
            query = query.where(SafetyReport.dataset_id == dataset_id)
        if refinery_unit:
            query = query.where(func.lower(SafetyReport.refinery_unit) == refinery_unit.lower())
        if equipment:
            query = query.where(func.lower(SafetyReport.equipment) == equipment.lower())
        if work_type:
            query = query.where(func.lower(SafetyReport.work_type) == work_type.lower())
        if department:
            query = query.where(func.lower(SafetyReport.department) == department.lower())
        if risk_level:
            query = query.where(func.lower(SafetyReport.risk_level) == risk_level.lower())
        if action_status:
            query = query.where(func.lower(SafetyReport.action_status) == action_status.lower())
        if immediate_cause:
            query = query.where(func.lower(SafetyReport.immediate_cause) == immediate_cause.lower())
        if potential_consequence:
            query = query.where(func.lower(SafetyReport.potential_consequence) == potential_consequence.lower())
        if high_potential is not None:
            query = query.where(SafetyReport.high_potential == high_potential)
        if date_from:
            query = query.where(SafetyReport.report_date >= date_from)
        if date_to:
            query = query.where(SafetyReport.report_date <= date_to)

        # Full-text / substring search across multiple narrative & descriptor fields
        if search:
            search_pattern = f"%{search.strip().lower()}%"
            query = query.where(
                or_(
                    func.lower(SafetyReport.description).like(search_pattern),
                    func.lower(SafetyReport.original_id).like(search_pattern),
                    func.lower(SafetyReport.immediate_cause).like(search_pattern),
                    func.lower(SafetyReport.potential_consequence).like(search_pattern),
                    func.lower(SafetyReport.corrective_action).like(search_pattern),
                    func.lower(SafetyReport.refinery_unit).like(search_pattern),
                    func.lower(SafetyReport.department).like(search_pattern)
                )
            )

        # Total count before pagination
        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0

        # Sorting
        sort_col = getattr(SafetyReport, sort_by, SafetyReport.report_date)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_col).nulls_last())
        else:
            query = query.order_by(desc(sort_col).nulls_last())

        # Pagination
        offset = (page - 1) * page_size
        items = list(db.scalars(query.offset(offset).limit(page_size)).all())

        return items, total

    @staticmethod
    def get_report_by_id(db: Session, report_id: str) -> Optional[SafetyReport]:
        return db.scalar(select(SafetyReport).where(SafetyReport.id == report_id))

    @staticmethod
    def get_report_counts(db: Session, dataset_id: Optional[str] = None) -> Dict[str, Any]:
        base_query = select(SafetyReport)
        if dataset_id:
            base_query = base_query.where(SafetyReport.dataset_id == dataset_id)

        all_reports = list(db.scalars(base_query).all())
        total_reports = len(all_reports)

        high_cnt = 0
        med_cnt = 0
        low_cnt = 0

        for r in all_reports:
            norm = normalize_risk_level(r.risk_level, fallback_item=r.raw_data)
            if norm == "HIGH":
                high_cnt += 1
            elif norm == "LOW":
                low_cnt += 1
            else:
                med_cnt += 1

        by_risk_level = {
            "HIGH": high_cnt,
            "MEDIUM": med_cnt,
            "LOW": low_cnt,
            "High": high_cnt,
            "Medium": med_cnt,
            "Low": low_cnt
        }

        print(f"[OIL_SIF RISK SUMMARY] Total observations: {total_reports} | High: {high_cnt} | Medium: {med_cnt} | Low: {low_cnt}")

        def get_group_counts(column):
            q = select(column, func.count(SafetyReport.id)).where(column != None)
            if dataset_id:
                q = q.where(SafetyReport.dataset_id == dataset_id)
            q = q.group_by(column)
            results = db.execute(q).all()
            return {str(val): count for val, count in results}

        by_department = get_group_counts(SafetyReport.department)
        by_refinery_unit = get_group_counts(SafetyReport.refinery_unit)
        by_action_status = get_group_counts(SafetyReport.action_status)
        by_work_type = get_group_counts(SafetyReport.work_type)

        return {
            "total_reports": total_reports,
            "by_risk_level": by_risk_level,
            "by_department": by_department,
            "by_refinery_unit": by_refinery_unit,
            "by_action_status": by_action_status,
            "by_work_type": by_work_type
        }
