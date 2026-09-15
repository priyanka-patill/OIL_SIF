from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.safety_report import SafetyReport


class RecurrenceEngine:
    """Identifies recurring safety issues, equipment hotspots, and repeated unit patterns."""

    @classmethod
    def analyze_dataset_recurrence(cls, db: Session, dataset_id: str) -> Dict[str, Any]:
        """Calculates recurrence frequencies across all reports in a dataset."""
        reports = list(db.scalars(
            select(SafetyReport).where(SafetyReport.dataset_id == dataset_id)
        ).all())

        equipment_counts = defaultdict(list)
        unit_counts = defaultdict(list)
        dept_counts = defaultdict(list)
        work_type_counts = defaultdict(list)

        for rep in reports:
            if rep.equipment:
                equipment_counts[rep.equipment].append(rep)
            if rep.refinery_unit:
                unit_counts[rep.refinery_unit].append(rep)
            if rep.department:
                dept_counts[rep.department].append(rep)
            if rep.work_type:
                work_type_counts[rep.work_type].append(rep)

        return {
            "equipment_map": equipment_counts,
            "unit_map": unit_counts,
            "dept_map": dept_counts,
            "work_type_map": work_type_counts,
            "total_reports": len(reports)
        }

    @classmethod
    def evaluate_report_recurrence(
        cls,
        report: SafetyReport,
        recurrence_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Evaluates recurrence for a single report.
        Returns: (is_recurring, recurrence_score, recurrence_details)
        """
        equip = report.equipment
        unit = report.refinery_unit
        dept = report.department
        wt = report.work_type
        prev_reports_val = report.previous_similar_reports or 0

        equip_occurrences = 1
        unit_occurrences = 1
        dept_occurrences = 1
        wt_occurrences = 1

        if recurrence_context:
            if equip and equip in recurrence_context.get("equipment_map", {}):
                equip_occurrences = len(recurrence_context["equipment_map"][equip])
            if unit and unit in recurrence_context.get("unit_map", {}):
                unit_occurrences = len(recurrence_context["unit_map"][unit])
            if dept and dept in recurrence_context.get("dept_map", {}):
                dept_occurrences = len(recurrence_context["dept_map"][dept])
            if wt and wt in recurrence_context.get("work_type_map", {}):
                wt_occurrences = len(recurrence_context["work_type_map"][wt])

        # A report is considered recurring if:
        # - Recorded previous similar reports > 0, OR
        # - The specific equipment has multiple near misses (occurrences > 1), OR
        # - The process unit has high near-miss concentration (> 5)
        is_recurring = (
            prev_reports_val > 0
            or equip_occurrences > 2
            or report.repeated_issue is True
        )

        # Recurrence Score between 0.0 and 1.0
        score = 0.0
        if prev_reports_val > 0:
            score += min(0.5, prev_reports_val * 0.25)
        if equip_occurrences > 1:
            score += min(0.3, equip_occurrences * 0.05)
        if unit_occurrences > 3:
            score += min(0.2, unit_occurrences * 0.02)
        if report.repeated_issue:
            score += 0.3

        recurrence_score = min(1.0, round(score, 2))

        recurrence_details = {
            "equipment_id": equip,
            "equipment_occurrences_in_dataset": equip_occurrences,
            "refinery_unit": unit,
            "unit_occurrences_in_dataset": unit_occurrences,
            "department": dept,
            "department_occurrences_in_dataset": dept_occurrences,
            "work_type": wt,
            "work_type_occurrences_in_dataset": wt_occurrences,
            "recorded_previous_similar_reports": prev_reports_val,
            "is_systemic_repeat": is_recurring
        }

        return is_recurring, recurrence_score, recurrence_details
