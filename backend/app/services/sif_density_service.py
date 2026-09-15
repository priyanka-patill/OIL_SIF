from typing import List, Dict, Any, Optional
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.safety_report import SafetyReport
from app.models.report_analysis import ReportAnalysis
from app.services.sif_service import SIFService


class SIFDensityService:
    """
    SIF Precursor Density & Dimension Analytics Service.
    Calculates SIF Precursor Density = (SIF-potential reports / Total relevant reports)
    and computes dimension rankings across Refinery Unit, Activity, Department, Equipment,
    and IOGP Life-Saving Rules.
    """

    @classmethod
    def calculate_sif_density(
        cls,
        db: Session,
        dataset_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates SIF Precursor Density overall and across all available dimensions.
        """
        # Ensure analyses exist
        analyses = list(db.scalars(
            select(ReportAnalysis).where(ReportAnalysis.dataset_id == dataset_id) if dataset_id else select(ReportAnalysis)
        ).all())

        if not analyses:
            SIFService.batch_analyze_dataset(db, dataset_id)
            analyses = list(db.scalars(
                select(ReportAnalysis).where(ReportAnalysis.dataset_id == dataset_id) if dataset_id else select(ReportAnalysis)
            ).all())

        total_reports = len(analyses)
        if total_reports == 0:
            return {
                "total_reports": 0,
                "sif_precursor_count": 0,
                "sif_precursor_density_percentage": 0.0,
                "dimension_rankings": {},
                "unavailable_dimensions": [
                    "refinery_unit", "work_type", "department", "equipment", "iogp_rule", "location"
                ],
                "management_summary": "No safety reports available for SIF Precursor Density evaluation."
            }

        sif_count = sum(1 for a in analyses if a.sif_precursor == "YES")
        overall_density = round((sif_count / total_reports) * 100, 1)

        # Dimension grouping
        dimension_maps: Dict[str, Dict[str, List[ReportAnalysis]]] = {
            "refinery_unit": defaultdict(list),
            "work_type": defaultdict(list),
            "department": defaultdict(list),
            "equipment": defaultdict(list),
            "iogp_rule": defaultdict(list),
            "location": defaultdict(list)
        }

        for a in analyses:
            rep = a.report
            if rep and rep.refinery_unit:
                dimension_maps["refinery_unit"][rep.refinery_unit].append(a)
            if rep and rep.work_type:
                dimension_maps["work_type"][rep.work_type].append(a)
            if rep and rep.department:
                dimension_maps["department"][rep.department].append(a)
            if rep and rep.equipment:
                dimension_maps["equipment"][rep.equipment].append(a)
            if a.iogp_rule and a.iogp_rule != "No clear Life-Saving Rule match":
                dimension_maps["iogp_rule"][a.iogp_rule].append(a)
            if rep and rep.location:
                dimension_maps["location"][rep.location].append(a)

        dimension_rankings: Dict[str, List[Dict[str, Any]]] = {}
        unavailable_dimensions: List[str] = []

        dim_labels = {
            "refinery_unit": "Refinery Unit",
            "work_type": "Activity / Work Type",
            "department": "Department",
            "equipment": "Equipment",
            "iogp_rule": "IOGP Life-Saving Rule",
            "location": "Location / Site"
        }

        for dim_key, dim_label in dim_labels.items():
            dim_data = dimension_maps[dim_key]
            # Check if dimension has meaningful variance (more than 0 values and not all empty)
            if not dim_data or len(dim_data) == 0:
                unavailable_dimensions.append(dim_label)
                continue

            # Check if constant single value across all reports
            if len(dim_data) == 1 and list(dim_data.keys())[0].lower() in ["n/a", "unknown", "none", "unspecified"]:
                unavailable_dimensions.append(dim_label)
                continue

            ranked_items = []
            for name, a_list in dim_data.items():
                d_total = len(a_list)
                d_sif = sum(1 for a in a_list if a.sif_precursor == "YES")
                d_high_risk = sum(1 for a in a_list if a.ai_risk_level in ["HIGH", "CRITICAL"])
                d_density = round((d_sif / d_total) * 100, 1) if d_total > 0 else 0.0

                ranked_items.append({
                    "dimension": dim_label,
                    "name": name,
                    "total_reports": d_total,
                    "sif_precursor_count": d_sif,
                    "high_risk_count": d_high_risk,
                    "sif_density_percentage": d_density,
                    "sample_report_ids": [a.report.original_id or a.report_id for a in a_list[:3] if a.report]
                })

            # Sort by SIF density desc, then sif_precursor_count desc
            ranked_items.sort(key=lambda x: (-x["sif_density_percentage"], -x["sif_precursor_count"]))
            dimension_rankings[dim_label] = ranked_items

        top_unit = dimension_rankings.get("Refinery Unit", [{}])[0].get("name", "Process Units")
        top_rule = dimension_rankings.get("IOGP Life-Saving Rule", [{}])[0].get("name", "Safety Controls")

        summary = (
            f"Overall SIF Precursor Density is {overall_density}% ({sif_count} SIF precursor reports out of {total_reports} total). "
            f"Highest precursor density concentrated in '{top_unit}' and driven by '{top_rule}' violations."
        )

        return {
            "total_reports": total_reports,
            "sif_precursor_count": sif_count,
            "sif_precursor_density_percentage": overall_density,
            "dimension_rankings": dimension_rankings,
            "unavailable_dimensions": unavailable_dimensions,
            "management_summary": summary
        }
