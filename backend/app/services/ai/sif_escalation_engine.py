from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from app.models.safety_report import SafetyReport
from app.schemas.barriers import BarrierAssessmentItem
from app.schemas.sif_escalation import (
    EscalationStageItem,
    PreventiveIntelligencePayload,
    ReportSIFEscalationResponse
)
from app.services.ai.bdi_engine import BDIEngine


class SIFEscalationEngine:
    """
    SIF Precursor Escalation Engine.
    Evaluates multi-dimensional evidence across recorded risk, AI risk, BDI score, defense barrier integrity,
    organizational factors, recurrence, and cross-report convergence to detect potential serious injury/fatality escalation.
    Constructs explainable 7-stage conceptual scenario pathways using probabilistic safety language.
    """

    VERSION = "v4.0.0"

    HIGH_ENERGY_HAZARDS = [
        "hydrocarbon release", "flash fire", "fire", "explosion", "bleve",
        "toxic gas", "h2s", "benzene", "high pressure", "steam release",
        "rotating equipment", "confined space", "work at height", "fall",
        "crane lift", "chemical splash", "acid", "caustic", "electrical arc"
    ]

    CRITICAL_CONSEQUENCES = [
        "fatality", "multiple casualties", "lost-time injury", "major fire",
        "catastrophic failure", "rupture", "severe burn", "amputation", "toxic asphyxiation"
    ]

    SEVERITY_COLORS = {
        "NORMAL": "green",
        "WATCH": "cyan",
        "ELEVATED": "amber",
        "HIGH": "orange",
        "CRITICAL": "red"
    }

    @classmethod
    def categorize_sif_hazard(cls, report: SafetyReport) -> str:
        """Determines the primary SIF hazard category from report text and metadata."""
        desc = (report.description or "").lower()
        hazard = (report.hazard or report.potential_consequence or "").lower()
        work = (report.work_type or "").lower()
        comb = f"{desc} {hazard} {work}"

        if any(k in comb for k in ["fire", "flash", "thermal", "hot work", "burner", "furnace"]):
            return "Thermal / Flash Fire Hazard"
        elif any(k in comb for k in ["hydrocarbon", "gas", "toxic", "h2s", "chemical", "acid", "caustic", "leak"]):
            return "Chemical / Hydrocarbon / Toxic Gas Release"
        elif any(k in comb for k in ["confined", "vessel", "tank entry"]):
            return "Confined Space Atmospheric Hazard"
        elif any(k in comb for k in ["height", "fall", "scaffold", "ladder", "roof"]):
            return "Work at Height / Fall Hazard"
        elif any(k in comb for k in ["rotating", "pump", "compressor", "turbine", "coupling", "seal"]):
            return "High-Energy Rotating Equipment Mechanical Hazard"
        elif any(k in comb for k in ["lift", "crane", "overhead", "impact", "rigging", "falling object"]):
            return "Overhead Impact & Heavy Lifting Hazard"
        elif any(k in comb for k in ["electrical", "arc", "switchgear", "voltage"]):
            return "High-Voltage Electrical Arc Hazard"
        return "Operational Process Safety Control Hazard"

    @classmethod
    def evaluate_escalation(
        cls,
        report: SafetyReport,
        barriers: List[BarrierAssessmentItem],
        bdi_score: float,
        bdi_classification: str,
        has_cross_report_correlation: bool = False,
        correlated_reports: Optional[List[SafetyReport]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates multi-dimensional evidence to determine SIF Precursor Status, Severity,
        7-stage conceptual escalation scenario, and comprehensive explainability.
        """
        desc_lower = (report.description or "").lower()
        consequence_lower = (report.potential_consequence or report.hazard or "").lower()
        work_lower = (report.work_type or "").lower()
        unit_str = report.refinery_unit or "Process Unit"
        equip_str = f" / Equipment {report.equipment}" if report.equipment else ""
        exposure_target = f"{unit_str}{equip_str} ({report.work_type or 'General Work'})"

        # 1. Evaluate Evidence Dimensions
        failed_barriers = [b for b in barriers if b.status == "FAILED"]
        degraded_barriers = [b for b in barriers if b.status == "DEGRADED"]
        total_holes = len(failed_barriers) + len(degraded_barriers)

        has_high_energy = any(h in desc_lower or h in consequence_lower for h in cls.HIGH_ENERGY_HAZARDS)
        has_catastrophic_consequence = any(c in consequence_lower for c in cls.CRITICAL_CONSEQUENCES) or ("multiple casualties" in consequence_lower) or ("bleve" in consequence_lower)
        is_high_potential = getattr(report, "high_potential", False) is True
        is_repeated = getattr(report, "repeated_issue", False) is True
        prev_count = report.previous_similar_reports or 0
        action_status = (report.action_status or "").strip().lower()
        is_overdue = (action_status == "overdue")
        is_action_unresolved = action_status in ["open", "in progress", "pending", "overdue"]

        # Factor counts
        factors: List[str] = []
        if getattr(report, "ppe_issue", False):
            factors.append("PPE Non-Compliance")
        if getattr(report, "supervisor_factor", False):
            factors.append("Supervisor Absence / Oversight Deficiency")
        if getattr(report, "maintenance_factor", False):
            factors.append("Equipment Maintenance Delay / Integrity Issue")
        if is_repeated:
            factors.append("Repeated Safety Issue Ignored")
        if prev_count > 0:
            factors.append(f"{prev_count} Previous Similar Report(s)")
        if is_overdue:
            factors.append("Overdue Corrective Remediation Action")
        elif is_action_unresolved:
            factors.append(f"Unresolved Corrective Action ('{report.action_status}')")
        if is_high_potential:
            factors.append("High Potential Near Miss (HiPo) Exposure")
        if has_cross_report_correlation:
            factors.append("Cross-Report Physical Convergence on Same Asset")

        sif_category = cls.categorize_sif_hazard(report)

        # 2. Multi-Dimensional Severity Determination
        # Rule: CRITICAL requires multi-dimensional convergence (high energy / severe consequence AND multiple barrier collapse AND unmitigated institutional context)
        # BDI > 80 alone on a low-energy event without severe hazard does NOT trigger CRITICAL.
        if (has_high_energy or has_catastrophic_consequence or is_high_potential) and (bdi_score >= 80.0 or len(failed_barriers) >= 2 or (total_holes >= 3 and is_overdue)):
            severity = "CRITICAL"
            sif_precursor_status = True
            why = (
                f"Escalated to CRITICAL due to multi-dimensional convergence: high-energy hazard exposure ({sif_category}), "
                f"{len(failed_barriers)} failed and {len(degraded_barriers)} degraded defense barrier(s) (BDI {bdi_score}), "
                f"combined with unresolved institutional breakdown ({', '.join(factors[:3])})."
            )
        elif is_high_potential and total_holes >= 2:
            severity = "CRITICAL"
            sif_precursor_status = True
            why = (
                f"Escalated to CRITICAL because incident is formally flagged as High Potential Near Miss with "
                f"{total_holes} compromised defense barriers and compound operational vulnerability."
            )
        elif (has_high_energy or has_catastrophic_consequence or is_high_potential or bdi_score >= 60.1) and (total_holes >= 2 or is_overdue or is_repeated):
            severity = "HIGH"
            sif_precursor_status = True
            why = (
                f"Escalated to HIGH: Active SIF precursor conditions present with {total_holes} compromised defense layer(s) "
                f"and elevated barrier degradation index (BDI {bdi_score})."
            )
        elif total_holes >= 2 or bdi_score >= 40.1 or is_repeated or (has_high_energy and total_holes >= 1):
            severity = "ELEVATED"
            sif_precursor_status = bool(has_high_energy or is_high_potential)
            why = (
                f"Classified as ELEVATED: Moderate barrier erosion detected across {total_holes} control layer(s) "
                f"(BDI {bdi_score}) requiring operational supervisory intervention."
            )
        elif total_holes == 1 or bdi_score >= 20.1 or is_action_unresolved:
            severity = "WATCH"
            sif_precursor_status = False
            why = (
                f"Classified as WATCH: Isolated single-barrier deficiency identified ({', '.join([b.barrier_name for b in degraded_barriers + failed_barriers])}) "
                f"without compound defense collapse or direct high-energy escalation vector."
            )
        else:
            severity = "NORMAL"
            sif_precursor_status = False
            why = "Classified as NORMAL: Defensive controls are verified intact with minimal barrier erosion and no precursor vectors."

        # 3. Build 7-Stage Conceptual Escalation Scenario
        failed_names = [b.barrier_name for b in failed_barriers]
        degraded_names = [b.barrier_name for b in degraded_barriers]
        all_hole_names = failed_names + degraded_names
        primary_hole = all_hole_names[0] if all_hole_names else "Physical Guarding & Containment"

        escalation_scenario: List[EscalationStageItem] = [
            EscalationStageItem(
                stage_number=1,
                stage_name="CURRENT CONDITION",
                description=f"Observed condition on {exposure_target}: {report.description or 'Operating baseline'}.",
                barrier_or_factor_involved=primary_hole
            ),
            EscalationStageItem(
                stage_number=2,
                stage_name="CONTINUED EXPOSURE",
                description="Field activities continue without pausing work to verify defense barrier integrity.",
                barrier_or_factor_involved="Supervision & Operational Oversight"
            ),
            EscalationStageItem(
                stage_number=3,
                stage_name="MULTIPLE CONTROL DEGRADATION",
                description=f"Erosion compounds across defense layers: {', '.join(all_hole_names) if all_hole_names else 'Baseline control decay'}.",
                barrier_or_factor_involved="Defense-in-Depth Layers"
            ),
            EscalationStageItem(
                stage_number=4,
                stage_name="LOSS OF CONTROL",
                description=f"Compromised controls allow primary energy or hazardous medium to breach containment envelope in {unit_str}.",
                barrier_or_factor_involved="Engineering & Equipment Integrity"
            ),
            EscalationStageItem(
                stage_number=5,
                stage_name="POTENTIAL INCIDENT",
                description=f"Potential energetic release, ignition flash, mechanical failure, or personal fall event ({sif_category}).",
                barrier_or_factor_involved="Permit & Procedural Control"
            ),
            EscalationStageItem(
                stage_number=6,
                stage_name="SERIOUS CONSEQUENCE",
                description=f"Theoretical scenario consequence: {report.potential_consequence or 'Lost-time personal injury or major equipment damage'}.",
                barrier_or_factor_involved="PPE & Physical Protection"
            ),
            EscalationStageItem(
                stage_number=7,
                stage_name="POTENTIAL FATAL CONSEQUENCE",
                description="Worst-case conceptual scenario pathway under unmitigated defense collapse (hypothetical escalation model).",
                barrier_or_factor_involved="Multi-Barrier Safeguarding"
            )
        ]

        # 4. Preventive Intelligence Payload (for HIGH and CRITICAL)
        preventive_intel: Optional[PreventiveIntelligencePayload] = None
        if severity in ["HIGH", "CRITICAL"]:
            preventive_intel = PreventiveIntelligencePayload(
                current_condition=report.description or "Active operating exposure",
                hazard_exposure=f"{sif_category} within {unit_str}",
                control_failure=f"Compromised defense barriers: {', '.join(all_hole_names) if all_hole_names else 'Defense erosion'}",
                immediate_containment=(
                    "MANDATORY STOP-WORK: Verify complete physical isolation, ensure 100% compliant PPE donning, "
                    "and mandate on-site supervisor presence before work resumption."
                    if severity == "CRITICAL" else
                    "Pause work to re-establish compromised barrier controls and verify work authorization."
                ),
                preventive_control=(
                    "Conduct root-cause barrier audit, expedite overdue corrective actions, and review engineering interlocks across unit."
                    if severity == "CRITICAL" else
                    "Implement preventive maintenance check and reinforce job safety analysis verification."
                ),
                potential_escalation=f"Potential scenario pathway toward {report.potential_consequence or 'severe energy release and lost-time injury'}."
            )

        # 5. Formulate Specific Explanation Questions
        which_reports = [report.id]
        if correlated_reports:
            which_reports.extend([r.id for r in correlated_reports])

        unresolved: List[str] = []
        if is_overdue:
            unresolved.append(f"Corrective action is OVERDUE (Status: '{report.action_status}')")
        elif is_action_unresolved:
            unresolved.append(f"Corrective action in progress without verified closure ('{report.action_status}')")
        if is_repeated:
            unresolved.append("Recurring equipment/operational defect previously documented without effective closure")
        if failed_barriers:
            unresolved.append(f"Unrestored defense barrier(s): {', '.join(failed_names)}")

        what_could_happen = (
            f"If unmitigated, continued exposure in {unit_str} presents a potential escalation pathway toward "
            f"uncontrolled {sif_category.lower()} and {report.potential_consequence or 'severe personal consequence'}."
        )

        # 6. Action Recommendations
        if severity == "CRITICAL":
            imm_action = "CRITICAL ALERT: Issue immediate stop-work order. Secure physical area, verify positive isolation, and escalate to Refinery Operations Management."
            prev_action = "Execute comprehensive barrier reconstruction audit, resolve overdue corrective actions, and mandate formal MOC review."
        elif severity == "HIGH":
            imm_action = "URGENT INTERVENTION: Require immediate supervisory review on site and re-establish degraded personal/procedural barriers."
            prev_action = "Expedite maintenance work order, verify permit conditions, and inspect similar equipment across the process unit."
        elif severity == "ELEVATED":
            imm_action = "Supervisory briefing required before commencing next shift operation; remediate identified barrier deficiency."
            prev_action = "Track open corrective action to closure and log inspection verification in safety management system."
        elif severity == "WATCH":
            imm_action = "Remind technicians of standard operating procedures and compliant protective measures."
            prev_action = "Include identified item in upcoming routine maintenance or safety walkdown."
        else:
            imm_action = "Maintain routine operational monitoring."
            prev_action = "Continue standard scheduled safety inspections."

        confidence = 0.85
        if len(factors) >= 3:
            confidence += 0.07
        if is_high_potential:
            confidence += 0.04
        if has_catastrophic_consequence:
            confidence += 0.02
        confidence = min(0.98, round(confidence, 2))

        barrier_summary = {
            "intact": sum(1 for b in barriers if b.status == "INTACT"),
            "degraded": len(degraded_barriers),
            "failed": len(failed_barriers),
            "unknown": sum(1 for b in barriers if b.status == "UNKNOWN")
        }

        return {
            "severity": severity,
            "severity_color": cls.SEVERITY_COLORS.get(severity, "gray"),
            "sif_precursor_status": sif_precursor_status,
            "sif_category": sif_category,
            "why_escalated": why,
            "which_barriers": all_hole_names,
            "which_factors": factors,
            "which_reports": which_reports,
            "what_exposure": exposure_target,
            "what_potential_consequence": report.potential_consequence or "Uncontrolled Energy Release / Personal Injury",
            "what_remains_unresolved": unresolved,
            "what_could_happen": what_could_happen,
            "barrier_summary": barrier_summary,
            "contributing_factors": factors,
            "escalation_scenario": escalation_scenario,
            "preventive_intelligence": preventive_intel,
            "recommended_immediate_action": imm_action,
            "recommended_preventive_action": prev_action,
            "confidence": confidence,
            "engine_version": cls.VERSION,
            "created_at": datetime.utcnow()
        }
