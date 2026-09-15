import hashlib
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

from app.models.safety_report import SafetyReport
from app.schemas.barriers import BarrierAssessmentItem
from app.schemas.orchestrator import ActionPackageSchema, EmailDraftResponse


class OrchestrationEngine:
    """
    AI Safety Action Orchestrator Engine.
    Synthesizes multi-factor correlations, barrier health, BDI, and SIF escalation into a controlled,
    role-based action package with SLA deadlines, context-aware email drafts, and webhook payloads.
    Guarantees strict safety boundaries (workflow intelligence only; never operates equipment).
    """

    VERSION = "v5.0.0"

    ROLE_MATRIX = {
        "CRITICAL": "Unit In-Charge",
        "HIGH": "Safety Officer",
        "ELEVATED": "Unit In-Charge",
        "WATCH": "Safety Officer",
        "NORMAL": "Safety Officer"
    }

    SLA_MATRIX = {
        "CRITICAL": 2,     # 2 Hours (Immediate Stop-Work & Containment)
        "HIGH": 4,         # 4 Hours (Supervisory Review & Containment)
        "ELEVATED": 24,    # 24 Hours (Corrective Action)
        "WATCH": 72,       # 72 Hours (Routine Maintenance Walkdown)
        "NORMAL": 72       # 72 Hours (Routine Verification)
    }

    ACTION_TYPE_MATRIX = {
        "CRITICAL": "SAFETY_HOLD_REQUEST",
        "HIGH": "CONTAINMENT",
        "ELEVATED": "CORRECTIVE_ACTION",
        "WATCH": "PREVENTIVE_ACTION",
        "NORMAL": "VERIFICATION"
    }

    @classmethod
    def generate_action_package(
        cls,
        report: SafetyReport,
        barriers: List[BarrierAssessmentItem],
        bdi_result: Dict[str, Any],
        escalation_result: Dict[str, Any],
        correlated_reports: Optional[List[SafetyReport]] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes all platform intelligence into a comprehensive 19-field Action Package.
        """
        sev = escalation_result.get("severity", "HIGH")
        sla_hrs = cls.SLA_MATRIX.get(sev, 24)
        sla_deadline = datetime.utcnow() + timedelta(hours=sla_hrs)

        action_type = cls.ACTION_TYPE_MATRIX.get(sev, "CONTAINMENT")
        if getattr(report, "maintenance_factor", False) and sev in ["HIGH", "ELEVATED"]:
            assigned_role = "Department Head"
        elif sev == "CRITICAL":
            assigned_role = "Unit In-Charge"
        else:
            assigned_role = cls.ROLE_MATRIX.get(sev, "Safety Officer")

        # Extract barrier names
        failed_barriers = [b.barrier_name for b in barriers if b.status == "FAILED"]
        degraded_barriers = [b.barrier_name for b in barriers if b.status == "DEGRADED"]
        all_compromised = failed_barriers + degraded_barriers

        unit_str = report.refinery_unit or "Process Unit"
        equip_str = f" / {report.equipment}" if report.equipment else ""

        # Verification requirement
        if sev == "CRITICAL":
            verif_req = "Mandatory on-site physical walkdown by Unit In-Charge and HSE Head with documented permit re-authorization prior to lifting safety hold."
        elif sev == "HIGH":
            verif_req = "Field inspection by Safety Officer confirming positive barrier remediation before closing action item."
        elif sev == "ELEVATED":
            verif_req = "Shift supervisor verification and closure sign-off logged in safety management system."
        else:
            verif_req = "Standard routine inspection sign-off."

        title = f"{action_type.replace('_', ' ')}: {escalation_result.get('sif_category', 'Safety Exposure')} at {unit_str}{equip_str}"
        description = (
            f"Automated AI safety response package for report {report.id} ({unit_str}). "
            f"Precursor evaluated at {sev} severity with BDI score {bdi_result.get('bdi_score', 0.0)} ({bdi_result.get('classification', 'MINIMAL')}). "
            f"Compromised barriers: {', '.join(all_compromised) if all_compromised else 'None'}. "
            f"Required containment SLA: {sla_hrs} hours."
        )

        prev_intel = escalation_result.get("preventive_intelligence")
        corr_act = None
        if isinstance(prev_intel, dict):
            corr_act = prev_intel.get("control_failure") or prev_intel.get("root_cause")
        elif hasattr(prev_intel, "control_failure"):
            corr_act = getattr(prev_intel, "control_failure", None)
        if not corr_act:
            corr_act = "Remediate identified defense barrier defect."

        package_data = {
            "report_id": report.id,
            "dataset_id": report.dataset_id,
            "refinery_unit": report.refinery_unit,
            "equipment": report.equipment,
            "work_type": report.work_type,
            "observed_condition": report.description or "Observed operational deviation",
            "safety_factors": escalation_result.get("which_factors", []),
            "barrier_status": bdi_result.get("barrier_states_summary", {}),
            "bdi_score": bdi_result.get("bdi_score", 0.0),
            "bdi_classification": bdi_result.get("classification", "MINIMAL"),
            "recorded_risk": report.risk_level or "Low",
            "ai_risk": "Critical" if sev == "CRITICAL" else ("High" if sev == "HIGH" else "Medium"),
            "severity": sev,
            "sif_status": "YES" if escalation_result.get("sif_precursor_status") else "NO",
            "potential_consequence": escalation_result.get("what_potential_consequence", "Uncontrolled Exposure"),
            "immediate_containment_recommendation": escalation_result.get("recommended_immediate_action", "Pause work and verify controls"),
            "corrective_action": corr_act,
            "preventive_action": escalation_result.get("recommended_preventive_action", "Implement engineering controls and audit process unit"),
            "verification_requirement": verif_req,
            "responsible_role": assigned_role,
            "sla_hours": sla_hrs,
            "sla_deadline": sla_deadline.isoformat()
        }

        ai_recommendations = {
            "immediate_containment": escalation_result.get("recommended_immediate_action"),
            "preventive_action": escalation_result.get("recommended_preventive_action"),
            "verification_requirement": verif_req,
            "escalation_pathway_summary": escalation_result.get("what_could_happen"),
            "safety_restrictions": "ADVISORY ONLY: Agent does not operate equipment, valves, or process controls."
        }

        return {
            "report_id": report.id,
            "dataset_id": report.dataset_id,
            "action_type": action_type,
            "severity": sev,
            "title": title,
            "description": description,
            "assigned_role": assigned_role,
            "sla_hours": sla_hrs,
            "sla_deadline": sla_deadline,
            "action_package": package_data,
            "ai_recommendation": ai_recommendations,
            "status": "PENDING_APPROVAL",
            "approval_status": "PENDING",
            "created_at": datetime.utcnow()
        }

    @classmethod
    def generate_email_draft(cls, package: Dict[str, Any]) -> EmailDraftResponse:
        """
        Generates a context-aware email draft distinctly separating factual source data
        from AI-generated recommendations and precursor evaluations.
        """
        sev = package.get("severity") or (
            "CRITICAL" if package.get("ai_risk") == "Critical" else (
                "HIGH" if package.get("ai_risk") == "High" else "HIGH"
            )
        )
        unit = package.get("refinery_unit") or "Process Unit"
        equip = f" / {package.get('equipment')}" if package.get("equipment") else ""
        report_id = package.get("report_id", "N/A")
        sla_hrs = package.get("sla_hours", 24)
        role = package.get("responsible_role") or package.get("assigned_role", "Safety Officer")

        subject = f"{sev} SIF PRECURSOR — ACTION REQUIRED — UNIT {unit.upper()}{equip.upper()} [Report: {report_id}]"

        source_data = {
            "Report ID": report_id,
            "Refinery Unit": unit,
            "Equipment Tag": package.get("equipment") or "General Area",
            "Work Type": package.get("work_type") or "General Activity",
            "Recorded Risk Level": package.get("recorded_risk") or "Medium",
            "Observed Condition": package.get("observed_condition") or "Field safety observation",
            "Potential Consequence": package.get("potential_consequence") or "Potential physical exposure"
        }

        ai_recommendations = {
            "SIF Precursor Status": package.get("sif_status", "YES"),
            "Severity Level": sev,
            "Barrier Degradation Index (BDI)": f"{package.get('bdi_score', 0.0)} ({package.get('bdi_classification', 'MINIMAL')})",
            "Safety Factors": ", ".join(package.get("safety_factors", [])) if package.get("safety_factors") else "None",
            "Immediate Containment Recommendation": package.get("immediate_containment_recommendation", "Pause work and inspect barriers"),
            "Systemic Preventive Action": package.get("preventive_action", "Audit barrier controls"),
            "Mandatory Verification Requirement": package.get("verification_requirement", "Sign-off required"),
            "Responsible Role": role,
            "SLA Response Window": f"{sla_hrs} Hours"
        }

        body_text = f"""============================================================
SAFETY INTELLIGENCE PLATFORM — ACTION DISPATCH NOTIFICATION
============================================================
ALERT: A {sev} SIF Precursor has been identified. Please review the factual observation and execute required containment.

------------------------------------------------------------
SECTION 1: SOURCE DATA (OBSERVED FACTUAL RECORD)
------------------------------------------------------------
• Report ID:             {source_data['Report ID']}
• Refinery Unit:         {source_data['Refinery Unit']}
• Equipment Tag:         {source_data['Equipment Tag']}
• Work Type:             {source_data['Work Type']}
• Recorded Risk Level:   {source_data['Recorded Risk Level']}
• Observed Condition:    {source_data['Observed Condition']}
• Potential Consequence: {source_data['Potential Consequence']}

------------------------------------------------------------
SECTION 2: AI-GENERATED RECOMMENDATIONS & PRECURSORS
------------------------------------------------------------
• SIF Precursor Status:  {ai_recommendations['SIF Precursor Status']}
• Escalation Severity:   {ai_recommendations['Severity Level']}
• Barrier Degradation:   {ai_recommendations['Barrier Degradation Index (BDI)']}
• Contributing Factors:  {ai_recommendations['Safety Factors']}
• Immediate Containment: {ai_recommendations['Immediate Containment Recommendation']}
• Preventive Action:     {ai_recommendations['Systemic Preventive Action']}
• Required Verification: {ai_recommendations['Mandatory Verification Requirement']}
• Responsible Role:      {ai_recommendations['Responsible Role']}
• Containment SLA:       {ai_recommendations['SLA Response Window']}

------------------------------------------------------------
GOVERNANCE & SAFETY NOTICE:
This notification was formulated by the AI Safety Action Orchestrator for human safety review.
The AI does not directly operate refinery controls, valves, or machinery.
============================================================
"""

        body_html = f"""<div style="font-family: Arial, sans-serif; max-width: 650px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
    <div style="background-color: {'#DC2626' if sev == 'CRITICAL' else '#EA580C'}; color: white; padding: 16px 20px;">
        <h2 style="margin: 0; font-size: 18px;"> {sev} SIF PRECURSOR — ACTION REQUIRED</h2>
        <p style="margin: 4px 0 0 0; font-size: 14px;">Unit: <strong>{unit}</strong> | Equipment: <strong>{package.get('equipment') or 'General Area'}</strong></p>
    </div>
    <div style="padding: 20px;">
        <h3 style="color: #1E293B; border-bottom: 2px solid #E2E8F0; padding-bottom: 6px; margin-top: 0;">1. SOURCE DATA (OBSERVED FACTUAL RECORD)</h3>
        <table style="width: 100%; font-size: 14px; border-collapse: collapse; margin-bottom: 20px;">
            <tr><td style="padding: 6px 0; color: #64748B; width: 35%;">Report ID:</td><td style="font-weight: 600;">{source_data['Report ID']}</td></tr>
            <tr><td style="padding: 6px 0; color: #64748B;">Work Type:</td><td>{source_data['Work Type']}</td></tr>
            <tr><td style="padding: 6px 0; color: #64748B;">Recorded Risk:</td><td><span style="background: #F1F5F9; padding: 2px 8px; border-radius: 4px;">{source_data['Recorded Risk Level']}</span></td></tr>
            <tr><td style="padding: 6px 0; color: #64748B;">Observed Condition:</td><td>{source_data['Observed Condition']}</td></tr>
            <tr><td style="padding: 6px 0; color: #64748B;">Potential Consequence:</td><td style="color: #DC2626; font-weight: 600;">{source_data['Potential Consequence']}</td></tr>
        </table>

        <h3 style="color: #7C3AED; border-bottom: 2px solid #EDE9FE; padding-bottom: 6px;">2. AI-GENERATED RECOMMENDATIONS & PRECURSORS</h3>
        <table style="width: 100%; font-size: 14px; border-collapse: collapse;">
            <tr><td style="padding: 6px 0; color: #64748B; width: 35%;">SIF Precursor Status:</td><td><strong style="color: #DC2626;">{ai_recommendations['SIF Precursor Status']}</strong></td></tr>
            <tr><td style="padding: 6px 0; color: #64748B;">Barrier Degradation (BDI):</td><td>{ai_recommendations['Barrier Degradation Index (BDI)']}</td></tr>
            <tr><td style="padding: 6px 0; color: #64748B;">Contributing Factors:</td><td>{ai_recommendations['Safety Factors']}</td></tr>
            <tr><td style="padding: 6px 0; color: #64748B;">Immediate Containment:</td><td style="background: #FEF2F2; color: #991B1B; padding: 8px; border-radius: 4px; font-weight: 600;">{ai_recommendations['Immediate Containment Recommendation']}</td></tr>
            <tr><td style="padding: 6px 0; color: #64748B;">Preventive Action:</td><td>{ai_recommendations['Systemic Preventive Action']}</td></tr>
            <tr><td style="padding: 6px 0; color: #64748B;">Verification Requirement:</td><td>{ai_recommendations['Mandatory Verification Requirement']}</td></tr>
            <tr><td style="padding: 6px 0; color: #64748B;">Responsible Role:</td><td><strong>{ai_recommendations['Responsible Role']}</strong></td></tr>
            <tr><td style="padding: 6px 0; color: #64748B;">Response SLA:</td><td><strong style="color: #EA580C;">{ai_recommendations['SLA Response Window']}</strong></td></tr>
        </table>
    </div>
    <div style="background: #F8FAFC; padding: 12px 20px; font-size: 12px; color: #64748B; border-top: 1px solid #E2E8F0;">
         <em>Governance Note: Automated workflow draft prepared for human officer review. AI does not operate physical equipment or release permits.</em>
    </div>
</div>"""

        return EmailDraftResponse(
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            source_data_summary=source_data,
            ai_recommendations_summary=ai_recommendations,
            sla_deadline=package.get("sla_deadline"),
            assigned_role=role
        )

    @classmethod
    def generate_webhook_payload(cls, action_dict: Dict[str, Any], event_type: str = "ACTION_DISPATCHED") -> Tuple[Dict[str, Any], str]:
        """
        Constructs a sanitized webhook payload and generates an immutable SHA-256 hash for deduplication.
        """
        payload = {
            "event_type": event_type,
            "action_id": action_dict.get("id", "N/A"),
            "report_id": action_dict.get("report_id", "N/A"),
            "refinery_unit": action_dict.get("action_package", {}).get("refinery_unit") or "N/A",
            "equipment": action_dict.get("action_package", {}).get("equipment"),
            "severity": action_dict.get("severity", "HIGH"),
            "action_type": action_dict.get("action_type", "CONTAINMENT"),
            "assigned_role": action_dict.get("assigned_role", "Safety Officer"),
            "sla_hours": action_dict.get("sla_hours", 24),
            "status": action_dict.get("status", "DISPATCHED"),
            "immediate_containment": action_dict.get("action_package", {}).get("immediate_containment_recommendation"),
            "timestamp": datetime.utcnow().isoformat()
        }

        # Deterministic SHA-256 hash
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        payload_hash = hashlib.sha256(encoded).hexdigest()

        return payload, payload_hash
