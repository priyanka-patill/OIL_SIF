from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
from datetime import datetime

from app.models.safety_report import SafetyReport
from app.schemas.barriers import BarrierAssessmentItem
from app.schemas.bdi import (
    BDIComponentContribution,
    BDIExplainability,
    IndependentMetrics,
    ReportBDIResponse
)


class BDIEngine:
    """
    Barrier Degradation Index (BDI) Calculation & Explainability Engine.
    Computes an analytical score (0-100) indicating defense layer erosion around safety exposures.
    Maintains strict independence from recorded risk, AI risk, and accident probability.
    """

    VERSION = "v3.0.0"

    # Default Configurable Weight Matrix (Transparent & Documented)
    DEFAULT_WEIGHTS: Dict[str, float] = {
        "failed_barrier_per_item": 20.0,
        "max_failed_barriers": 40.0,
        "degraded_barrier_per_item": 12.0,
        "max_degraded_barriers": 36.0,
        "multi_factor_2_points": 10.0,
        "multi_factor_3_points": 18.0,
        "multi_factor_4_points": 25.0,
        "repeated_issue_points": 15.0,
        "previous_similar_per_report": 5.0,
        "max_previous_similar": 15.0,
        "unresolved_action_open": 10.0,
        "unresolved_action_overdue": 15.0,
        "high_potential_points": 15.0,
        "cross_report_convergence_points": 10.0
    }

    # Default Configurable Classification Thresholds
    DEFAULT_THRESHOLDS: Dict[str, Tuple[float, float]] = {
        "MINIMAL": (0.0, 20.0),
        "LOW": (20.1, 40.0),
        "MODERATE": (40.1, 60.0),
        "HIGH": (60.1, 80.0),
        "SEVERE": (80.1, 100.0)
    }

    CLASSIFICATION_COLORS: Dict[str, str] = {
        "MINIMAL": "green",
        "LOW": "cyan",
        "MODERATE": "amber",
        "HIGH": "orange",
        "SEVERE": "red"
    }

    DOCUMENTATION: Dict[str, str] = {
        "failed_barrier": "Points added for complete loss or bypass of a defensive control layer.",
        "degraded_barrier": "Points added for partial compromise or deficiency in a defensive barrier.",
        "multi_factor": "Escalation points when multiple barrier failures occur simultaneously.",
        "repeated_issue": "Points added when institutional recurrence prevention fails.",
        "unresolved_action": "Points added when previous corrective remediation remains open or overdue.",
        "high_potential": "Points added when the event carries catastrophic potential consequence.",
        "cross_report_convergence": "Points added when separate reports converge around the same physical equipment."
    }

    @classmethod
    def get_active_config(cls) -> Dict[str, Any]:
        return {
            "weights": cls.DEFAULT_WEIGHTS.copy(),
            "thresholds": {k: [v[0], v[1]] for k, v in cls.DEFAULT_THRESHOLDS.items()},
            "version": cls.VERSION,
            "documentation": cls.DOCUMENTATION.copy()
        }

    @classmethod
    def classify_score(
        cls,
        score: float,
        thresholds: Optional[Dict[str, Tuple[float, float]]] = None
    ) -> Tuple[str, str]:
        t = thresholds or cls.DEFAULT_THRESHOLDS
        for label, (low, high) in t.items():
            if low <= score <= high:
                return label, cls.CLASSIFICATION_COLORS.get(label, "gray")
        if score > 80.0:
            return "SEVERE", "red"
        return "MINIMAL", "green"

    @classmethod
    def calculate_report_bdi(
        cls,
        report: SafetyReport,
        barriers: List[BarrierAssessmentItem],
        has_cross_report_correlation: bool = False,
        custom_weights: Optional[Dict[str, float]] = None,
        custom_thresholds: Optional[Dict[str, Tuple[float, float]]] = None
    ) -> Dict[str, Any]:
        """
        Calculates BDI score, component contributions, classification, and explainability for a report.
        """
        w = custom_weights or cls.DEFAULT_WEIGHTS
        contributions: List[BDIComponentContribution] = []
        raw_points = 0.0

        # 1. Failed Barriers
        failed_barriers = [b for b in barriers if b.status == "FAILED"]
        if failed_barriers:
            pts = min(w["max_failed_barriers"], len(failed_barriers) * w["failed_barrier_per_item"])
            raw_points += pts
            b_names = [b.barrier_name for b in failed_barriers]
            contributions.append(BDIComponentContribution(
                component_name="Failed Defense Barriers",
                category="Barrier State",
                points_added=pts,
                max_possible_points=w["max_failed_barriers"],
                description=f"{len(failed_barriers)} barrier(s) completely failed or breached: {', '.join(b_names)}",
                evidence_detail={"failed_count": len(failed_barriers), "barriers": b_names}
            ))

        # 2. Degraded Barriers
        degraded_barriers = [b for b in barriers if b.status == "DEGRADED"]
        if degraded_barriers:
            pts = min(w["max_degraded_barriers"], len(degraded_barriers) * w["degraded_barrier_per_item"])
            raw_points += pts
            b_names = [b.barrier_name for b in degraded_barriers]
            contributions.append(BDIComponentContribution(
                component_name="Degraded Defense Barriers",
                category="Barrier State",
                points_added=pts,
                max_possible_points=w["max_degraded_barriers"],
                description=f"{len(degraded_barriers)} barrier(s) partially compromised or deficient: {', '.join(b_names)}",
                evidence_detail={"degraded_count": len(degraded_barriers), "barriers": b_names}
            ))

        # 3. Multi-Factor Convergence
        total_holes = len(failed_barriers) + len(degraded_barriers)
        factor_count = (report.factor_count or 0) or len(report.detected_factors or []) or total_holes
        if factor_count >= 4 or total_holes >= 4:
            pts = w["multi_factor_4_points"]
            raw_points += pts
            contributions.append(BDIComponentContribution(
                component_name="4+ Factor Multi-Barrier Convergence",
                category="Convergence Complexity",
                points_added=pts,
                max_possible_points=w["multi_factor_4_points"],
                description="Simultaneous collapse across 4 or more safety control layers.",
                evidence_detail={"factor_count": factor_count, "holes_aligned": total_holes}
            ))
        elif factor_count == 3 or total_holes == 3:
            pts = w["multi_factor_3_points"]
            raw_points += pts
            contributions.append(BDIComponentContribution(
                component_name="3-Factor Multi-Barrier Convergence",
                category="Convergence Complexity",
                points_added=pts,
                max_possible_points=w["multi_factor_3_points"],
                description="Simultaneous collapse across 3 safety control layers.",
                evidence_detail={"factor_count": factor_count, "holes_aligned": total_holes}
            ))
        elif factor_count == 2 or total_holes == 2:
            pts = w["multi_factor_2_points"]
            raw_points += pts
            contributions.append(BDIComponentContribution(
                component_name="2-Factor Multi-Barrier Convergence",
                category="Convergence Complexity",
                points_added=pts,
                max_possible_points=w["multi_factor_2_points"],
                description="Compound interaction between 2 compromised defense barriers.",
                evidence_detail={"factor_count": factor_count, "holes_aligned": total_holes}
            ))

        # 4. Recurring Issue
        if report.repeated_issue is True:
            pts = w["repeated_issue_points"]
            raw_points += pts
            contributions.append(BDIComponentContribution(
                component_name="Repeated Control Failure",
                category="Systemic Recurrence",
                points_added=pts,
                max_possible_points=w["repeated_issue_points"],
                description="Repeated safety issue ignored or recurrence prevention failure on record.",
                evidence_detail={"repeated_issue": True}
            ))

        # 5. Previous Similar Reports
        prev_cnt = report.previous_similar_reports or 0
        if prev_cnt > 0:
            pts = min(w["max_previous_similar"], prev_cnt * w["previous_similar_per_report"])
            raw_points += pts
            contributions.append(BDIComponentContribution(
                component_name="Historical Recurrence Frequency",
                category="Systemic Recurrence",
                points_added=pts,
                max_possible_points=w["max_previous_similar"],
                description=f"{prev_cnt} previous similar reports recorded on this equipment/unit.",
                evidence_detail={"previous_similar_reports": prev_cnt}
            ))

        # 6. Unresolved Corrective Actions
        status = (report.action_status or "").strip().lower()
        if status in ["overdue"]:
            pts = w["unresolved_action_overdue"]
            raw_points += pts
            contributions.append(BDIComponentContribution(
                component_name="Overdue Corrective Action",
                category="Remediation Status",
                points_added=pts,
                max_possible_points=w["unresolved_action_overdue"],
                description="Remediation deadline has expired without closure verification.",
                evidence_detail={"action_status": report.action_status}
            ))
        elif status in ["open", "in progress", "pending"]:
            pts = w["unresolved_action_open"]
            raw_points += pts
            contributions.append(BDIComponentContribution(
                component_name="Unresolved Corrective Action",
                category="Remediation Status",
                points_added=pts,
                max_possible_points=w["unresolved_action_open"],
                description=f"Remedial action in active execution state ('{report.action_status}').",
                evidence_detail={"action_status": report.action_status}
            ))

        # 7. High Potential Near Miss
        if getattr(report, "high_potential", False) is True:
            pts = w["high_potential_points"]
            raw_points += pts
            contributions.append(BDIComponentContribution(
                component_name="High-Potential Precursor Exposure",
                category="Consequence Potential",
                points_added=pts,
                max_possible_points=w["high_potential_points"],
                description="Incident formally categorized as High-Potential Near Miss.",
                evidence_detail={"high_potential": True}
            ))

        # 8. Cross-Report Convergence
        if has_cross_report_correlation:
            pts = w["cross_report_convergence_points"]
            raw_points += pts
            contributions.append(BDIComponentContribution(
                component_name="Cross-Report Physical Convergence",
                category="Operational Alignment",
                points_added=pts,
                max_possible_points=w["cross_report_convergence_points"],
                description="Evidence indicates multiple independent reports converging on same equipment or unit.",
                evidence_detail={"cross_report_convergence": True}
            ))

        # Final BDI Score (0.0 to 100.0)
        bdi_score = min(100.0, max(0.0, round(raw_points, 1)))
        active_thresholds = custom_thresholds or cls.DEFAULT_THRESHOLDS
        classification, color = cls.classify_score(bdi_score, active_thresholds)

        # Build Explainability
        top_contribs = [c.component_name for c in sorted(contributions, key=lambda x: -x.points_added)[:4]]

        if bdi_score <= 20.0:
            why = f"BDI is {bdi_score} ({classification}): Controls are predominantly intact with minimal barrier erosion."
            remediation = "Continue routine inspections and maintain verified barrier compliance."
        elif bdi_score <= 40.0:
            why = f"BDI is {bdi_score} ({classification}): Isolated single-barrier degradation detected without compound control collapse."
            remediation = "Remediate identified minor barrier deficiency during upcoming maintenance cycle."
        elif bdi_score <= 60.0:
            why = f"BDI is {bdi_score} ({classification}): Moderate barrier degradation driven by {', '.join(top_contribs[:2])}."
            remediation = "Implement supervisory intervention and verify integrity of compromised defense layers."
        elif bdi_score <= 80.0:
            why = f"BDI is {bdi_score} ({classification}): Significant barrier compromise resulting from {', '.join(top_contribs[:3])}."
            remediation = "URGENT: Expedite overdue remediation and review physical operating envelope."
        else:
            why = f"BDI is {bdi_score} ({classification}): Critical multi-barrier collapse driven by {', '.join(top_contribs[:4])}."
            remediation = "CRITICAL: Immediate management escalation required; re-establish all compromised barriers before continuing operations."

        t_range = active_thresholds.get(classification, cls.DEFAULT_THRESHOLDS[classification])
        explainability = BDIExplainability(
            why_summary=why,
            classification_rationale=f"Score {bdi_score} falls into the '{classification}' threshold range ({t_range[0]} - {t_range[1]}).",
            top_contributors=top_contribs,
            component_breakdown=contributions,
            remediation_guidance=remediation
        )

        barrier_states_summary = {
            "intact": sum(1 for b in barriers if b.status == "INTACT"),
            "degraded": len(degraded_barriers),
            "failed": len(failed_barriers),
            "unknown": sum(1 for b in barriers if b.status == "UNKNOWN")
        }

        independent_metrics = IndependentMetrics(
            recorded_risk_level=report.risk_level or "Unspecified",
            ai_risk_level="High" if bdi_score >= 60.0 else ("Medium" if bdi_score >= 30.0 else "Low"),
            bdi_score=bdi_score,
            bdi_classification=classification,
            sif_precursor_status=bool(report.sif_precursor or report.high_potential),
            high_potential_status=bool(report.high_potential)
        )

        return {
            "bdi_score": bdi_score,
            "classification": classification,
            "classification_color": color,
            "independent_metrics": independent_metrics,
            "component_contributions": contributions,
            "barrier_states_summary": barrier_states_summary,
            "explainability": explainability,
            "source_reports_count": 1,
            "source_report_ids": [report.id],
            "calculation_version": cls.VERSION,
            "calculated_at": datetime.utcnow()
        }

    @classmethod
    def calculate_unit_bdi(
        cls,
        unit_name: str,
        reports: List[SafetyReport],
        unit_barriers: List[BarrierAssessmentItem]
    ) -> Dict[str, Any]:
        """
        Calculates unit-level BDI weighted by barrier degradation density and equipment convergence.
        """
        if not reports:
            return {
                "refinery_unit": unit_name,
                "unit_bdi_score": 0.0,
                "classification": "MINIMAL",
                "classification_color": "green",
                "data_adequacy_status": "INSUFFICIENT",
                "total_contributing_reports": 0,
                "dominant_degraded_barriers": [],
                "dominant_factors": [],
                "high_bdi_equipment_count": 0,
                "calculation_methodology_note": "Insufficient operational safety reports in unit to establish a reliable BDI.",
                "trend_direction": "STABLE"
            }

        # Calculate individual BDIs
        individual_scores = []
        high_equip = set()
        for r in reports:
            rep_barriers = [b for b in unit_barriers if r.id in b.source_report_ids]
            res = cls.calculate_report_bdi(r, rep_barriers)
            score = res["bdi_score"]
            individual_scores.append(score)
            if score >= 60.0 and r.equipment:
                high_equip.add(r.equipment)

        avg_score = sum(individual_scores) / len(individual_scores)

        # Density of multi-barrier breakdown in the unit
        severe_ratio = sum(1 for s in individual_scores if s >= 80.0) / len(individual_scores)
        high_ratio = sum(1 for s in individual_scores if s >= 60.0) / len(individual_scores)

        # Unit BDI calculation (Weighted combination: 60% avg + 25% high density + 15% equipment concentration)
        unit_score = (avg_score * 0.60) + (high_ratio * 30.0) + (min(len(high_equip), 5) * 5.0)
        unit_bdi = min(100.0, max(0.0, round(unit_score, 1)))
        classification, color = cls.classify_score(unit_bdi)

        # Dominant degraded barriers
        degraded_counter = Counter([b.barrier_name for b in unit_barriers if b.status in ["DEGRADED", "FAILED"]])
        dominant_barriers = [{"barrier": k, "count": v} for k, v in degraded_counter.most_common(5)]

        # Dominant factors
        factor_counter = Counter()
        for r in reports:
            if r.detected_factors:
                for f in r.detected_factors:
                    factor_counter[f] += 1
            if r.ppe_issue:
                factor_counter["PPE_NonCompliance"] += 1
            if r.supervisor_factor:
                factor_counter["Supervisor_Negligence"] += 1
            if r.maintenance_factor:
                factor_counter["Maintenance_Delay_or_Issue"] += 1
            if r.repeated_issue:
                factor_counter["Repeated_Issue_Ignored"] += 1

        dominant_factors = [{"factor": k.replace("_", " "), "count": v} for k, v in factor_counter.most_common(5)]

        methodology_note = (
            f"Unit BDI of {unit_bdi} ({classification}) computed from {len(reports)} reports and {len(unit_barriers)} barrier assessments "
            f"using weighted density modeling (60% baseline mean BDI [{round(avg_score, 1)}], 25% elevated risk concentration [{round(high_ratio*100, 1)}%], "
            f"and 15% equipment hotspot clustering [{len(high_equip)} high-degradation equipment tag(s)])."
        )

        return {
            "refinery_unit": unit_name,
            "unit_bdi_score": unit_bdi,
            "classification": classification,
            "classification_color": color,
            "data_adequacy_status": "SUFFICIENT",
            "total_contributing_reports": len(reports),
            "dominant_degraded_barriers": dominant_barriers,
            "dominant_factors": dominant_factors,
            "high_bdi_equipment_count": len(high_equip),
            "calculation_methodology_note": methodology_note,
            "trend_direction": "INCREASING" if severe_ratio > 0.2 else ("STABLE" if high_ratio > 0.2 else "DECREASING")
        }
