import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Set
from collections import Counter

from app.models.safety_report import SafetyReport
from app.schemas.barriers import (
    BarrierExplainability,
    BarrierAssessmentItem,
    SwissCheeseLayer,
    SwissCheeseVisualization
)


class BarrierEngine:
    """
    Reason's Swiss Cheese Safety Defense & Multi-Barrier Convergence Engine.
    Evaluates safety controls as defensive layers, determines discrete barrier states
    (INTACT, DEGRADED, FAILED, UNKNOWN) grounded in evidence, and models escalation pathways.
    """

    ENGINE_VERSION = "v2.0.0"

    # Standard Layer Hierarchy (Outer Organizational to Inner Physical)
    STANDARD_BARRIERS = [
        {
            "id": "PROCEDURAL_CONTROL",
            "name": "Permit & Procedural Control",
            "category": "Procedural Defense",
            "layer_index": 1
        },
        {
            "id": "SUPERVISION",
            "name": "Supervision & Operational Oversight",
            "category": "Organizational Oversight",
            "layer_index": 2
        },
        {
            "id": "RECURRENCE_PREVENTION",
            "name": "Recurrence Prevention & Systemic Learning",
            "category": "Systemic Learning",
            "layer_index": 3
        },
        {
            "id": "CORRECTIVE_ACTION",
            "name": "Corrective Action Remediation",
            "category": "Remediation Defense",
            "layer_index": 4
        },
        {
            "id": "EQUIPMENT_INTEGRITY",
            "name": "Equipment Integrity & Preventive Maintenance",
            "category": "Engineering Defense",
            "layer_index": 5
        },
        {
            "id": "OPERATIONAL_CONTROL",
            "name": "Operational Environmental Control",
            "category": "Operational Defense",
            "layer_index": 6
        },
        {
            "id": "PERSONAL_PROTECTION",
            "name": "PPE & Physical Personal Protection",
            "category": "Physical Defense",
            "layer_index": 7
        }
    ]

    @classmethod
    def assess_report_barriers(cls, report: SafetyReport) -> List[BarrierAssessmentItem]:
        """
        Assesses discrete barrier states for a single safety report.
        Activates barriers ONLY when the dataset provides relevant concrete evidence.
        """
        assessments: List[BarrierAssessmentItem] = []
        rep_id = report.id
        source_id_label = report.original_id or report.id[:8]

        # 1. PPE & Personal Protection Barrier
        ppe_val = getattr(report, "ppe_issue", None)
        desc_lower = f"{report.description or ''} {report.unsafe_act or ''} {report.unsafe_condition or ''}".lower()

        if ppe_val is True or any(term in desc_lower for term in ["without ppe", "no ppe", "missing ppe", "damaged helmet", "no goggles", "without harness", "unprotected"]):
            status = "FAILED" if any(term in desc_lower for term in ["refused", "bypassed ppe", "deliberate", "ignored ppe"]) else "DEGRADED"
            why = "Personal protective equipment barrier compromised during task execution."
            what = f"ppe_issue={ppe_val}; narrative details lack of compliant personal protective barriers."
            assessments.append(cls._create_assessment_item(
                barrier_id="PERSONAL_PROTECTION",
                barrier_name="PPE & Physical Personal Protection",
                barrier_category="Physical Defense",
                layer_index=7,
                status=status,
                confidence=0.95,
                why=why,
                what=what,
                source_reports=[rep_id],
                source_fields=["ppe_issue", "description", "unsafe_act"]
            ))
        elif ppe_val is False and any(term in desc_lower for term in ["ppe verified", "wearing all ppe", "ppe compliant", "properly equipped"]):
            assessments.append(cls._create_assessment_item(
                barrier_id="PERSONAL_PROTECTION",
                barrier_name="PPE & Physical Personal Protection",
                barrier_category="Physical Defense",
                layer_index=7,
                status="INTACT",
                confidence=0.90,
                why="Personal protective equipment verified present, compliant, and deployed.",
                what="Field audit confirmed complete compliant PPE donning.",
                source_reports=[rep_id],
                source_fields=["ppe_issue", "description"]
            ))

        # 2. Supervision & Oversight Barrier
        sup_val = getattr(report, "supervisor_factor", None)
        if sup_val is True or any(term in desc_lower for term in ["supervisor absent", "unsupervised", "lack of supervision", "no supervisor", "unauthorized"]):
            status = "FAILED" if "supervisor absent" in desc_lower or "no permit authorization" in desc_lower else "DEGRADED"
            why = "Supervisory barrier failed to ensure safe system of work before execution."
            what = f"supervisor_factor={sup_val}; task carried out with compromised operational oversight."
            assessments.append(cls._create_assessment_item(
                barrier_id="SUPERVISION",
                barrier_name="Supervision & Operational Oversight",
                barrier_category="Organizational Oversight",
                layer_index=2,
                status=status,
                confidence=0.90,
                why=why,
                what=what,
                source_reports=[rep_id],
                source_fields=["supervisor_factor", "description"]
            ))
        elif sup_val is False and any(term in desc_lower for term in ["supervisor verified", "under supervision", "supervisor stopped work"]):
            assessments.append(cls._create_assessment_item(
                barrier_id="SUPERVISION",
                barrier_name="Supervision & Operational Oversight",
                barrier_category="Organizational Oversight",
                layer_index=2,
                status="INTACT",
                confidence=0.85,
                why="Supervisory presence and job oversight active during operation.",
                what="Supervisor verification active on site.",
                source_reports=[rep_id],
                source_fields=["supervisor_factor", "description"]
            ))

        # 3. Equipment Integrity & Maintenance Barrier
        maint_val = getattr(report, "maintenance_factor", None)
        if maint_val is True or any(term in desc_lower for term in ["deferred maintenance", "seal leak", "vibration", "corrosion", "defective equipment", "maintenance delay", "equipment failure"]):
            status = "FAILED" if any(term in desc_lower for term in ["rupture", "containment loss", "valve failed", "blown gasket", "catastrophic"]) else "DEGRADED"
            why = "Physical equipment barrier or preventive maintenance integrity compromised."
            what = f"maintenance_factor={maint_val}; observed equipment degradation or deferred maintenance."
            assessments.append(cls._create_assessment_item(
                barrier_id="EQUIPMENT_INTEGRITY",
                barrier_name="Equipment Integrity & Preventive Maintenance",
                barrier_category="Engineering Defense",
                layer_index=5,
                status=status,
                confidence=0.90,
                why=why,
                what=what,
                source_reports=[rep_id],
                source_fields=["maintenance_factor", "equipment", "description"]
            ))
        elif maint_val is False and report.equipment and any(term in desc_lower for term in ["equipment inspected", "routine check passed", "preventive maintenance completed"]):
            assessments.append(cls._create_assessment_item(
                barrier_id="EQUIPMENT_INTEGRITY",
                barrier_name="Equipment Integrity & Preventive Maintenance",
                barrier_category="Engineering Defense",
                layer_index=5,
                status="INTACT",
                confidence=0.85,
                why="Equipment integrity verified in compliant operating condition.",
                what="Routine inspection confirms physical barrier intact.",
                source_reports=[rep_id],
                source_fields=["maintenance_factor", "equipment"]
            ))

        # 4. Recurrence Prevention & Systemic Learning Barrier
        rep_val = getattr(report, "repeated_issue", None)
        prev_cnt = report.previous_similar_reports or 0
        if rep_val is True or prev_cnt > 0:
            status = "FAILED"  # Recurrence prevention barrier definitively failed to stop repeat incident
            why = "Recurrence prevention barrier failed; identical hazard has manifested repeatedly."
            what = f"repeated_issue={rep_val}, previous_similar_reports={prev_cnt}; institutional controls failed to eliminate hazard."
            assessments.append(cls._create_assessment_item(
                barrier_id="RECURRENCE_PREVENTION",
                barrier_name="Recurrence Prevention & Systemic Learning",
                barrier_category="Systemic Learning",
                layer_index=3,
                status=status,
                confidence=0.95,
                why=why,
                what=what,
                source_reports=[rep_id],
                source_fields=["repeated_issue", "previous_similar_reports"]
            ))
        elif rep_val is False and prev_cnt == 0 and report.report_date:
            assessments.append(cls._create_assessment_item(
                barrier_id="RECURRENCE_PREVENTION",
                barrier_name="Recurrence Prevention & Systemic Learning",
                barrier_category="Systemic Learning",
                layer_index=3,
                status="INTACT",
                confidence=0.85,
                why="Isolated initial observation without prior recurrence record.",
                what="First recorded occurrence on this equipment/unit.",
                source_reports=[rep_id],
                source_fields=["repeated_issue", "previous_similar_reports"]
            ))

        # 5. Corrective Action Remediation Barrier
        act_status = (report.action_status or "").strip().lower()
        if act_status in ["overdue"]:
            assessments.append(cls._create_assessment_item(
                barrier_id="CORRECTIVE_ACTION",
                barrier_name="Corrective Action Remediation",
                barrier_category="Remediation Defense",
                layer_index=4,
                status="FAILED",
                confidence=0.95,
                why="Corrective action remediation barrier breached due to overdue resolution.",
                what=f"action_status='Overdue'; remediation deadline passed without closure verification.",
                source_reports=[rep_id],
                source_fields=["action_status", "due_date"]
            ))
        elif act_status in ["open", "in progress", "pending"]:
            assessments.append(cls._create_assessment_item(
                barrier_id="CORRECTIVE_ACTION",
                barrier_name="Corrective Action Remediation",
                barrier_category="Remediation Defense",
                layer_index=4,
                status="DEGRADED",
                confidence=0.90,
                why="Corrective action pending implementation; operational exposure remains unmitigated.",
                what=f"action_status='{report.action_status}'; corrective remediation in active progress.",
                source_reports=[rep_id],
                source_fields=["action_status", "assigned_to"]
            ))
        elif act_status in ["closed", "completed"]:
            assessments.append(cls._create_assessment_item(
                barrier_id="CORRECTIVE_ACTION",
                barrier_name="Corrective Action Remediation",
                barrier_category="Remediation Defense",
                layer_index=4,
                status="INTACT",
                confidence=0.95,
                why="Corrective action successfully implemented and closed.",
                what=f"action_status='Closed'; barrier re-established by verified remedial measures.",
                source_reports=[rep_id],
                source_fields=["action_status", "closure_verified_by"]
            ))

        # 6. Permit & Procedural Control Barrier
        work_type = (report.work_type or "").lower()
        if any(term in work_type for term in ["hot work", "confined space", "vessel entry", "height", "critical lift"]):
            if any(term in desc_lower for term in ["no permit", "permit expired", "procedure not followed", "sop violated", "unauthorized work", "bypassed isolat"]):
                status = "FAILED" if "no permit" in desc_lower else "DEGRADED"
                why = "Procedural safety authorization or work permit controls compromised."
                what = f"work_type='{report.work_type}'; deviation from mandatory safe working permit procedure."
                assessments.append(cls._create_assessment_item(
                    barrier_id="PROCEDURAL_CONTROL",
                    barrier_name="Permit & Procedural Control",
                    barrier_category="Procedural Defense",
                    layer_index=1,
                    status=status,
                    confidence=0.90,
                    why=why,
                    what=what,
                    source_reports=[rep_id],
                    source_fields=["work_type", "description"]
                ))
            elif any(term in desc_lower for term in ["permit signed", "valid permit", "ptw verified", "jsa completed"]):
                assessments.append(cls._create_assessment_item(
                    barrier_id="PROCEDURAL_CONTROL",
                    barrier_name="Permit & Procedural Control",
                    barrier_category="Procedural Defense",
                    layer_index=1,
                    status="INTACT",
                    confidence=0.85,
                    why="Permit-to-work and safe operating procedures formally authorized.",
                    what="Valid PTW and job safety analysis active on file.",
                    source_reports=[rep_id],
                    source_fields=["work_type", "description"]
                ))

        # 7. Operational Environmental Control
        if any(term in desc_lower for term in ["spill", "slippery", "lighting poor", "housekeeping", "interlock bypassed", "guard missing"]):
            assessments.append(cls._create_assessment_item(
                barrier_id="OPERATIONAL_CONTROL",
                barrier_name="Operational Environmental Control",
                barrier_category="Operational Defense",
                layer_index=6,
                status="DEGRADED",
                confidence=0.85,
                why="Operational workplace environment controls compromised.",
                what="Observed physical work area hazard or bypass of operational safeguarding.",
                source_reports=[rep_id],
                source_fields=["unsafe_condition", "description"]
            ))

        # 8. Dynamic Future Factors (Extensible Barrier Integration)
        if report.detected_factors and isinstance(report.detected_factors, list):
            for df in report.detected_factors:
                clean_name = df.replace("_", " ").title()
                standard_keys = ["Ppe Noncompliance", "Supervisor Negligence", "Maintenance Delay Or Issue", "Repeated Issue Ignored", "High Potential Near Miss", "Previous Similar Reports", "Unresolved Action"]
                if clean_name not in standard_keys:
                    assessments.append(cls._create_assessment_item(
                        barrier_id=f"DYNAMIC_{df.upper()}",
                        barrier_name=f"{clean_name} Barrier",
                        barrier_category="Specialized Control Defense",
                        layer_index=8,
                        status="DEGRADED",
                        confidence=0.85,
                        why=f"Dynamically detected barrier degradation: '{clean_name}'.",
                        what=f"detected_factors contains '{df}'.",
                        source_reports=[rep_id],
                        source_fields=["detected_factors"]
                    ))

        return assessments

    @classmethod
    def _create_assessment_item(
        cls,
        barrier_id: str,
        barrier_name: str,
        barrier_category: str,
        layer_index: int,
        status: str,
        confidence: float,
        why: str,
        what: str,
        source_reports: List[str],
        source_fields: List[str],
        is_cross_report: bool = False
    ) -> BarrierAssessmentItem:
        explain = BarrierExplainability(
            why=why,
            what_data_supports_this=what,
            which_reports_support_this=source_reports
        )
        evidence = {
            "observation": what,
            "explainability": explain.model_dump()
        }
        return BarrierAssessmentItem(
            id=str(uuid.uuid4()),
            barrier_id=barrier_id,
            barrier_name=barrier_name,
            barrier_category=barrier_category,
            layer_index=layer_index,
            status=status,
            confidence=confidence,
            evidence=evidence,
            explainability=explain,
            source_report_ids=source_reports,
            source_fields=source_fields,
            is_cross_report=is_cross_report,
            engine_version=cls.ENGINE_VERSION,
            created_at=datetime.utcnow()
        )

    @classmethod
    def build_swiss_cheese_model(
        cls,
        barriers: List[BarrierAssessmentItem],
        exposure_target: str,
        hazard_energy: Optional[str] = None
    ) -> SwissCheeseVisualization:
        """
        Synthesizes ordered Swiss Cheese defense layers, counts aligned holes,
        identifies multi-barrier convergence, and models explainable escalation pathways.
        """
        # Sort barriers by defense-in-depth layer index
        sorted_barriers = sorted(barriers, key=lambda b: b.layer_index)

        layers: List[SwissCheeseLayer] = []
        intact_cnt = 0
        degraded_cnt = 0
        failed_cnt = 0
        unknown_cnt = 0

        for b in sorted_barriers:
            st = b.status.upper()
            hole = (st in ["DEGRADED", "FAILED"])

            if st == "INTACT":
                intact_cnt += 1
                color = "green"
                sev = "NONE"
            elif st == "DEGRADED":
                degraded_cnt += 1
                color = "amber"
                sev = "MODERATE"
            elif st == "FAILED":
                failed_cnt += 1
                color = "red"
                sev = "CRITICAL"
            else:
                unknown_cnt += 1
                color = "gray"
                sev = "NONE"

            layers.append(SwissCheeseLayer(
                layer_index=b.layer_index,
                barrier_id=b.barrier_id,
                barrier_name=b.barrier_name,
                barrier_category=b.barrier_category,
                status=st,
                status_color=color,
                hole_present=hole,
                hole_severity=sev,
                explainability=b.explainability,
                source_report_ids=b.source_report_ids
            ))

        holes_aligned = degraded_cnt + failed_cnt
        total_layers = len(layers)

        # Convergence Level Classification
        if holes_aligned >= 3 or failed_cnt >= 2:
            conv_level = "CRITICAL_CONVERGENCE"
        elif holes_aligned == 2:
            conv_level = "ELEVATED"
        elif holes_aligned == 1:
            conv_level = "MINOR"
        else:
            conv_level = "NONE"

        # Build Explainable Escalation Pathway
        escalation_pathway: List[str] = []
        if holes_aligned == 0:
            escalation_pathway.append("All operational barriers intact. Normal defense-in-depth active.")
        else:
            for lyr in layers:
                if lyr.hole_present:
                    escalation_pathway.append(
                        f"Layer {lyr.layer_index} [{lyr.barrier_name}] compromised ({lyr.status}): {lyr.explainability.why}"
                    )
            escalation_pathway.append(
                f"Hazard energy ({hazard_energy or 'Operational Hazard'}) directly exposes target: {exposure_target} due to {holes_aligned} simultaneously aligned barrier hole(s)."
            )

        # Preventive Barrier Imperatives
        if failed_cnt > 0 or degraded_cnt >= 2:
            imperative = f"URGENT: Re-establish compromised defense layers ({holes_aligned} holes aligned). Prioritize restoring {', '.join(l.barrier_name for l in layers if l.hole_present)} before work continues."
        elif degraded_cnt == 1:
            imperative = f"Standard remediation: Address single degraded barrier ({layers[0].barrier_name if layers else 'Barrier'}) to restore complete barrier defense."
        else:
            imperative = "Maintain verified barrier defense compliance across all process layers."

        return SwissCheeseVisualization(
            exposure_target=exposure_target,
            hazard_energy=hazard_energy,
            total_layers=total_layers,
            intact_count=intact_cnt,
            degraded_count=degraded_cnt,
            failed_count=failed_cnt,
            unknown_count=unknown_cnt,
            holes_aligned_count=holes_aligned,
            convergence_level=conv_level,
            layers=layers,
            escalation_pathway=escalation_pathway,
            preventive_barrier_imperative=imperative
        )

    @classmethod
    def synthesize_cross_report_barriers(
        cls,
        primary_report: SafetyReport,
        correlated_reports: List[SafetyReport]
    ) -> List[BarrierAssessmentItem]:
        """
        Synthesizes cross-report barrier evidence into a unified Swiss Cheese sequence
        converging on a shared physical equipment / process unit exposure without merging records.
        """
        all_reports = [primary_report] + [r for r in correlated_reports if r.id != primary_report.id]
        barrier_map: Dict[str, BarrierAssessmentItem] = {}

        for rep in all_reports:
            rep_barriers = cls.assess_report_barriers(rep)
            for b in rep_barriers:
                key = b.barrier_id
                if key not in barrier_map:
                    barrier_map[key] = b
                else:
                    existing = barrier_map[key]
                    # If any report shows FAILED, barrier status escalates to FAILED
                    if b.status == "FAILED" and existing.status != "FAILED":
                        existing.status = "FAILED"
                        existing.explainability.why = b.explainability.why
                    elif b.status == "DEGRADED" and existing.status == "INTACT":
                        existing.status = "DEGRADED"
                        existing.explainability.why = b.explainability.why

                    # Union report IDs
                    combined_sources = list(set(existing.source_report_ids + b.source_report_ids))
                    existing.source_report_ids = combined_sources
                    existing.explainability.which_reports_support_this = combined_sources
                    existing.is_cross_report = (len(combined_sources) > 1)

        return list(barrier_map.values())
