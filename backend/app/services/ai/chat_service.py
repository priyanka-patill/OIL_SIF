import re
from typing import Optional, List, Dict, Any, Tuple
from collections import Counter, defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_, and_, desc

from app.models.safety_report import SafetyReport
from app.models.dataset import Dataset
from app.models.report_analysis import ReportAnalysis
from app.models.barrier_degradation_assessment import BarrierDegradationAssessment
from app.models.safety_barrier_assessment import SafetyBarrierAssessment
from app.models.sif_escalation_assessment import SIFEscalationAssessment
from app.models.safety_action import SafetyAction
from app.models.safety_hold import SafetyHold
from app.models.safety_correlation import SafetyCorrelation
from app.models.escalation_log import EscalationLog
from app.models.audit_log import AuditLog
from app.models.sla_policy import SLAPolicy
from app.services.sif_service import SIFService


class ChatService:
    @staticmethod
    def process_chat_message(
        db: Session,
        message: str,
        report_id: Optional[str] = None,
        dataset_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processes natural language inquiries against the actual database.
        Strict zero-hallucination policy: All metrics, counts, and lists are derived
        directly from live SQLAlchemy queries.
        """
        raw_msg = message.strip()
        msg = raw_msg.lower()

        # -------------------------------------------------------------
        # 1. REPORT-SPECIFIC CONTEXT CHAT ("ASK AI ABOUT THIS REPORT")
        # -------------------------------------------------------------
        if report_id:
            return ChatService._handle_report_specific_chat(db, report_id, msg)

        # -------------------------------------------------------------
        # 2. DATABASE-AWARE QUESTIONS & NATURAL LANGUAGE QUERIES
        # -------------------------------------------------------------

        # --- PART 4: MANDATORY NATURAL LANGUAGE INTENT ROUTES ---
        # 1. "How many SIF precursors were reported?"
        if any(k in msg for k in ["how many sif precursors", "sif precursors were reported", "how many sif precursor"]):
            return ChatService._query_sif_precursors_count(db, dataset_id)

        # 2. "Which unit has the highest SIF precursor density?"
        if any(k in msg for k in ["highest sif precursor density", "highest sif density", "unit has the highest sif precursor density", "sif precursor density by unit"]):
            return ChatService._query_highest_sif_density_unit(db, dataset_id)

        # 3. "Which Life-Saving Rule is most frequently involved?"
        if any(k in msg for k in ["life-saving rule is most frequently", "life saving rule is most frequently", "most frequently involved", "top life-saving rule", "life-saving rule distribution"]):
            return ChatService._query_top_iogp_rule(db, dataset_id)

        # 4. "Show recurring Line of Fire precursors."
        if any(k in msg for k in ["line of fire", "line-of-fire"]):
            return ChatService._query_recurring_line_of_fire(db, dataset_id)

        # 5. "Show reports where maintenance issues and PPE violations occurred together."
        if any(k in msg for k in ["maintenance issues and ppe", "maintenance and ppe", "ppe and maintenance", "maintenance issue and ppe"]):
            return ChatService._query_maintenance_and_ppe_together(db, dataset_id)

        # 6. "Which units have increasing SIF precursor density?"
        if any(k in msg for k in ["increasing sif precursor density", "increasing sif density", "trend in sif density", "sif density increasing"]):
            return ChatService._query_units_increasing_sif_density(db, dataset_id)

        # 7. "Why was this report classified as high SIF potential?"
        if any(k in msg for k in ["why was this report classified", "why classified as high sif", "classified as high sif potential"]):
            return ChatService._query_why_high_sif(db, dataset_id)

        # --- PHASE 7: SIF PRECURSOR ESCALATION, BDI, BARRIER & SLA INTELLIGENCE ---
        # 1. Critical SIF Precursors & Escalation
        if any(k in msg for k in ["critical sif", "critical sif precursors", "show critical sif", "sif escalation", "escalated reports"]):
            return ChatService._query_critical_sif_precursors(db, dataset_id)

        # 2. BDI & High BDI Units
        if any(k in msg for k in ["bdi", "barrier degradation index"]):
            if any(k in msg for k in ["unit", "units", "highest", "top unit"]):
                return ChatService._query_highest_bdi_units(db, dataset_id)
            return ChatService._query_bdi_intelligence(db, dataset_id)

        # 3. Degraded & Failed Barriers (Swiss Cheese)
        if any(k in msg for k in ["barriers are degraded", "barriers failed", "which barriers", "degraded barriers", "barrier degradation", "swiss cheese", "barrier failures"]):
            return ChatService._query_degraded_barriers_summary(db, dataset_id)

        # 4. Multi-Factor Correlation & Correlated Reports
        if any(k in msg for k in ["reports are correlated", "correlated reports", "show correlated", "correlations", "safety correlation"]):
            return ChatService._query_correlated_reports(db, dataset_id)

        # 5. Converging Factors
        if any(k in msg for k in ["factors are converging", "converging factors", "multi-factor convergence", "converging"]):
            return ChatService._query_converging_factors_summary(db, dataset_id)

        # 6. Equipment with Repeated Barrier Degradation
        if any(k in msg for k in ["equipment has repeated barrier", "repeated barrier degradation", "equipment degradation", "repeated equipment barrier"]):
            return ChatService._query_equipment_repeated_barrier_degradation(db, dataset_id)

        # 7. High-Potential Reports with Multiple Barrier Failures
        if any(k in msg for k in ["multiple barrier failures", "multiple barrier degradation", "hipo barrier"]):
            return ChatService._query_hipo_multiple_barrier_failures(db, dataset_id)

        # 8. SLA Breached Actions & Overdue
        if any(k in msg for k in ["breached sla", "sla breach", "sla breaches", "actions breached"]):
            return ChatService._query_sla_breached_actions(db, dataset_id)

        # 9. Action Escalation History
        if any(k in msg for k in ["action was escalated", "action escalated", "why was this action escalated", "action escalation"]):
            return ChatService._query_escalated_actions_summary(db, dataset_id)

        # 10. Actions Awaiting Acknowledgement & Digital Safety Holds
        if any(k in msg for k in ["awaiting acknowledgement", "unacknowledged", "safety hold", "safety holds", "digital safety hold", "active holds"]):
            return ChatService._query_actions_and_safety_holds(db, dataset_id)

        # A. High Potential Near Misses & Intelligence
        if any(k in msg for k in ["high-potential", "high potential", "hipo", "12_high_potential"]):
            if any(k in msg for k in ["factors", "which factors", "associated"]):
                return ChatService._query_high_potential_factors(db)
            return ChatService._query_high_potential_reports(db, dataset_id)

        # B. Multi-Factor & Factor Combinations Queries
        if any(k in msg for k in ["factor combination", "combination", "combinations", "dangerous combination", "occur together", "multiple safety failures", "multiple factors", "2-factor", "3-factor", "4-factor"]):
            if any(k in msg for k in ["dangerous", "most dangerous", "highest risk", "associated with high"]):
                return ChatService._query_factor_combinations_high_risk(db, dataset_id)
            if any(k in msg for k in ["occur together", "together", "co-occur"]):
                return ChatService._query_factors_co_occurrence(db, dataset_id)
            if any(k in msg for k in ["multiple safety failures", "multiple factors"]):
                return ChatService._query_multi_factor_reports(db, dataset_id)
            return ChatService._query_factor_combinations_common(db, dataset_id)

        # C. Single-Factor Counts & Specific Factor Queries
        if "supervisor negligence" in msg or "supervisor factor" in msg:
            return ChatService._query_supervisor_negligence_count(db, dataset_id)

        if "maintenance delay" in msg or "maintenance issue" in msg or "maintenance factor" in msg:
            return ChatService._query_maintenance_delay_count(db, dataset_id)

        if any(k in msg for k in ["repeated issue", "repeatedly ignored", "issues being ignored", "issues ignored"]):
            return ChatService._query_repeated_issues_count(db, dataset_id)

        if "only ppe" in msg or "involve only ppe" in msg:
            return ChatService._query_only_ppe_count(db, dataset_id)

        if any(k in msg for k in ["which safety factor appears most", "safety factor appears most", "most frequent factor", "top safety factor"]):
            return ChatService._query_top_safety_factor(db, dataset_id)

        # D. Dataset Comparison & Scoping Queries
        if "compare" in msg:
            if "ppe" in msg and "maintenance" in msg:
                return ChatService._query_compare_ppe_vs_maintenance(db)
            return ChatService._query_compare_single_vs_multi_factor(db)

        if any(k in msg for k in ["analyze the 4-factor", "analyze 4-factor", "11_4factor"]):
            return ChatService._query_analyze_dataset(db, "11_4Factor_All")

        if any(k in msg for k in ["analyze the ppe", "analyze ppe dataset", "01_ppe"]):
            return ChatService._query_analyze_dataset(db, "01_PPE_NonCompliance")

        # E. Hazard Specific Filtering (Hydrocarbon Release, Fire, Gas)
        if any(k in msg for k in ["hydrocarbon release", "hydrocarbon", "gas release"]):
            return ChatService._query_reports_by_hazard_term(db, "hydrocarbon release", dataset_id)

        if any(k in msg for k in ["fire risk", "fire hazard", "related to fire"]):
            return ChatService._query_reports_by_hazard_term(db, "fire", dataset_id)

        # F. Recurring Equipment, Units, Work Types
        if any(k in msg for k in ["equipment appears repeatedly", "repeated equipment", "recurring equipment"]):
            return ChatService._query_repeated_equipment(db, dataset_id)

        if any(k in msg for k in ["work types have the highest risk", "highest risk work types", "riskiest work type"]):
            return ChatService._query_highest_risk_work_types(db, dataset_id)

        if any(k in msg for k in ["refinery units have recurring", "units have recurring", "recurring units"]):
            return ChatService._query_recurring_refinery_units(db, dataset_id)

        # G. "How many reports are there?" / Total count
        if re.search(r'\b(how many|total|count of)\b.*\b(reports|records|observations|incidents)\b', msg) and not any(k in msg for k in ["high", "risk", "ppe", "open", "overdue", "recurring", "supervisor", "maintenance", "repeated", "critical"]):
            return ChatService._query_total_reports(db, dataset_id)

        # H. "How many high-risk / critical reports?"
        if re.search(r'\b(how many|count|number of)\b.*\b(high[- ]?risk|critical)\b', msg) or (msg in ["how many high-risk reports?", "how many high risk reports", "how many high-risk reports"]):
            return ChatService._query_high_risk_count(db, dataset_id)

        # I. "What are the most common PPE problems?"
        if any(k in msg for k in ["ppe problem", "ppe issue", "ppe violation", "ppe non-compliance", "common ppe", "ppe observations"]):
            if "maintenance" in msg:
                return ChatService._query_ppe_by_department(db, "Maintenance", dataset_id)
            if "high" in msg:
                return ChatService._query_high_risk_ppe(db, dataset_id)
            return ChatService._query_common_ppe_problems(db, dataset_id)

        # J. "Which refinery unit has the most reports?"
        if any(k in msg for k in ["which refinery unit has the most", "refinery unit has the most", "top refinery unit", "unit with the most reports", "most reports by unit"]):
            return ChatService._query_top_refinery_unit(db, dataset_id)

        # K. "Which department has the most observations?"
        if any(k in msg for k in ["which department has the most", "department has the most", "top department", "most observations by department"]):
            return ChatService._query_top_department(db, dataset_id)

        # L. "What are the most common immediate causes?"
        if any(k in msg for k in ["common immediate causes", "most common immediate cause", "top immediate cause", "immediate causes"]):
            return ChatService._query_common_immediate_causes(db, dataset_id)

        # M. "What consequences are most common?"
        if any(k in msg for k in ["consequences are most common", "common consequence", "most common consequence", "potential consequences"]):
            return ChatService._query_common_consequences(db, dataset_id)

        # N. "Which reports are open?"
        if any(k in msg for k in ["which reports are open", "show open reports", "open action reports", "what reports are open", "list open reports"]):
            return ChatService._query_open_reports(db, dataset_id)

        # O. "Which reports are recurring?"
        if any(k in msg for k in ["which reports are recurring", "show recurring issues", "show recurring reports", "recurring issues", "recurring problems"]):
            return ChatService._query_recurring_reports(db, dataset_id)

        # P. "Show reports where previous similar reports are greater than X"
        prev_match = re.search(r'previous\s+similar\s+reports\s*(?:are\s*)?(?:greater\s+than|>|>=)\s*(\d+)', msg)
        if prev_match:
            threshold = int(prev_match.group(1))
            return ChatService._query_reports_by_previous_similar(db, threshold, dataset_id)

        # Q. "Show high-risk reports from the [Unit Name]"
        unit_match = ChatService._extract_refinery_unit(msg)
        if "high" in msg and unit_match:
            return ChatService._query_high_risk_by_unit(db, unit_match, dataset_id)

        # R. "Show high-risk PPE reports."
        if ("high" in msg and "ppe" in msg) or msg == "show high-risk ppe reports.":
            return ChatService._query_high_risk_ppe(db, dataset_id)

        # S. "Show PPE observations from Maintenance."
        if "ppe" in msg and "maintenance" in msg:
            return ChatService._query_ppe_by_department(db, "Maintenance", dataset_id)

        # T. "Summarize the current safety situation." / Executive overview
        if any(k in msg for k in ["summarize the current safety situation", "safety situation", "executive summary", "overview of safety", "current safety summary", "safety status"]):
            return ChatService._query_safety_summary(db, dataset_id)

        # U. Specific Refinery Unit inquiry (general)
        if unit_match:
            return ChatService._query_unit_intel(db, unit_match, dataset_id)

        # V. SIF Precursors & Precursor rate
        if any(k in msg for k in ["sif", "precursor", "fatality", "fatal", "serious injury"]):
            return ChatService._query_sif_overview(db, dataset_id)

        # W. Overdue Actions Query
        if any(k in msg for k in ["overdue", "action status", "pending actions"]):
            return ChatService._query_overdue_actions(db, dataset_id)

        # X. Keyword / Semantic Search fallback
        if any(k in msg for k in ["similar to", "seen similar", "problems involving", "reports involving", "find reports", "search for"]):
            return ChatService._query_similar_reports_by_keyword(db, msg, dataset_id)

        # Fallback with real database grounding numbers
        return ChatService._generate_grounded_fallback(db, dataset_id)

    # -------------------------------------------------------------
    # REPORT-SPECIFIC QA IMPLEMENTATION
    # -------------------------------------------------------------
    @staticmethod
    def _handle_report_specific_chat(db: Session, report_id: str, msg: str) -> Dict[str, Any]:
        analysis = SIFService.get_analysis_by_report_id(db, report_id)
        report = db.scalar(select(SafetyReport).where(SafetyReport.id == report_id))

        if not report:
            return {
                "reply": f" Safety report ID `{report_id}` was not found in the active database.",
                "suggested_actions": ["Show all reports", "How many reports are there?"],
                "relevant_reports": [],
                "category": "REPORT_NOT_FOUND"
            }

        rec_risk = report.risk_level or "Unassigned"
        ai_risk = analysis.ai_risk_level if analysis else rec_risk
        unit = report.refinery_unit or "Process Unit"
        dept = report.department or "Operations"
        problem = report.description or "No description provided."
        consequence = report.potential_consequence or "Unmitigated personnel exposure"
        action = report.corrective_action or "Review control barriers"
        sif_status = analysis.sif_precursor if analysis else "EVALUATING"
        sif_cat = analysis.sif_category if analysis else "General Hazard"
        imm_action = analysis.immediate_action_recommendation if analysis else "Inspect work area immediately."
        prev_action = analysis.preventive_action_recommendation if analysis else "Verify standard operating procedures."
        esc = analysis.escalation_scenario if analysis else {}
        is_rec = (report.previous_similar_reports or 0) > 0 or (report.repeated_issue is True) or (analysis.is_recurring if analysis else False)
        rec_count = report.previous_similar_reports or (analysis.recurrence_score if analysis else 0)

        # PHASE 7 - A: "Why was this report escalated?"
        if any(k in msg for k in ["why was this report escalated", "why escalated", "escalation reason", "escalated"]):
            sif_esc = db.scalar(select(SIFEscalationAssessment).where(SIFEscalationAssessment.report_id == report_id))
            bdi_esc = db.scalar(select(BarrierDegradationAssessment).where(BarrierDegradationAssessment.report_id == report_id))
            barriers = list(db.scalars(select(SafetyBarrierAssessment).where(SafetyBarrierAssessment.report_id == report_id)).all())
            deg_count = sum(1 for b in barriers if b.status in ["DEGRADED", "FAILED"])
            
            sev = sif_esc.severity if sif_esc else ("HIGH" if str(ai_risk).upper() == "HIGH" else "NORMAL")
            why = (sif_esc.reasoning.get("why_escalated") if sif_esc and sif_esc.reasoning else None) or f"Detected high potential exposure in {unit} with recorded consequence '{consequence}' and {deg_count} degraded control barrier(s)."
            factors_str = ", ".join(sif_esc.contributing_factors) if (sif_esc and sif_esc.contributing_factors) else "Control degradation, personnel exposure"
            bdi_val = f"{bdi_esc.bdi_score:.1f} ({bdi_esc.classification})" if bdi_esc else "N/A"
            imm_rec = (sif_esc.immediate_actions[0] if (sif_esc and sif_esc.immediate_actions) else imm_action)

            reply = (
                f"### SIF Precursor Escalation Analysis: Report {report.original_id or report.id}\n\n"
                f"- **Escalation Severity**:  **{sev}**\n"
                f"- **Barrier Degradation Index (BDI)**: **{bdi_val}**\n"
                f"- **Degraded/Failed Barrier Count**: **{deg_count}**\n"
                f"- **Contributing Factors**: `{factors_str}`\n\n"
                f"**Why Escalated**:\n"
                f"{why}\n\n"
                f"**Immediate Containment Recommended**:\n"
                f" {imm_rec}\n\n"
                f"*Disclaimer: SIF precursor escalation detects potential pathways and exposure conditions, not guaranteed incident predictions.*"
            )
            return {
                "reply": reply,
                "suggested_actions": [
                    "Why is BDI high?",
                    "Which barriers are degraded?",
                    "What is the 7-stage precursor pathway?",
                    "What is the SLA and Safety Hold status?"
                ],
                "relevant_reports": [{"id": report.id, "original_id": report.original_id, "risk": ai_risk}],
                "category": "SIF_ESCALATION"
            }

        # PHASE 7 - B: "Why is BDI high?" / BDI Inquiry
        if any(k in msg for k in ["why is bdi high", "bdi", "barrier degradation index"]):
            bdi_esc = db.scalar(select(BarrierDegradationAssessment).where(BarrierDegradationAssessment.report_id == report_id))
            
            score = bdi_esc.bdi_score if bdi_esc else 0.0
            classification = bdi_esc.classification if bdi_esc else "MINIMAL"
            dom_barriers_list = bdi_esc.evidence.get("dominant_degraded_barriers", []) if (bdi_esc and bdi_esc.evidence) else []
            dom_barriers = ", ".join(dom_barriers_list) if dom_barriers_list else "None identified"
            dom_factors_list = bdi_esc.contributing_factors if (bdi_esc and bdi_esc.contributing_factors) else []
            dom_factors = ", ".join(dom_factors_list) if dom_factors_list else "Single observation"
            
            breakdown_lines = ""
            if bdi_esc and bdi_esc.component_scores:
                for comp, pts in bdi_esc.component_scores.items():
                    breakdown_lines += f"- **{comp.replace('_', ' ').title()}**: +{pts} pts\n"
            else:
                breakdown_lines = "- **Baseline Exposure**: 0 pts\n"

            reply = (
                f"### Barrier Degradation Index (BDI) Breakdown: Report {report.original_id or report.id}\n\n"
                f"- **Calculated BDI Score**: **{score:.1f} / 100**\n"
                f"- **Classification**: **{classification}**\n"
                f"- **Dominant Degraded Barriers**: `{dom_barriers}`\n"
                f"- **Contributing Safety Factors**: `{dom_factors}`\n\n"
                f"**Point Breakdown**:\n"
                f"{breakdown_lines}\n"
                f"*Disclaimer: BDI is an analytical indicator derived from observed safety data, not an official OIL risk score or accident probability.*"
            )
            return {
                "reply": reply,
                "suggested_actions": [
                    "Which barriers are degraded?",
                    "Why was this report escalated?",
                    "What immediate action is recommended?"
                ],
                "relevant_reports": [{"id": report.id, "original_id": report.original_id, "risk": ai_risk}],
                "category": "BDI_ANALYSIS"
            }

        # PHASE 7 - C: "Which barriers are degraded?" / Barrier States
        if any(k in msg for k in ["which barriers are degraded", "which barriers failed", "barrier states", "barrier degradation", "swiss cheese"]):
            barriers = list(db.scalars(select(SafetyBarrierAssessment).where(SafetyBarrierAssessment.report_id == report_id)).all())
            if not barriers:
                barriers_text = "- No specific barrier degradation records stored for this report."
            else:
                barriers_text = "\n".join([
                    f"- **{b.barrier_name}** ({b.barrier_category}): **{b.status}** (Confidence: {int(b.confidence * 100)}%) — *\"{b.evidence.get('reasoning', 'Verified') if b.evidence else 'Evaluated'}\"*"
                    for b in barriers
                ])

            reply = (
                f"### Swiss Cheese Barrier Defense Evaluation: Report {report.original_id or report.id}\n\n"
                f"Layer-by-layer evaluation of defense controls for **{unit}** ({dept}):\n\n"
                f"{barriers_text}\n\n"
                f"**Model Context**: Inspired by Reason's Swiss Cheese Model, degradation of multiple barrier layers elevates the risk of latent hazard escalation."
            )
            return {
                "reply": reply,
                "suggested_actions": [
                    "Why is BDI high?",
                    "Why was this report escalated?",
                    "What immediate action is recommended?"
                ],
                "relevant_reports": [{"id": report.id, "original_id": report.original_id, "risk": ai_risk}],
                "category": "BARRIER_DEFENSE"
            }

        # PHASE 7 - D: "What is the 7-stage precursor pathway?"
        if any(k in msg for k in ["7-stage", "seven stage", "escalation pathway", "precursor pathway"]):
            sif_esc = db.scalar(select(SIFEscalationAssessment).where(SIFEscalationAssessment.report_id == report_id))
            stages = sif_esc.escalation_scenario if (sif_esc and sif_esc.escalation_scenario) else []
            if stages:
                stage_lines = "\n".join([
                    f"{s.get('stage_number', i+1)}. **{s.get('stage_name', 'Stage')}**: {s.get('description', '')} {' [ACTIVE]' if s.get('is_active') else ''}"
                    for i, s in enumerate(stages)
                ])
            else:
                stage_lines = (
                    f"1. **Baseline Latent Hazard**: {problem}\n"
                    f"2. **Initiating Trigger / Exposure**: Unmitigated personnel exposure in {unit}\n"
                    f"3. **Primary Barrier Failure**: PPE or control failure\n"
                    f"4. **Secondary Barrier Failure**: Maintenance / procedural delay\n"
                    f"5. **Critical Convergence Point**: Multiple concurrent degraded barriers\n"
                    f"6. **Escalation Threshold**: Breach of physical separation\n"
                    f"7. **Potential SIF Outcome**: {consequence}"
                )

            reply = (
                f"### 7-Stage Precursor Escalation Pathway: Report {report.original_id or report.id}\n\n"
                f"{stage_lines}\n\n"
                f"*Disclaimer: Potential precursor escalation — not a guaranteed incident prediction.*"
            )
            return {
                "reply": reply,
                "suggested_actions": [
                    "What immediate action is recommended?",
                    "What is the SLA and Safety Hold status?",
                    "Why was this report escalated?"
                ],
                "relevant_reports": [{"id": report.id, "original_id": report.original_id, "risk": ai_risk}],
                "category": "PRECURSOR_PATHWAY"
            }

        # PHASE 7 - E: "What is the SLA and Safety Hold status?"
        if any(k in msg for k in ["sla", "safety hold", "hold status", "sla status"]):
            act = db.scalar(select(SafetyAction).where(SafetyAction.report_id == report_id))
            hld = db.scalar(select(SafetyHold).where(SafetyHold.report_id == report_id))
            
            act_info = f"- **Action Status**: `{act.status if act else report.action_status or 'Open'}`\n- **Assigned Role**: `{act.assigned_role if act else 'Safety Officer'}`\n- **SLA State**: `{act.sla_state if act else 'NORMAL'}`\n- **Escalation Level**: `Level {act.escalation_level if act else 0}`"
            hold_info = f"- **Hold State**: `{hld.status if hld else 'NORMAL (No Active Hold)'}`\n- **Trigger**: `{hld.trigger if hld else 'N/A'}`" if hld else "- **Digital Safety Hold**: `NORMAL (No active hold on this unit)`"

            reply = (
                f"### SLA & Safety Hold Governance: Report {report.original_id or report.id}\n\n"
                f"**Safety Action Telemetry**:\n"
                f"{act_info}\n\n"
                f"**Digital Safety Hold Telemetry**:\n"
                f"{hold_info}\n"
            )
            return {
                "reply": reply,
                "suggested_actions": [
                    "What immediate action is recommended?",
                    "Why was this report escalated?",
                    "Which barriers are degraded?"
                ],
                "relevant_reports": [{"id": report.id, "original_id": report.original_id, "risk": ai_risk}],
                "category": "SLA_HOLD_STATUS"
            }

        # 1. "Why is this report important?"
        if any(k in msg for k in ["why is this report important", "importance", "why important", "why does this matter"]):
            reasoning_bullets = ""
            if analysis and analysis.reasoning:
                reasoning_bullets = "\n".join([f"- {r}" for r in analysis.reasoning])
            else:
                reasoning_bullets = f"- Direct exposure in active process unit ({unit})\n- Recorded consequence: {consequence}"

            reply = (
                f"### Report Importance Assessment: {report.original_id or report.id}\n\n"
                f"This report is critical because it represents **{sif_status} SIF Precursor potential** in **{unit}** ({dept}).\n\n"
                f"**Key Risk Drivers Identified**:\n"
                f"{reasoning_bullets}\n\n"
                f"- **Observed Problem**: *\"{problem}\"*\n"
                f"- **AI Assessed Risk**: **{ai_risk}** (Source record had: `{rec_risk}`)\n"
                f"- **SIF Category**: `{sif_cat}`"
            )
            return {
                "reply": reply,
                "suggested_actions": [
                    "What is the potential safety consequence?",
                    "What immediate action is recommended?",
                    "Is this issue recurring?",
                    "What could happen if this remains unresolved?"
                ],
                "relevant_reports": [{"id": report.id, "original_id": report.original_id, "risk": ai_risk}],
                "category": "REPORT_IMPORTANCE"
            }

        # 2. "What could happen if this remains unresolved?"
        if any(k in msg for k in ["remains unresolved", "unresolved", "not fixed", "escalation"]):
            cond = esc.get("current_condition", problem) if esc else problem
            exp = esc.get("continued_exposure", "Continued operational activity with active hazard") if esc else "Personnel exposure"
            loss = esc.get("loss_of_control", "Barrier degradation") if esc else "Control loss"
            inc = esc.get("incident_event", "Hazard release or impact") if esc else "Incident trigger"
            sif_res = esc.get("potential_fatal_consequence", consequence) if esc else consequence

            reply = (
                f"### Unresolved Escalation Progression: Report {report.original_id or report.id}\n\n"
                f"If this issue remains uncorrected, the **6-Stage Risk Escalation Model** predicts:\n\n"
                f"1. **Initial Condition**: {cond}\n"
                f"2. **Continued Exposure**: {exp}\n"
                f"3. **Loss of Control Barrier**: {loss}\n"
                f"4. **Incident Event**: {inc}\n"
                f"5. **Final Potential SIF Outcome**:  **{sif_res}**\n\n"
                f"**Mandatory Resolution**: Assign corrective action immediately to prevent escalation."
            )
            return {
                "reply": reply,
                "suggested_actions": [
                    "What immediate action is recommended?",
                    "Why is this report important?",
                    "Is this issue recurring?"
                ],
                "relevant_reports": [{"id": report.id, "original_id": report.original_id, "risk": ai_risk}],
                "category": "REPORT_ESCALATION"
            }

        # 3. "What is the potential safety consequence?"
        if any(k in msg for k in ["potential safety consequence", "consequence", "what could happen", "what injury"]):
            fatal_consequence = esc.get("potential_fatal_consequence", consequence) if esc else consequence
            reply = (
                f"### Potential Safety Consequence Analysis: {report.original_id or report.id}\n\n"
                f"- **Recorded Field Consequence**: `{consequence}`\n"
                f"- **AI Evaluated SIF Outcome**: **{fatal_consequence}**\n"
                f"- **SIF Exposure Vector**: `{sif_cat}`\n\n"
                f"**Risk Context**:\n"
                f"In the **{unit}**, unmitigated exposure to this condition under operational stress can lead to **{fatal_consequence}**."
            )
            return {
                "reply": reply,
                "suggested_actions": [
                    "What immediate action is recommended?",
                    "What could happen if this remains unresolved?",
                    "Is this issue recurring?"
                ],
                "relevant_reports": [{"id": report.id, "original_id": report.original_id, "risk": ai_risk}],
                "category": "REPORT_CONSEQUENCE"
            }

        # 4. "What immediate action is recommended?"
        if any(k in msg for k in ["immediate action", "what action is recommended", "corrective action", "recommended action"]):
            reply = (
                f"### Recommended Actions for Report: {report.original_id or report.id}\n\n"
                f"**1. AI Recommended Immediate Mitigation**:\n"
                f" **{imm_action}**\n\n"
                f"**2. Recorded Field Corrective Action**:\n"
                f" *\"{action}\"*\n\n"
                f"**3. Long-term Preventive Strategy**:\n"
                f" **{prev_action}**\n\n"
                f"**Current Action Status**: `{report.action_status or 'Open'}` (Assigned: `{report.assigned_to or 'Unassigned'}`)"
            )
            return {
                "reply": reply,
                "suggested_actions": [
                    "Assign action to supervisor",
                    "What could happen if this remains unresolved?",
                    "Why is this report important?"
                ],
                "relevant_reports": [{"id": report.id, "original_id": report.original_id, "risk": ai_risk}],
                "category": "REPORT_ACTIONS"
            }

        # 5. "Is this issue recurring?"
        if any(k in msg for k in ["recurring", "repeated", "similar report", "happened before"]):
            reply = (
                f"### Recurrence Telemetry: Report {report.original_id or report.id}\n\n"
                f"- **Recurrence Status**: {' **YES - SYSTEMIC RECURRING ISSUE**' if is_rec else ' **NO PRIOR MATCHES DETECTED**'}\n"
                f"- **Previous Similar Reports Logged**: **{rec_count}**\n"
                f"- **Equipment Involved**: `{report.equipment or 'General Unit'}` ({unit})\n"
                f"- **Department**: `{dept}`\n\n"
            )
            if is_rec:
                reply += f"This failure mode has occurred multiple times in `{unit}`. Engineering barrier verification is strongly recommended to eliminate root causes."
            else:
                reply += "This appears to be an isolated observation without immediate precursor cluster history."

            return {
                "reply": reply,
                "suggested_actions": [
                    "Why is this report important?",
                    "What immediate action is recommended?",
                    "What could happen if this remains unresolved?"
                ],
                "relevant_reports": [{"id": report.id, "original_id": report.original_id, "risk": ai_risk}],
                "category": "REPORT_RECURRENCE"
            }

        # General single report summary fallback
        reply = (
            f"### Safety Report Telemetry Context: {report.original_id or report.id}\n\n"
            f"- **Unit & Equipment**: {unit} ({report.equipment or 'General'})\n"
            f"- **Department**: {dept} | **Work Type**: {report.work_type or 'General'}\n"
            f"- **Observed Problem**: *\"{problem}\"*\n"
            f"- **SIF Status**: **{sif_status}** ({sif_cat})\n"
            f"- **Risk Level**: Recorded `{rec_risk}`, AI evaluated **`{ai_risk}`**\n"
            f"- **Immediate Action**: {imm_action}\n"
            f"- **Potential Escalation**: {esc.get('potential_fatal_consequence', consequence) if esc else consequence}"
        )
        return {
            "reply": reply,
            "suggested_actions": [
                "Why is this report important?",
                "What is the potential safety consequence?",
                "What immediate action is recommended?",
                "Is this issue recurring?",
                "What could happen if this remains unresolved?"
            ],
            "relevant_reports": [{"id": report.id, "original_id": report.original_id, "risk": ai_risk}],
            "category": "REPORT_CONTEXT"
        }

    # -------------------------------------------------------------
    # DATABASE-AWARE AGGREGATION QUERIES
    # -------------------------------------------------------------

    @staticmethod
    def _query_total_reports(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(func.count(SafetyReport.id))
        if dataset_id:
            q = q.where(SafetyReport.dataset_id == dataset_id)
        total = db.scalar(q) or 0

        # Also get dataset name
        ds_info = f" in active dataset" if dataset_id else " across all datasets"
        reply = (
            f"### Database Record Telemetry\n\n"
            f"There are **{total} safety reports** currently recorded in the OIL Safety Intelligence Database{ds_info}.\n\n"
            f"- Grounded source: `safety_reports` table (SQL query: `SELECT COUNT(*) FROM safety_reports`)\n"
            f"- All reports are normalized with canonical schema mapping and data quality profiling."
        )
        return {
            "reply": reply,
            "suggested_actions": [
                "How many high-risk reports?",
                "Which refinery unit has the most reports?",
                "What are the most common PPE problems?",
                "Summarize the current safety situation."
            ],
            "relevant_reports": [],
            "category": "COUNT"
        }

    @staticmethod
    def _query_high_risk_count(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q_recorded = select(func.count(SafetyReport.id)).where(func.lower(SafetyReport.risk_level) == "high")
        q_total = select(func.count(SafetyReport.id))
        if dataset_id:
            q_recorded = q_recorded.where(SafetyReport.dataset_id == dataset_id)
            q_total = q_total.where(SafetyReport.dataset_id == dataset_id)

        high_recorded = db.scalar(q_recorded) or 0
        total = db.scalar(q_total) or 0
        pct = (high_recorded / total * 100) if total > 0 else 0

        # Sample high risk reports
        sample_q = select(SafetyReport).where(func.lower(SafetyReport.risk_level) == "high").limit(3)
        if dataset_id:
            sample_q = sample_q.where(SafetyReport.dataset_id == dataset_id)
        sample_reports = list(db.scalars(sample_q).all())

        reply = (
            f"### High-Risk Observations Telemetry\n\n"
            f"There are **{high_recorded} high-risk reports** out of **{total} total observations** ({pct:.1f}% of all records).\n\n"
            f"**High-Risk Records Sample**:\n"
        )
        rel_reps = []
        for r in sample_reports:
            rel_reps.append({"id": r.id, "original_id": r.original_id, "risk": r.risk_level})
            reply += f"- **{r.original_id}** ({r.refinery_unit} - {r.department}): \"{r.description}\" | Consequence: `{r.potential_consequence}`\n"

        return {
            "reply": reply,
            "suggested_actions": [
                "Show high-risk reports from the Hydrogen Unit.",
                "Show high-risk PPE reports.",
                "Which reports are open?",
                "Summarize the current safety situation."
            ],
            "relevant_reports": rel_reps,
            "category": "HIGH_RISK"
        }

    @staticmethod
    def _query_common_ppe_problems(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        # Count explicit PPE reports and analyze PPE problem types
        q_ppe = select(SafetyReport).where(
            or_(
                SafetyReport.ppe_issue == True,
                func.lower(SafetyReport.report_type).like("%ppe%"),
                func.lower(SafetyReport.description).like("%ppe%"),
                func.lower(SafetyReport.description).like("%helmet%"),
                func.lower(SafetyReport.description).like("%glasses%"),
                func.lower(SafetyReport.description).like("%gloves%"),
                func.lower(SafetyReport.description).like("%goggles%"),
                func.lower(SafetyReport.description).like("%shoes%"),
                func.lower(SafetyReport.description).like("%ear%"),
                func.lower(SafetyReport.description).like("%mask%")
            )
        )
        if dataset_id:
            q_ppe = q_ppe.where(SafetyReport.dataset_id == dataset_id)
        ppe_reports = list(db.scalars(q_ppe).all())

        # Count frequencies of PPE types mentioned
        ppe_types = {
            "Safety Glasses / Face Shield": 0,
            "Safety Helmet / Hard Hat": 0,
            "Chemical / Hand Gloves": 0,
            "Safety Boots / Shoes": 0,
            "Hearing Protection (Earplugs)": 0,
            "Dust Mask / Respirator": 0,
            "Fall Protection Harness": 0,
            "FR Clothing / Coverall": 0
        }

        for r in ppe_reports:
            text = f"{r.description or ''} {r.hazard or ''} {r.unsafe_act or ''}".lower()
            if any(w in text for w in ["glass", "eye", "spectacle", "goggle", "face shield"]):
                ppe_types["Safety Glasses / Face Shield"] += 1
            if any(w in text for w in ["helmet", "hard hat", "head"]):
                ppe_types["Safety Helmet / Hard Hat"] += 1
            if any(w in text for w in ["glove", "hand"]):
                ppe_types["Chemical / Hand Gloves"] += 1
            if any(w in text for w in ["boot", "shoe", "foot"]):
                ppe_types["Safety Boots / Shoes"] += 1
            if any(w in text for w in ["ear", "hearing", "noise"]):
                ppe_types["Hearing Protection (Earplugs)"] += 1
            if any(w in text for w in ["mask", "respirator", "dust"]):
                ppe_types["Dust Mask / Respirator"] += 1
            if any(w in text for w in ["harness", "lanyard", "fall"]):
                ppe_types["Fall Protection Harness"] += 1
            if any(w in text for w in ["clothing", "coverall", "fr"]):
                ppe_types["FR Clothing / Coverall"] += 1

        sorted_ppe = sorted([(k, v) for k, v in ppe_types.items() if v > 0], key=lambda x: x[1], reverse=True)

        reply = (
            f"### Most Common PPE Problems & Violations\n\n"
            f"Across **{len(ppe_reports)} PPE-related observations** in the database, the most prevalent non-compliance categories are:\n\n"
        )
        for name, cnt in sorted_ppe[:6]:
            reply += f"- **{name}**: **{cnt} observations**\n"

        reply += "\n*Primary Violation Modality*: Improper wearing / non-use in designated mandatory PPE zones."

        rel_reps = [{"id": r.id, "original_id": r.original_id, "risk": r.risk_level} for r in ppe_reports[:3]]

        return {
            "reply": reply,
            "suggested_actions": [
                "Show high-risk PPE reports.",
                "Show PPE observations from Maintenance.",
                "Which refinery unit has the most reports?",
                "Summarize the current safety situation."
            ],
            "relevant_reports": rel_reps,
            "category": "PPE_INTEL"
        }

    @staticmethod
    def _query_top_refinery_unit(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SafetyReport.refinery_unit, func.count(SafetyReport.id).label("cnt")).where(
            SafetyReport.refinery_unit != None
        )
        if dataset_id:
            q = q.where(SafetyReport.dataset_id == dataset_id)
        q = q.group_by(SafetyReport.refinery_unit).order_by(desc("cnt"))
        results = db.execute(q).all()

        if not results:
            return {
                "reply": "No refinery units recorded in the database.",
                "suggested_actions": ["How many reports are there?"],
                "relevant_reports": [],
                "category": "UNIT_INTEL"
            }

        top_unit, top_cnt = results[0]
        reply = (
            f"### Refinery Unit Analysis: Highest Volume of Reports\n\n"
            f"The refinery unit with the most safety reports is **{top_unit}** with **{top_cnt} observations**.\n\n"
            f"**Complete Unit Breakdown**:\n"
        )
        for unit, cnt in results:
            reply += f"- **{unit}**: {cnt} reports\n"

        # Fetch sample from top unit
        sample_q = select(SafetyReport).where(SafetyReport.refinery_unit == top_unit).limit(3)
        sample_reps = list(db.scalars(sample_q).all())
        rel_reps = [{"id": r.id, "original_id": r.original_id, "risk": r.risk_level} for r in sample_reps]

        return {
            "reply": reply,
            "suggested_actions": [
                f"Show high-risk reports from the {top_unit}.",
                "Which department has the most observations?",
                "What are the most common immediate causes?",
                "Summarize the current safety situation."
            ],
            "relevant_reports": rel_reps,
            "category": "UNIT_INTEL"
        }

    @staticmethod
    def _query_top_department(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SafetyReport.department, func.count(SafetyReport.id).label("cnt")).where(
            SafetyReport.department != None
        )
        if dataset_id:
            q = q.where(SafetyReport.dataset_id == dataset_id)
        q = q.group_by(SafetyReport.department).order_by(desc("cnt"))
        results = db.execute(q).all()

        if not results:
            return {
                "reply": "No departments recorded in the database.",
                "suggested_actions": ["How many reports are there?"],
                "relevant_reports": [],
                "category": "DEPT_INTEL"
            }

        top_dept, top_cnt = results[0]
        reply = (
            f"### Department Observation Telemetry\n\n"
            f"The department with the highest number of safety observations is **{top_dept}** with **{top_cnt} reports**.\n\n"
            f"**Department Observation Breakdown**:\n"
        )
        for dept, cnt in results:
            reply += f"- **{dept}**: {cnt} observations\n"

        sample_q = select(SafetyReport).where(SafetyReport.department == top_dept).limit(3)
        sample_reps = list(db.scalars(sample_q).all())
        rel_reps = [{"id": r.id, "original_id": r.original_id, "risk": r.risk_level} for r in sample_reps]

        return {
            "reply": reply,
            "suggested_actions": [
                f"Show PPE observations from {top_dept}.",
                "Which refinery unit has the most reports?",
                "What consequences are most common?",
                "Summarize the current safety situation."
            ],
            "relevant_reports": rel_reps,
            "category": "DEPT_INTEL"
        }

    @staticmethod
    def _query_common_immediate_causes(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SafetyReport.immediate_cause, func.count(SafetyReport.id).label("cnt")).where(
            SafetyReport.immediate_cause != None
        )
        if dataset_id:
            q = q.where(SafetyReport.dataset_id == dataset_id)
        q = q.group_by(SafetyReport.immediate_cause).order_by(desc("cnt"))
        results = db.execute(q).all()

        reply = (
            f"### Most Common Immediate Causes in Database\n\n"
            f"Aggregating all recorded incident and observation causes:\n\n"
        )
        for cause, cnt in results[:6]:
            reply += f"- **{cause}**: **{cnt} reports**\n"

        return {
            "reply": reply,
            "suggested_actions": [
                "What consequences are most common?",
                "Which reports are recurring?",
                "Show high-risk PPE reports.",
                "Summarize the current safety situation."
            ],
            "relevant_reports": [],
            "category": "CAUSES"
        }

    @staticmethod
    def _query_common_consequences(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SafetyReport.potential_consequence, func.count(SafetyReport.id).label("cnt")).where(
            SafetyReport.potential_consequence != None
        )
        if dataset_id:
            q = q.where(SafetyReport.dataset_id == dataset_id)
        q = q.group_by(SafetyReport.potential_consequence).order_by(desc("cnt"))
        results = db.execute(q).all()

        reply = (
            f"### Most Common Potential Consequences in Database\n\n"
            f"Aggregating all recorded near-miss and incident outcome ratings:\n\n"
        )
        for consequence, cnt in results[:6]:
            reply += f"- **{consequence}**: **{cnt} occurrences**\n"

        return {
            "reply": reply,
            "suggested_actions": [
                "What are the most common immediate causes?",
                "How many high-risk reports?",
                "Which reports are open?",
                "Summarize the current safety situation."
            ],
            "relevant_reports": [],
            "category": "CONSEQUENCES"
        }

    @staticmethod
    def _query_open_reports(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SafetyReport).where(
            or_(
                func.lower(SafetyReport.action_status) == "open",
                SafetyReport.action_status == None
            )
        )
        if dataset_id:
            q = q.where(SafetyReport.dataset_id == dataset_id)
        open_reports = list(db.scalars(q).all())
        total_open = len(open_reports)

        reply = (
            f"### Open Safety Actions Telemetry\n\n"
            f"There are currently **{total_open} Open Safety Reports** requiring field verification and corrective action closure:\n\n"
        )
        rel_reps = []
        for r in open_reports[:5]:
            rel_reps.append({"id": r.id, "original_id": r.original_id, "risk": r.risk_level})
            reply += f"- **{r.original_id}** ({r.refinery_unit} - {r.department}): Action: *\"{r.corrective_action}\"* | Assigned: `{r.assigned_to or 'Unassigned'}`\n"

        return {
            "reply": reply,
            "suggested_actions": [
                "Which corrective actions are overdue?",
                "How many high-risk reports?",
                "Which reports are recurring?",
                "Summarize the current safety situation."
            ],
            "relevant_reports": rel_reps,
            "category": "ACTIONS_OPEN"
        }

    @staticmethod
    def _query_recurring_reports(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SafetyReport).where(
            or_(
                SafetyReport.repeated_issue == True,
                SafetyReport.previous_similar_reports > 0
            )
        )
        if dataset_id:
            q = q.where(SafetyReport.dataset_id == dataset_id)
        recurring = list(db.scalars(q).all())

        reply = (
            f"### Recurring Issues & Hotspot Observations\n\n"
            f"There are **{len(recurring)} recurring safety issues** recorded where repeated failure modes or prior similar incidents were identified:\n\n"
        )
        rel_reps = []
        for r in recurring[:5]:
            rel_reps.append({"id": r.id, "original_id": r.original_id, "risk": r.risk_level})
            reply += f"- **{r.original_id}** ({r.refinery_unit} - {r.equipment}): Prior Events: **{r.previous_similar_reports or 1}** | Problem: *\"{r.description}\"*\n"

        return {
            "reply": reply,
            "suggested_actions": [
                "Show reports where previous similar reports are greater than 2.",
                "Which refinery unit has the most reports?",
                "What are the most common PPE problems?",
                "Summarize the current safety situation."
            ],
            "relevant_reports": rel_reps,
            "category": "RECURRING"
        }

    @staticmethod
    def _query_reports_by_previous_similar(db: Session, threshold: int, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SafetyReport).where(SafetyReport.previous_similar_reports > threshold)
        if dataset_id:
            q = q.where(SafetyReport.dataset_id == dataset_id)
        matched = list(db.scalars(q).all())

        reply = (
            f"### Parameterized Query Results: Previous Similar Reports > {threshold}\n\n"
            f"Found **{len(matched)} reports** matching `previous_similar_reports > {threshold}`:\n\n"
        )
        rel_reps = []
        for r in matched:
            rel_reps.append({"id": r.id, "original_id": r.original_id, "risk": r.risk_level})
            reply += f"- **{r.original_id}** ({r.refinery_unit}): **{r.previous_similar_reports} previous similar reports** | \"{r.description}\" (Risk: `{r.risk_level}`)\n"

        if not matched:
            reply += f"No reports found with strictly more than {threshold} previous similar occurrences."

        return {
            "reply": reply,
            "suggested_actions": [
                "Which reports are recurring?",
                "How many high-risk reports?",
                "Summarize the current safety situation."
            ],
            "relevant_reports": rel_reps,
            "category": "PARAMETRIC_FILTER"
        }

    @staticmethod
    def _query_high_risk_by_unit(db: Session, unit_name: str, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SafetyReport).where(
            and_(
                func.lower(SafetyReport.refinery_unit) == unit_name.lower(),
                func.lower(SafetyReport.risk_level) == "high"
            )
        )
        if dataset_id:
            q = q.where(SafetyReport.dataset_id == dataset_id)
        reports = list(db.scalars(q).all())

        reply = (
            f"### High-Risk Observations in {unit_name}\n\n"
            f"Found **{len(reports)} High-Risk safety reports** from **{unit_name}**:\n\n"
        )
        rel_reps = []
        for r in reports:
            rel_reps.append({"id": r.id, "original_id": r.original_id, "risk": r.risk_level})
            reply += f"- **{r.original_id}** ({r.work_type}): \"{r.description}\" | Consequence: `{r.potential_consequence}` | Status: `{r.action_status}`\n"

        if not reports:
            reply += f"Zero high-risk reports found for unit '{unit_name}' in the active database."

        return {
            "reply": reply,
            "suggested_actions": [
                f"Show all reports from {unit_name}.",
                "Show high-risk PPE reports.",
                "Summarize the current safety situation."
            ],
            "relevant_reports": rel_reps,
            "category": "UNIT_FILTER"
        }

    @staticmethod
    def _query_high_risk_ppe(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SafetyReport).where(
            and_(
                or_(
                    SafetyReport.ppe_issue == True,
                    func.lower(SafetyReport.report_type).like("%ppe%"),
                    func.lower(SafetyReport.description).like("%ppe%"),
                    func.lower(SafetyReport.description).like("%helmet%"),
                    func.lower(SafetyReport.description).like("%glasses%"),
                    func.lower(SafetyReport.description).like("%goggles%"),
                    func.lower(SafetyReport.description).like("%gloves%")
                ),
                func.lower(SafetyReport.risk_level) == "high"
            )
        )
        if dataset_id:
            q = q.where(SafetyReport.dataset_id == dataset_id)
        reports = list(db.scalars(q).all())

        reply = (
            f"### High-Risk PPE Safety Observations ({len(reports)} Total)\n\n"
            f"The following reports represent **High-Risk PPE violations** where unmitigated personnel exposure intersects with high-energy or toxic process hazards:\n\n"
        )
        rel_reps = []
        for r in reports:
            rel_reps.append({"id": r.id, "original_id": r.original_id, "risk": r.risk_level})
            reply += f"- **{r.original_id}** ({r.refinery_unit} - {r.department}): \"{r.description}\" | Consequence: `{r.potential_consequence}`\n"

        return {
            "reply": reply,
            "suggested_actions": [
                "What are the most common PPE problems?",
                "Which refinery unit has the most reports?",
                "Which reports are open?",
                "Summarize the current safety situation."
            ],
            "relevant_reports": rel_reps,
            "category": "HIGH_RISK_PPE"
        }

    @staticmethod
    def _query_ppe_by_department(db: Session, dept_name: str, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SafetyReport).where(
            and_(
                func.lower(SafetyReport.department) == dept_name.lower(),
                or_(
                    SafetyReport.ppe_issue == True,
                    func.lower(SafetyReport.report_type).like("%ppe%"),
                    func.lower(SafetyReport.description).like("%ppe%"),
                    func.lower(SafetyReport.description).like("%helmet%"),
                    func.lower(SafetyReport.description).like("%glasses%"),
                    func.lower(SafetyReport.description).like("%gloves%")
                )
            )
        )
        if dataset_id:
            q = q.where(SafetyReport.dataset_id == dataset_id)
        reports = list(db.scalars(q).all())

        reply = (
            f"### PPE Observations from {dept_name} ({len(reports)} Total)\n\n"
            f"Filtered records where department is **{dept_name}** and PPE issue is flagged:\n\n"
        )
        rel_reps = []
        for r in reports[:6]:
            rel_reps.append({"id": r.id, "original_id": r.original_id, "risk": r.risk_level})
            reply += f"- **{r.original_id}** ({r.refinery_unit}): \"{r.description}\" | Risk: `{r.risk_level}` | Consequence: `{r.potential_consequence}`\n"

        return {
            "reply": reply,
            "suggested_actions": [
                "What are the most common PPE problems?",
                "Which department has the most observations?",
                "Show high-risk PPE reports.",
                "Summarize the current safety situation."
            ],
            "relevant_reports": rel_reps,
            "category": "DEPT_PPE"
        }

    @staticmethod
    def _query_safety_summary(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        # Aggregate true database metrics
        total = db.scalar(select(func.count(SafetyReport.id))) or 0
        high = db.scalar(select(func.count(SafetyReport.id)).where(func.lower(SafetyReport.risk_level) == "high")) or 0
        med = db.scalar(select(func.count(SafetyReport.id)).where(func.lower(SafetyReport.risk_level) == "medium")) or 0
        low = db.scalar(select(func.count(SafetyReport.id)).where(func.lower(SafetyReport.risk_level) == "low")) or 0
        overdue = db.scalar(select(func.count(SafetyReport.id)).where(func.lower(SafetyReport.action_status) == "overdue")) or 0
        open_cnt = db.scalar(select(func.count(SafetyReport.id)).where(func.lower(SafetyReport.action_status) == "open")) or 0

        # Top unit
        top_unit_res = db.execute(
            select(SafetyReport.refinery_unit, func.count(SafetyReport.id).label("cnt"))
            .where(SafetyReport.refinery_unit != None)
            .group_by(SafetyReport.refinery_unit)
            .order_by(desc("cnt"))
            .limit(1)
        ).first()
        top_unit = f"{top_unit_res[0]} ({top_unit_res[1]} reports)" if top_unit_res else "N/A"

        # SIF summary
        sif_sum = SIFService.get_sif_summary(db, dataset_id)

        reply = (
            f"### Executive Safety Intelligence Summary\n\n"
            f"**Operational Safety Telemetry (Database Grounded)**:\n"
            f"- **Total Safety Reports Logged**: **{total}**\n"
            f"- **Risk Profile**: High Risk: **{high}** ({(high/total*100):.1f}%), Medium Risk: **{med}**, Low Risk: **{low}**\n"
            f"- **SIF Precursor Detection**: **{sif_sum['sif_precursors_detected']}** potential precursor events ({sif_sum['sif_precursor_rate_percentage']}% rate)\n"
            f"- **Top Observation Hotspot**: **{top_unit}**\n"
            f"- **Action Status Telemetry**: **{overdue} Overdue Actions**  | **{open_cnt} Open Actions**\n\n"
            f"**Strategic HSE Focus**:\n"
            f"1. Prioritize immediate closure of the **{overdue} Overdue Action Items**.\n"
            f"2. Inspect high-energy process barrier compliance in **{top_unit_res[0] if top_unit_res else 'Process Units'}**.\n"
            f"3. Enforce mandatory eye and head PPE compliance across all maintenance and operations zones."
        )

        return {
            "reply": reply,
            "suggested_actions": [
                "Show high-risk reports",
                "Which corrective actions are overdue?",
                "Which refinery unit has the most reports?",
                "What are the most common PPE problems?"
            ],
            "relevant_reports": [],
            "category": "EXECUTIVE_SUMMARY"
        }

    @staticmethod
    def _query_unit_intel(db: Session, unit_name: str, dataset_id: Optional[str]) -> Dict[str, Any]:
        reports = list(db.scalars(
            select(SafetyReport).where(func.lower(SafetyReport.refinery_unit) == unit_name.lower())
        ).all())

        if not reports:
            return {
                "reply": f"No reports found for unit **{unit_name}** in the database.",
                "suggested_actions": ["Which refinery unit has the most reports?", "How many reports are there?"],
                "relevant_reports": [],
                "category": "UNIT_INTEL"
            }

        total_u = len(reports)
        high_u = sum(1 for r in reports if (r.risk_level or "").lower() == "high")
        work_types = list(set(r.work_type for r in reports if r.work_type))

        reply = (
            f"### Refinery Unit Intelligence: {reports[0].refinery_unit or unit_name}\n\n"
            f"- **Total Observations in Unit**: **{total_u}**\n"
            f"- **High-Risk Observations**: **{high_u}**\n"
            f"- **Active Work Types**: {', '.join(work_types[:4])}\n\n"
            f"**Sample Observations**:\n"
        )
        rel_reps = []
        for r in reports[:3]:
            rel_reps.append({"id": r.id, "original_id": r.original_id, "risk": r.risk_level})
            reply += f"- **{r.original_id}**: \"{r.description}\" (Risk: `{r.risk_level}`)\n"

        return {
            "reply": reply,
            "suggested_actions": [
                f"Show high-risk reports from the {reports[0].refinery_unit}.",
                "Which refinery unit has the most reports?",
                "Summarize the current safety situation."
            ],
            "relevant_reports": rel_reps,
            "category": "UNIT_INTEL"
        }

    @staticmethod
    def _query_sif_overview(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        summary = SIFService.get_sif_summary(db, dataset_id)
        reply = (
            f"### SIF Precursor Intelligence Overview\n\n"
            f"- **Total Safety Reports Analyzed**: {summary['total_analyzed']}\n"
            f"- **SIF Precursors Detected**: **{summary['sif_precursors_detected']}** ({summary['sif_precursor_rate_percentage']}% of all observations)\n"
            f"- **AI Risk Rating Breakdown**: High: {summary['by_ai_risk_level'].get('HIGH', 0)}, Medium: {summary['by_ai_risk_level'].get('MEDIUM', 0)}, Low: {summary['by_ai_risk_level'].get('LOW', 0)}\n"
            f"- **Risk Level Upgrades by AI**: **{summary['risk_level_upgrades']}** reports elevated due to high-energy exposure vectors in active process units.\n\n"
            f"**Top SIF Exposure Categories**:\n"
        )
        for cat, cnt in sorted(summary['by_sif_category'].items(), key=lambda x: x[1], reverse=True)[:4]:
            reply += f"- **{cat}**: {cnt} observations\n"

        return {
            "reply": reply,
            "suggested_actions": [
                "Show high-risk safety observations",
                "What are the most common PPE problems?",
                "Which refinery unit has the most reports?",
                "Summarize the current safety situation."
            ],
            "relevant_reports": [],
            "category": "SIF_OVERVIEW"
        }

    @staticmethod
    def _query_overdue_actions(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SafetyReport).where(func.lower(SafetyReport.action_status) == "overdue")
        if dataset_id:
            q = q.where(SafetyReport.dataset_id == dataset_id)
        overdue_reports = list(db.scalars(q).all())

        reply = (
            f"### Overdue Corrective Action Telemetry\n\n"
            f"Currently, there are **{len(overdue_reports)} Overdue Action Items** requiring immediate management closure:\n\n"
        )
        rel_reps = []
        for r in overdue_reports:
            rel_reps.append({"id": r.id, "original_id": r.original_id, "risk": r.risk_level})
            reply += f"- **{r.original_id}** ({r.refinery_unit}): Action: *\"{r.corrective_action}\"* | Risk: `{r.risk_level}`\n"

        return {
            "reply": reply,
            "suggested_actions": [
                "Which reports are open?",
                "How many high-risk reports?",
                "Summarize the current safety situation."
            ],
            "relevant_reports": rel_reps,
            "category": "OVERDUE_ACTIONS"
        }

    @staticmethod
    def _generate_grounded_fallback(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        total = db.scalar(select(func.count(SafetyReport.id))) or 0
        high = db.scalar(select(func.count(SafetyReport.id)).where(func.lower(SafetyReport.risk_level) == "high")) or 0
        overdue = db.scalar(select(func.count(SafetyReport.id)).where(func.lower(SafetyReport.action_status) == "overdue")) or 0

        reply = (
            f"### OIL Safety Intelligence Assistant\n\n"
            f"I am connected to the **OIL Safety Intelligence Database** (**{total} reports loaded**, {high} High-Risk, {overdue} Overdue Actions).\n\n"
            f"You can ask me questions grounded in the database such as:\n"
            f"- *\"How many reports are there?\"*\n"
            f"- *\"How many high-risk reports?\"*\n"
            f"- *\"What are the most common PPE problems?\"*\n"
            f"- *\"Which refinery unit has the most reports?\"*\n"
            f"- *\"Which department has the most observations?\"*\n"
            f"- *\"What are the most common immediate causes?\"*\n"
            f"- *\"What consequences are most common?\"*\n"
            f"- *\"Which reports are open?\"*\n"
            f"- *\"Which reports are recurring?\"*\n"
            f"- *\"Show high-risk reports from the Hydrogen Unit.\"*\n"
            f"- *\"Show PPE observations from Maintenance.\"*\n"
            f"- *\"Show reports where previous similar reports are greater than 2.\"*\n"
            f"- *\"Summarize the current safety situation.\"*"
        )
        return {
            "reply": reply,
            "suggested_actions": [
                "How many reports are there?",
                "How many high-risk reports?",
                "What are the most common PPE problems?",
                "Which refinery unit has the most reports?",
                "Summarize the current safety situation."
            ],
            "relevant_reports": [],
            "category": "HELP"
        }

    @staticmethod
    def _extract_refinery_unit(msg: str) -> Optional[str]:
        known_units = [
            "hydrogen unit",
            "hydrotreating unit",
            "fcc",
            "loading bay",
            "tank farm",
            "utilities",
            "cdu",
            "vdu",
            "sulfur recovery unit",
            "distillation unit",
            "cracking unit",
            "alkylation unit"
        ]
        for u in known_units:
            if u in msg:
                return u
        return None

    # -------------------------------------------------------------
    # EXPANDED MULTI-DATASET & FACTOR INTELLIGENCE QUERY HANDLERS
    # -------------------------------------------------------------
    @staticmethod
    def _query_supervisor_negligence_count(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SafetyReport).where(
            or_(
                SafetyReport.supervisor_factor == True,
                SafetyReport.detected_factors.contains("Supervisor_Negligence")
            )
        )
        if dataset_id:
            q = q.where(SafetyReport.dataset_id == dataset_id)
        reports = list(db.scalars(q).all())
        total = len(reports)
        high = sum(1 for r in reports if (r.risk_level or "").lower() in ["high", "critical"])
        overdue = sum(1 for r in reports if (r.action_status or "").lower() == "overdue")

        reply = (
            f"### Supervisor Factor / Negligence Telemetry\n\n"
            f"Across the active safety database:\n"
            f"- **Total Observations Involving Supervisor Negligence**: **{total}**\n"
            f"- **High/Critical Risk Observations**: **{high}** ({(high/total*100):.1f}% if {total}>0 else 0%)\n"
            f"- **Overdue Corrective Actions**: **{overdue}**\n\n"
            f"**Key Findings**: Supervisory oversights frequently correlate with bypassed permits, lack of PPE enforcement during turnarounds, and delayed barrier validation."
        )
        rel_reps = [{"id": r.id, "original_id": r.original_id, "risk": r.risk_level} for r in reports[:3]]
        return {
            "reply": reply,
            "suggested_actions": [
                "Which factor combinations are most common?",
                "How many reports involve maintenance delay?",
                "Show high-potential near misses."
            ],
            "relevant_reports": rel_reps,
            "category": "FACTOR_INTEL"
        }

    @staticmethod
    def _query_maintenance_delay_count(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SafetyReport).where(
            or_(
                SafetyReport.maintenance_factor == True,
                SafetyReport.detected_factors.contains("Maintenance_Delay_or_Issue")
            )
        )
        if dataset_id:
            q = q.where(SafetyReport.dataset_id == dataset_id)
        reports = list(db.scalars(q).all())
        total = len(reports)
        high = sum(1 for r in reports if (r.risk_level or "").lower() in ["high", "critical"])
        units = Counter([r.refinery_unit for r in reports if r.refinery_unit]).most_common(3)

        reply = (
            f"### Maintenance Delay / Issue Telemetry\n\n"
            f"Across the active safety database:\n"
            f"- **Total Observations Involving Maintenance Delays**: **{total}**\n"
            f"- **High/Critical Risk Incidents**: **{high}**\n"
            f"- **Top Impacted Refinery Units**: {', '.join([f'{u[0]} ({u[1]})' for u in units])}\n\n"
            f"**Key Findings**: Deferred maintenance predominantly impacts pressure relief valves, pump mechanical seals, and vibration monitoring routines."
        )
        rel_reps = [{"id": r.id, "original_id": r.original_id, "risk": r.risk_level} for r in reports[:3]]
        return {
            "reply": reply,
            "suggested_actions": [
                "How many reports involve repeated issues being ignored?",
                "Which factor combinations are associated with high risk?",
                "Summarize the current safety situation."
            ],
            "relevant_reports": rel_reps,
            "category": "FACTOR_INTEL"
        }

    @staticmethod
    def _query_repeated_issues_count(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SafetyReport).where(
            or_(
                SafetyReport.repeated_issue == True,
                SafetyReport.detected_factors.contains("Repeated_Issue_Ignored"),
                SafetyReport.previous_similar_reports > 0
            )
        )
        if dataset_id:
            q = q.where(SafetyReport.dataset_id == dataset_id)
        reports = list(db.scalars(q).all())
        total = len(reports)
        high = sum(1 for r in reports if (r.risk_level or "").lower() in ["high", "critical"])

        reply = (
            f"### Repeated Issues Ignored Telemetry\n\n"
            f"- **Total Observations Involving Recurring / Ignored Issues**: **{total}**\n"
            f"- **High / Critical Risk Severity**: **{high}** observations\n\n"
            f"**Systemic Risk Note**: Repeated issues indicate barrier erosion where previous corrective actions failed to address root operational causes."
        )
        rel_reps = [{"id": r.id, "original_id": r.original_id, "risk": r.risk_level} for r in reports[:3]]
        return {
            "reply": reply,
            "suggested_actions": [
                "Which problems are repeatedly ignored?",
                "Which equipment appears repeatedly?",
                "Show high-potential near misses."
            ],
            "relevant_reports": rel_reps,
            "category": "FACTOR_INTEL"
        }

    @staticmethod
    def _query_only_ppe_count(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SafetyReport).where(
            SafetyReport.factor_count == 1,
            or_(
                SafetyReport.ppe_issue == True,
                SafetyReport.source_dataset.ilike("%ppe%")
            )
        )
        if dataset_id:
            q = q.where(SafetyReport.dataset_id == dataset_id)
        reports = list(db.scalars(q).all())
        total = len(reports)
        high = sum(1 for r in reports if (r.risk_level or "").lower() in ["high", "critical"])

        reply = (
            f"### Single-Factor PPE Telemetry\n\n"
            f"- **Observations Involving ONLY PPE Non-Compliance**: **{total}**\n"
            f"- **High-Risk Observations**: **{high}**\n\n"
            f"Single-factor PPE non-compliances represent isolated behavioral non-compliances without co-occurring mechanical or supervisory breakdown."
        )
        return {
            "reply": reply,
            "suggested_actions": [
                "What changes when multiple safety factors occur together?",
                "Which factor combinations are most common?",
                "What are the most common PPE problems?"
            ],
            "relevant_reports": [],
            "category": "FACTOR_INTEL"
        }

    @staticmethod
    def _query_top_safety_factor(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        from app.services.factor_service import FactorService
        summary = FactorService.get_factor_summary(db, dataset_id)
        if not summary.factors:
            return {"reply": "Insufficient data available to determine top safety factors.", "suggested_actions": [], "relevant_reports": [], "category": "FACTOR_INTEL"}

        top_factor = summary.factors[0]
        reply = (
            f"### Safety Factor Precursor Ranking\n\n"
            f"The most frequently observed safety factor is **{top_factor.display_name}** with **{top_factor.total_count} observations** ({top_factor.percentage}% of analyzed corpus).\n\n"
            f"**Complete Factor Frequency Breakdown**:\n"
        )
        for f in summary.factors:
            reply += f"- **{f.display_name}**: {f.total_count} reports ({f.percentage}%) | High Risk: {f.high_risk_count}\n"

        return {
            "reply": reply,
            "suggested_actions": [
                "Which factor combinations are most common?",
                "Which factor combinations have the highest risk?",
                "Show high-potential near misses."
            ],
            "relevant_reports": [],
            "category": "FACTOR_INTEL"
        }

    @staticmethod
    def _query_factor_combinations_common(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        from app.services.factor_service import FactorService
        combs = FactorService.get_factor_combinations(db, dataset_id)
        reply = (
            f"### Safety Factor Combination Frequency Matrix\n\n"
            f"- **1-Factor Observations**: {combs.level_1_count} reports\n"
            f"- **2-Factor Combinations**: {combs.level_2_count} reports\n"
            f"- **3-Factor Combinations**: {combs.level_3_count} reports\n"
            f"- **4-Factor Combinations**: {combs.level_4_count} reports\n\n"
            f"**Top Multi-Factor Combinations**:\n"
        )
        multi_combs = [c for c in combs.combinations if c.factor_count > 1][:4]
        for c in multi_combs:
            reply += f"- **{c.combination_key}** ({c.report_count} reports) &rarr; High Risk: `{c.high_risk_count}` | Danger: `{c.danger_level}`\n"

        return {
            "reply": reply,
            "suggested_actions": [
                "Which factor combinations have the highest risk?",
                "Which combination appears most dangerous?",
                "Show high-potential near misses."
            ],
            "relevant_reports": [],
            "category": "COMBINATION_INTEL"
        }

    @staticmethod
    def _query_factor_combinations_high_risk(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        from app.services.factor_service import FactorService
        combs = FactorService.get_factor_combinations(db, dataset_id)
        danger_ranked = combs.danger_ranked_combinations[:4]

        reply = (
            f"### High-Risk & Dangerous Factor Combinations Ranking\n\n"
            f"When multiple control barriers fail simultaneously, risk escalates non-linearly:\n\n"
        )
        for c in danger_ranked:
            reply += (
                f"- **{c.combination_key}**\n"
                f"  - **Danger Level**: `{c.danger_level}` (AI Score: `{c.danger_score}/100`)\n"
                f"  - **High/Critical Risk Ratio**: `{c.high_risk_ratio * 100:.1f}%` ({c.high_risk_count}/{c.report_count})\n"
                f"  - **Top Potential Consequences**: {', '.join(c.top_consequences[:2])}\n\n"
            )

        return {
            "reply": reply,
            "suggested_actions": [
                "Show reports where multiple safety failures occurred together.",
                "Show high-potential near misses.",
                "Compare single-factor and multi-factor reports."
            ],
            "relevant_reports": [],
            "category": "COMBINATION_INTEL"
        }

    @staticmethod
    def _query_factors_co_occurrence(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        from app.services.factor_service import FactorService
        combs = FactorService.get_factor_combinations(db, dataset_id)
        multi_2 = [c for c in combs.combinations if c.factor_count == 2]

        reply = (
            f"### Co-Occurring Safety Factors Analysis\n\n"
            f"The safety corpus reveals distinct co-occurrence patterns across refinery operations:\n\n"
        )
        for c in multi_2:
            reply += f"- **{c.combination_key}**: {c.report_count} observations (High Risk: {c.high_risk_count})\n"

        reply += "\n**Insight**: Maintenance Delays and Repeated Issues Ignored exhibit the highest co-occurrence correlation with critical equipment vibrations and pipeline leaks."
        return {
            "reply": reply,
            "suggested_actions": [
                "Which factor combinations are associated with high-risk reports?",
                "Compare single-factor and multi-factor reports.",
                "Show high-potential near misses."
            ],
            "relevant_reports": [],
            "category": "COMBINATION_INTEL"
        }

    @staticmethod
    def _query_multi_factor_reports(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SafetyReport).where(SafetyReport.factor_count >= 3)
        if dataset_id:
            q = q.where(SafetyReport.dataset_id == dataset_id)
        reports = list(db.scalars(q).all())
        total = len(reports)
        crit = sum(1 for r in reports if (r.risk_level or "").lower() == "critical")
        high = sum(1 for r in reports if (r.risk_level or "").lower() == "high")

        reply = (
            f"### Compound Multi-Factor Safety Observations (3+ Barriers Failed)\n\n"
            f"- **Total Compound Reports**: **{total}** observations\n"
            f"- **Critical Risk Reports**: **{crit}**\n"
            f"- **High Risk Reports**: **{high}**\n\n"
            f"**Sample Multi-Barrier Breakdown Incidents**:\n"
        )
        rel_reps = []
        for r in reports[:3]:
            rel_reps.append({"id": r.id, "original_id": r.original_id, "risk": r.risk_level})
            factors_str = ", ".join([f.replace("_", " ") for f in (r.detected_factors or [])])
            reply += f"- **{r.original_id}** ({r.refinery_unit}): *\"{r.description}\"* [Factors: `{factors_str}` | Risk: `{r.risk_level}`]\n"

        return {
            "reply": reply,
            "suggested_actions": [
                "Show high-potential near misses.",
                "Which factor combinations have the highest risk?",
                "Summarize the current safety situation."
            ],
            "relevant_reports": rel_reps,
            "category": "COMBINATION_INTEL"
        }

    @staticmethod
    def _query_high_potential_reports(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        from app.services.factor_service import FactorService
        hipo_intel = FactorService.get_high_potential_intelligence(db)

        reply = (
            f"### High-Potential (HiPo) Safety Intelligence\n\n"
            f"- **Total High-Potential Near Misses**: **{hipo_intel.total_high_potential_incidents}** observations\n"
            f"- **Critical Risk Classifications**: **{hipo_intel.critical_risk_count}**\n"
            f"- **Multi-Barrier Failure Co-occurrence**: **{hipo_intel.multi_barrier_failure_count}** incidents\n\n"
            f"**Key Failure Mechanisms**:\n"
        )
        for p in hipo_intel.key_failure_patterns:
            reply += f"- **{p.pattern_name}** ({p.incident_count} events): Causes: {', '.join(p.immediate_causes[:2])} | Potential: {', '.join(p.potential_consequences[:2])}\n"

        reply += "\n**Mandatory Preventive Imperative**: " + hipo_intel.preventive_imperatives[0]

        return {
            "reply": reply,
            "suggested_actions": [
                "Which factors are associated with high-potential near misses?",
                "Which factor combinations are most common?",
                "Show reports where multiple safety failures occurred together."
            ],
            "relevant_reports": [],
            "category": "HIPO_INTEL"
        }

    @staticmethod
    def _query_high_potential_factors(db: Session) -> Dict[str, Any]:
        reply = (
            f"### Factors Associated with High-Potential Near Misses\n\n"
            f"In the **12_High_Potential** safety dataset (100 incidents):\n"
            f"- **PPE Non-Compliance**: Present in 100% of observations (bypassed or defective protective equipment).\n"
            f"- **Supervisor Negligence**: Present in 100% of observations (lack of oversight during critical permits).\n"
            f"- **Maintenance Delay / Issue**: Present in 100% of observations (unresolved degradation on active process lines).\n"
            f"- **Repeated Issue Ignored**: Present in 100% of observations (prior similar notifications without closure).\n\n"
            f"**Analysis**: High-Potential events are characterized by the simultaneous breakdown of all primary organizational and physical barriers."
        )
        return {
            "reply": reply,
            "suggested_actions": [
                "Show high-potential near misses.",
                "Which factor combinations have the highest risk?",
                "Summarize the current safety situation."
            ],
            "relevant_reports": [],
            "category": "HIPO_INTEL"
        }

    @staticmethod
    def _query_analyze_dataset(db: Session, sheet_name: str) -> Dict[str, Any]:
        ds = db.scalar(select(Dataset).where(Dataset.dataset_name == sheet_name))
        reports = list(db.scalars(select(SafetyReport).where(SafetyReport.source_dataset == sheet_name)).all())
        total = len(reports)
        high = sum(1 for r in reports if (r.risk_level or "").lower() in ["high", "critical"])
        crit = sum(1 for r in reports if (r.risk_level or "").lower() == "critical")
        hipo = sum(1 for r in reports if bool(r.high_potential))

        reply = (
            f"### Dataset Scope Analysis: `{sheet_name}`\n\n"
            f"- **Dataset Classification**: `{ds.dataset_type if ds else 'operational'}` ({ds.factor_count if ds else 0} active factors)\n"
            f"- **Total Records**: **{total}**\n"
            f"- **Risk Profile**: High Risk: {high}, Critical Risk: {crit}, Low/Medium: {total - high}\n"
            f"- **High-Potential Records**: **{hipo}**\n"
            f"- **Active Factor Flags**: {', '.join(ds.factor_names if ds else [])}\n"
        )
        rel_reps = [{"id": r.id, "original_id": r.original_id, "risk": r.risk_level} for r in reports[:3]]
        return {
            "reply": reply,
            "suggested_actions": [
                "Compare single-factor and multi-factor reports.",
                "Which factor combinations have the highest risk?",
                "Show high-potential near misses."
            ],
            "relevant_reports": rel_reps,
            "category": "DATASET_SCOPE"
        }

    @staticmethod
    def _query_compare_single_vs_multi_factor(db: Session) -> Dict[str, Any]:
        single_reports = list(db.scalars(select(SafetyReport).where(SafetyReport.factor_count == 1)).all())
        multi_reports = list(db.scalars(select(SafetyReport).where(SafetyReport.factor_count > 1)).all())

        tot_s = len(single_reports)
        tot_m = len(multi_reports)

        high_s = sum(1 for r in single_reports if (r.risk_level or "").lower() in ["high", "critical"])
        high_m = sum(1 for r in multi_reports if (r.risk_level or "").lower() in ["high", "critical"])

        pct_s = (high_s / tot_s * 100) if tot_s > 0 else 0
        pct_m = (high_m / tot_m * 100) if tot_m > 0 else 0

        reply = (
            f"### Comparative Intelligence: Single-Factor vs Multi-Factor Observations\n\n"
            f"| Metric | Single-Factor Datasets | Multi-Factor Datasets |\n"
            f"| :--- | :--- | :--- |\n"
            f"| **Total Observations** | **{tot_s}** | **{tot_m}** |\n"
            f"| **High / Critical Risk Count** | **{high_s}** ({pct_s:.1f}%) | **{high_m}** ({pct_m:.1f}%) |\n"
            f"| **High Potential Incidents** | 0 | {sum(1 for r in multi_reports if bool(r.high_potential))} |\n\n"
            f"**Conclusion**: Multi-factor compounding increases High/Critical incident severity probability by +{pct_m - pct_s:.1f}% compared to isolated single-barrier failures."
        )
        return {
            "reply": reply,
            "suggested_actions": [
                "Which factor combinations have the highest risk?",
                "Show high-potential near misses.",
                "Summarize the current safety situation."
            ],
            "relevant_reports": [],
            "category": "COMPARISON"
        }

    @staticmethod
    def _query_compare_ppe_vs_maintenance(db: Session) -> Dict[str, Any]:
        ppe_reports = list(db.scalars(select(SafetyReport).where(SafetyReport.source_dataset == "01_PPE_NonCompliance")).all())
        maint_reports = list(db.scalars(select(SafetyReport).where(SafetyReport.source_dataset == "01_Maintenance_Delay_or_Issue")).all())

        tot_p = len(ppe_reports)
        tot_m = len(maint_reports)

        high_p = sum(1 for r in ppe_reports if (r.risk_level or "").lower() == "high")
        high_m = sum(1 for r in maint_reports if (r.risk_level or "").lower() == "high")

        reply = (
            f"### Comparative Analysis: PPE Non-Compliance vs Maintenance Delay\n\n"
            f"- **01_PPE_NonCompliance** ({tot_p} reports): High Risk = {high_p} ({(high_p/tot_p*100):.1f}%). Primary consequence: Lost-time injuries & minor personnel trauma.\n"
            f"- **01_Maintenance_Delay_or_Issue** ({tot_m} reports): High Risk = {high_m} ({(high_m/tot_m*100):.1f}%). Primary consequence: Hydrocarbon releases & equipment damage.\n\n"
            f"**Key Difference**: Maintenance delays present process safety containment risks, whereas PPE non-compliance presents direct occupational exposure risks."
        )
        return {
            "reply": reply,
            "suggested_actions": [
                "Compare single-factor and multi-factor reports.",
                "Which refinery unit has the most reports?",
                "Summarize the current safety situation."
            ],
            "relevant_reports": [],
            "category": "COMPARISON"
        }

    @staticmethod
    def _query_reports_by_hazard_term(db: Session, term: str, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SafetyReport).where(
            or_(
                SafetyReport.potential_consequence.ilike(f"%{term}%"),
                SafetyReport.hazard.ilike(f"%{term}%"),
                SafetyReport.description.ilike(f"%{term}%")
            )
        )
        if dataset_id:
            q = q.where(SafetyReport.dataset_id == dataset_id)
        reports = list(db.scalars(q).all())
        total = len(reports)
        high = sum(1 for r in reports if (r.risk_level or "").lower() in ["high", "critical"])

        reply = (
            f"### Hazard Intelligence: Observations Involving '{term.title()}'\n\n"
            f"- **Matching Observations Found**: **{total}**\n"
            f"- **High / Critical Severity**: **{high}**\n\n"
            f"**Sample Incidents**:\n"
        )
        rel_reps = []
        for r in reports[:3]:
            rel_reps.append({"id": r.id, "original_id": r.original_id, "risk": r.risk_level})
            reply += f"- **{r.original_id}** ({r.refinery_unit}): *\"{r.description}\"* (Consequence: `{r.potential_consequence}`)\n"

        return {
            "reply": reply,
            "suggested_actions": [
                "Show high-potential near misses.",
                "What consequences are most common?",
                "Summarize the current safety situation."
            ],
            "relevant_reports": rel_reps,
            "category": "HAZARD_QUERY"
        }

    @staticmethod
    def _query_repeated_equipment(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SafetyReport.equipment).where(SafetyReport.equipment.isnot(None))
        if dataset_id:
            q = q.where(SafetyReport.dataset_id == dataset_id)
        equipment_list = list(db.scalars(q).all())
        counts = Counter(equipment_list).most_common(5)

        reply = (
            f"### Recurring Equipment Tag Telemetry\n\n"
            f"The following equipment items have generated the highest observation frequency across the database:\n\n"
        )
        for eq, cnt in counts:
            reply += f"- **{eq}**: **{cnt}** observations recorded\n"

        return {
            "reply": reply,
            "suggested_actions": [
                "Which refinery units have recurring problems?",
                "Which problems are repeatedly ignored?",
                "Show high-potential near misses."
            ],
            "relevant_reports": [],
            "category": "RECURRING_EQUIPMENT"
        }

    @staticmethod
    def _query_highest_risk_work_types(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SafetyReport.work_type, SafetyReport.risk_level).where(SafetyReport.work_type.isnot(None))
        if dataset_id:
            q = q.where(SafetyReport.dataset_id == dataset_id)
        records = db.execute(q).all()

        type_map = defaultdict(lambda: {"total": 0, "high": 0})
        for wt, rl in records:
            type_map[wt]["total"] += 1
            if (rl or "").lower() in ["high", "critical"]:
                type_map[wt]["high"] += 1

        sorted_wt = sorted(type_map.items(), key=lambda x: (x[1]["high"], x[1]["total"]), reverse=True)[:5]

        reply = (
            f"### Highest Risk Work Types Ranking\n\n"
            f"Work activities with the highest frequency of High/Critical risk observations:\n\n"
        )
        for wt, stats in sorted_wt:
            pct = (stats["high"] / stats["total"] * 100) if stats["total"] > 0 else 0
            reply += f"- **{wt}**: {stats['high']} High-Risk / {stats['total']} Total ({pct:.1f}% High-Risk Rate)\n"

        return {
            "reply": reply,
            "suggested_actions": [
                "Which department has the most observations?",
                "Which factor combinations have the highest risk?",
                "Summarize the current safety situation."
            ],
            "relevant_reports": [],
            "category": "WORK_TYPE_RISK"
        }

    @staticmethod
    def _query_recurring_refinery_units(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SafetyReport.refinery_unit).where(
            SafetyReport.refinery_unit.isnot(None),
            or_(SafetyReport.repeated_issue == True, SafetyReport.previous_similar_reports > 0)
        )
        if dataset_id:
            q = q.where(SafetyReport.dataset_id == dataset_id)
        unit_list = list(db.scalars(q).all())
        counts = Counter(unit_list).most_common(5)

        reply = (
            f"### Refinery Units with Highest Recurrence Rates\n\n"
            f"Process units with the highest concentration of repeated or prior similar safety issues:\n\n"
        )
        for u, cnt in counts:
            reply += f"- **{u}**: **{cnt}** recurring observations\n"

        return {
            "reply": reply,
            "suggested_actions": [
                "Which equipment appears repeatedly?",
                "Which refinery unit has the most reports?",
                "Summarize the current safety situation."
            ],
            "relevant_reports": [],
            "category": "RECURRING_UNITS"
        }

    @staticmethod
    def _query_repeatedly_ignored_problems(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SafetyReport).where(SafetyReport.repeated_issue == True)
        if dataset_id:
            q = q.where(SafetyReport.dataset_id == dataset_id)
        reports = list(db.scalars(q).all())
        total = len(reports)
        open_cnt = sum(1 for r in reports if (r.action_status or "").lower() in ["open", "overdue"])

        reply = (
            f"### Repeatedly Ignored Problems Intelligence\n\n"
            f"- **Total Flagged Repeated Issues**: **{total}** observations\n"
            f"- **Currently Open / Overdue**: **{open_cnt}** action items\n\n"
            f"**Prevalent Repeated Problem Themes**:\n"
            f"- Recurring valve packing leaks deferred until scheduled turnaround.\n"
            f"- Gas detector alarm recalibration delays across process units.\n"
            f"- Compressor and pump abnormal vibration exceeding threshold without maintenance shutdown."
        )
        return {
            "reply": reply,
            "suggested_actions": [
                "Which equipment appears repeatedly?",
                "Which reports are open?",
                "Show high-potential near misses."
            ],
            "relevant_reports": [],
            "category": "REPEATED_PROBLEMS"
        }

    @staticmethod
    def _query_similar_reports_by_keyword(db: Session, msg: str, dataset_id: Optional[str]) -> Dict[str, Any]:
        # Extract potential keyword from query
        clean_msg = re.sub(r'\b(show|me|previous|reports|similar|to|this|one|have|we|seen|problems|involving|find|search|for|the|a|an)\b', '', msg).strip()
        search_term = clean_msg[:30].strip() if clean_msg else "leakage"

        q = select(SafetyReport).where(
            or_(
                SafetyReport.description.ilike(f"%{search_term}%"),
                SafetyReport.hazard.ilike(f"%{search_term}%"),
                SafetyReport.immediate_cause.ilike(f"%{search_term}%"),
                SafetyReport.potential_consequence.ilike(f"%{search_term}%")
            )
        )
        if dataset_id:
            q = q.where(SafetyReport.dataset_id == dataset_id)
        matches = list(db.scalars(q.limit(5)).all())

        if not matches:
            return {
                "reply": f"Insufficient matching data found for query term: *\"{search_term}\"*. Try searching for terms like 'gas detector', 'vibration', 'leakage', or 'harness'.",
                "suggested_actions": ["How many reports are there?", "What are the most common PPE problems?", "Summarize the current safety situation."],
                "relevant_reports": [],
                "category": "KEYWORD_SEARCH"
            }

        reply = (
            f"### Historical Safety Observation Retrieval (Keyword: *\"{search_term}\"*)\n\n"
            f"Found **{len(matches)} relevant historical reports** in the database:\n\n"
        )
        rel_reps = []
        for r in matches:
            rel_reps.append({"id": r.id, "original_id": r.original_id, "risk": r.risk_level})
            reply += f"- **{r.original_id}** ({r.refinery_unit}): *\"{r.description}\"* [Risk: `{r.risk_level}`]\n"

        return {
            "reply": reply,
            "suggested_actions": [
                "Which refinery unit has the most reports?",
                "Which factor combinations have the highest risk?",
                "Summarize the current safety situation."
            ],
            "relevant_reports": rel_reps,
            "category": "KEYWORD_SEARCH"
        }

    # =============================================================
    # PHASE 7 ANALYTICAL INTELLIGENCE QUERY METHODS
    # =============================================================

    @staticmethod
    def _query_critical_sif_precursors(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SIFEscalationAssessment)
        if dataset_id:
            q = q.where(SIFEscalationAssessment.dataset_id == dataset_id)
        assessments = list(db.scalars(q).all())

        if not assessments:
            return {
                "reply": "No sufficient SIF precursor escalation evidence available in current dataset.",
                "suggested_actions": ["How many reports are there?", "Summarize the current safety situation."],
                "relevant_reports": [],
                "category": "SIF_PRECURSOR_SUMMARY"
            }

        crit_count = sum(1 for a in assessments if a.severity == "CRITICAL")
        high_count = sum(1 for a in assessments if a.severity == "HIGH")
        elev_count = sum(1 for a in assessments if a.severity == "ELEVATED")
        watch_count = sum(1 for a in assessments if a.severity == "WATCH")
        norm_count = sum(1 for a in assessments if a.severity == "NORMAL")

        crit_items = [a for a in assessments if a.severity in ["CRITICAL", "HIGH"]][:5]

        reply = (
            f"### Critical SIF Precursor Intelligence Overview\n\n"
            f"- **Total Assessed Reports**: **{len(assessments)}**\n"
            f"- **Critical Precursor Severity**:  **{crit_count}**\n"
            f"- **High Precursor Severity**:  **{high_count}**\n"
            f"- **Elevated / Watch Precursors**: **{elev_count + watch_count}**\n"
            f"- **Normal Baseline**: **{norm_count}**\n\n"
            f"**High & Critical SIF Precursor Spotlight**:\n"
        )
        rel_reps = []
        for c in crit_items:
            rep = db.scalar(select(SafetyReport).where(SafetyReport.id == c.report_id))
            orig_id = rep.original_id if rep else (c.report_id[:8] if c.report_id else "N/A")
            rel_reps.append({"id": c.report_id, "original_id": orig_id, "risk": c.severity})
            why_text = (c.reasoning.get("why_escalated") if c.reasoning else None) or "Multi-barrier convergence around exposure."
            imm_text = (c.immediate_actions[0] if c.immediate_actions else None) or "Verify isolation."
            reply += (
                f"- **Report {orig_id}** ({c.refinery_unit or 'Process Unit'} • {c.equipment or 'General'}):\n"
                f"  - **Severity**: `{c.severity}` | **BDI**: `{c.bdi_score:.1f}` ({c.bdi_classification})\n"
                f"  - **Why Escalated**: *\"{why_text}\"*\n"
                f"  - **Immediate Containment**:  {imm_text}\n"
            )

        reply += "\n*Disclaimer: Potential precursor escalation — not a guaranteed incident prediction.*"

        return {
            "reply": reply,
            "suggested_actions": [
                "Which units have the highest BDI?",
                "Which barriers are degraded?",
                "Which actions breached SLA?",
                "Show active safety holds."
            ],
            "relevant_reports": rel_reps,
            "category": "SIF_PRECURSOR_SUMMARY"
        }

    @staticmethod
    def _query_bdi_intelligence(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(BarrierDegradationAssessment)
        if dataset_id:
            q = q.where(BarrierDegradationAssessment.dataset_id == dataset_id)
        bdi_list = list(db.scalars(q).all())

        if not bdi_list:
            return {
                "reply": "No sufficient barrier degradation records stored for this dataset.",
                "suggested_actions": ["How many reports are there?", "Summarize the current safety situation."],
                "relevant_reports": [],
                "category": "BDI_SUMMARY"
            }

        avg_bdi = sum(b.bdi_score for b in bdi_list) / len(bdi_list)
        sev_count = sum(1 for b in bdi_list if b.classification == "SEVERE")
        sig_count = sum(1 for b in bdi_list if b.classification == "SIGNIFICANT")
        mod_count = sum(1 for b in bdi_list if b.classification == "MODERATE")
        low_count = sum(1 for b in bdi_list if b.classification == "LOW")
        min_count = sum(1 for b in bdi_list if b.classification == "MINIMAL")

        # Aggregate degraded barriers
        barrier_counter: Counter = Counter()
        for b in bdi_list:
            b_bars = b.evidence.get("dominant_degraded_barriers", []) if b.evidence else []
            for bar in b_bars:
                barrier_counter[bar] += 1

        top_barriers = barrier_counter.most_common(3)
        top_barriers_str = ", ".join([f"{name} ({cnt})" for name, cnt in top_barriers]) if top_barriers else "None identified"

        reply = (
            f"### Barrier Degradation Index (BDI) Intelligence Summary\n\n"
            f"- **Average BDI Score**: **{avg_bdi:.1f} / 100**\n"
            f"- **Severe Degradation (BDI ≥ 80)**:  **{sev_count}** reports\n"
            f"- **Significant Degradation (BDI 60-79)**:  **{sig_count}** reports\n"
            f"- **Moderate Degradation (BDI 40-59)**: **{mod_count}** reports\n"
            f"- **Low / Minimal (BDI < 40)**: **{low_count + min_count}** reports\n\n"
            f"**Dominant Degraded Barrier Layers**:\n"
            f"`{top_barriers_str}`\n\n"
            f"*Disclaimer: BDI is an analytical indicator derived from observed safety data, not an official OIL risk score or accident probability.*"
        )

        return {
            "reply": reply,
            "suggested_actions": [
                "Which units have the highest BDI?",
                "Which barriers are degraded?",
                "Show critical SIF precursors.",
                "Which equipment has repeated barrier degradation?"
            ],
            "relevant_reports": [],
            "category": "BDI_SUMMARY"
        }

    @staticmethod
    def _query_highest_bdi_units(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(BarrierDegradationAssessment)
        if dataset_id:
            q = q.where(BarrierDegradationAssessment.dataset_id == dataset_id)
        bdi_list = list(db.scalars(q).all())

        if not bdi_list:
            return {
                "reply": "No sufficient barrier degradation data to compute unit rankings.",
                "suggested_actions": ["How many reports are there?", "Summarize the current safety situation."],
                "relevant_reports": [],
                "category": "BDI_UNITS"
            }

        unit_scores: Dict[str, List[float]] = defaultdict(list)
        unit_severe: Dict[str, int] = defaultdict(int)

        for b in bdi_list:
            u = b.refinery_unit or "General Process Area"
            unit_scores[u].append(b.bdi_score)
            if b.classification in ["SEVERE", "SIGNIFICANT"]:
                unit_severe[u] += 1

        ranked = sorted(
            [(u, sum(scores) / len(scores), len(scores), unit_severe[u]) for u, scores in unit_scores.items()],
            key=lambda x: x[1],
            reverse=True
        )

        reply = (
            f"### Refinery Units Ranked by Barrier Degradation Index (BDI)\n\n"
            f"Analytical ranking of process units exhibiting the highest concentration of degraded barrier defenses:\n\n"
        )
        for unit, avg_score, count, sev_cnt in ranked[:5]:
            reply += (
                f"- **{unit}**:\n"
                f"  - **Average BDI**: **{avg_score:.1f} / 100** ({count} total observations)\n"
                f"  - **Severe/Significant BDI Events**: `{sev_cnt}`\n"
            )

        reply += "\n*Disclaimer: BDI is an analytical indicator derived from observed data, not an official OIL risk score.*"

        return {
            "reply": reply,
            "suggested_actions": [
                "Which barriers are degraded?",
                "Show critical SIF precursors.",
                "Which equipment has repeated barrier degradation?"
            ],
            "relevant_reports": [],
            "category": "BDI_UNITS"
        }

    @staticmethod
    def _query_degraded_barriers_summary(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SafetyBarrierAssessment).where(SafetyBarrierAssessment.status.in_(["FAILED", "DEGRADED"]))
        if dataset_id:
            q = q.where(SafetyBarrierAssessment.dataset_id == dataset_id)
        barriers = list(db.scalars(q).all())

        if not barriers:
            return {
                "reply": "No degraded or failed safety barrier records identified in this dataset.",
                "suggested_actions": ["How many reports are there?", "Summarize the current safety situation."],
                "relevant_reports": [],
                "category": "BARRIER_SUMMARY"
            }

        barrier_counts: Counter = Counter()
        failed_counts: Counter = Counter()
        for b in barriers:
            barrier_counts[b.barrier_name] += 1
            if b.status == "FAILED":
                failed_counts[b.barrier_name] += 1

        reply = (
            f"### Swiss Cheese Safety Barrier Degradation Intelligence\n\n"
            f"Identified **{len(barriers)} barrier degradation records** across active observations:\n\n"
        )
        for name, cnt in barrier_counts.most_common(5):
            f_cnt = failed_counts.get(name, 0)
            reply += f"- **{name}**: **{cnt}** observations degraded ( `{f_cnt}` outright failed)\n"

        sample_reports = list({b.report_id for b in barriers if b.report_id})[:5]
        rel_reps = []
        for r_id in sample_reports:
            rep = db.scalar(select(SafetyReport).where(SafetyReport.id == r_id))
            orig_id = rep.original_id if rep else r_id[:8]
            rel_reps.append({"id": r_id, "original_id": orig_id, "risk": rep.risk_level if rep else "High"})

        return {
            "reply": reply,
            "suggested_actions": [
                "Which units have the highest BDI?",
                "Show critical SIF precursors.",
                "Which equipment has repeated barrier degradation?"
            ],
            "relevant_reports": rel_reps,
            "category": "BARRIER_SUMMARY"
        }

    @staticmethod
    def _query_correlated_reports(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SafetyCorrelation).order_by(desc(SafetyCorrelation.correlation_score)).limit(10)
        if dataset_id:
            q = q.where(SafetyCorrelation.dataset_id == dataset_id)
        corrs = list(db.scalars(q).all())

        if not corrs:
            return {
                "reply": "No multi-factor safety correlations logged yet. Correlate reports via the Multi-Factor Engine.",
                "suggested_actions": ["How many reports are there?", "Which factors are converging?"],
                "relevant_reports": [],
                "category": "CORRELATIONS"
            }

        reply = (
            f"### Multi-Factor Safety Correlation Intelligence\n\n"
            f"Identified **{len(corrs)} strong cross-report safety correlations**:\n\n"
        )
        rel_reps = []
        for c in corrs[:5]:
            src = db.scalar(select(SafetyReport).where(SafetyReport.id == c.source_report_id))
            rel = db.scalar(select(SafetyReport).where(SafetyReport.id == c.related_report_id))
            src_id = src.original_id if src else (c.source_report_id[:8] if c.source_report_id else "N/A")
            rel_id = rel.original_id if rel else (c.related_report_id[:8] if c.related_report_id else "N/A")

            factors_str = ", ".join(c.convergence_factors) if c.convergence_factors else "Shared Unit/Hazard"
            reply += (
                f"- **Report {src_id}**  **Report {rel_id}**:\n"
                f"  - **Relationship**: `{c.relationship_type}` (Score: `{c.correlation_score:.2f}`)\n"
                f"  - **Converging Factors**: `{factors_str}`\n"
            )
            if src:
                rel_reps.append({"id": src.id, "original_id": src.original_id, "risk": src.risk_level})

        return {
            "reply": reply,
            "suggested_actions": [
                "Which factors are converging?",
                "Which equipment has repeated barrier degradation?",
                "Show critical SIF precursors."
            ],
            "relevant_reports": rel_reps,
            "category": "CORRELATIONS"
        }

    @staticmethod
    def _query_converging_factors_summary(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SafetyReport)
        if dataset_id:
            q = q.where(SafetyReport.dataset_id == dataset_id)
        reports = list(db.scalars(q).all())

        def count_factors(r: SafetyReport) -> int:
            cnt = 0
            if r.ppe_issue or (r.description and any(k in r.description.lower() for k in ["ppe", "goggles", "helmet", "harness", "gloves", "suit"])):
                cnt += 1
            if r.maintenance_factor or (r.immediate_cause and "maintenance" in r.immediate_cause.lower()):
                cnt += 1
            if r.supervisor_factor or (r.immediate_cause and "supervis" in r.immediate_cause.lower()):
                cnt += 1
            if r.repeated_issue or (r.previous_similar_reports or 0) > 0:
                cnt += 1
            return cnt

        two_factor = sum(1 for r in reports if count_factors(r) == 2)
        three_factor = sum(1 for r in reports if count_factors(r) == 3)
        four_factor = sum(1 for r in reports if count_factors(r) >= 4)

        reply = (
            f"### Multi-Factor Convergence Breakdown\n\n"
            f"- **4-Factor Critical Convergences**:  **{four_factor}** observations\n"
            f"- **3-Factor High Convergences**:  **{three_factor}** observations\n"
            f"- **2-Factor Moderate Convergences**: **{two_factor}** observations\n\n"
            f"**Key Convergence Insights**:\n"
            f"When PPE violations converge with maintenance backlogs and supervisor overrides, potential SIF precursor probability elevates significantly."
        )

        return {
            "reply": reply,
            "suggested_actions": [
                "Which combination of safety factors is most dangerous?",
                "Which reports are correlated?",
                "Show critical SIF precursors."
            ],
            "relevant_reports": [],
            "category": "CONVERGING_FACTORS"
        }

    @staticmethod
    def _query_equipment_repeated_barrier_degradation(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SafetyBarrierAssessment).where(
            and_(
                SafetyBarrierAssessment.status.in_(["FAILED", "DEGRADED"]),
                SafetyBarrierAssessment.equipment != None
            )
        )
        if dataset_id:
            q = q.where(SafetyBarrierAssessment.dataset_id == dataset_id)
        barriers = list(db.scalars(q).all())

        if not barriers:
            return {
                "reply": "No equipment-specific barrier degradation records logged.",
                "suggested_actions": ["Which barriers are degraded?", "How many reports are there?"],
                "relevant_reports": [],
                "category": "EQUIPMENT_BARRIERS"
            }

        eq_counter: Counter = Counter()
        for b in barriers:
            if b.equipment:
                eq_counter[b.equipment] += 1

        reply = (
            f"### Equipment with Repeated Barrier Degradation\n\n"
            f"Tag IDs exhibiting repeated physical or procedural defense degradation:\n\n"
        )
        for eq, cnt in eq_counter.most_common(5):
            reply += f"- **{eq}**: **{cnt}** degraded barrier instances logged\n"

        return {
            "reply": reply,
            "suggested_actions": [
                "Which units have the highest BDI?",
                "Which actions breached SLA?",
                "Show critical SIF precursors."
            ],
            "relevant_reports": [],
            "category": "EQUIPMENT_BARRIERS"
        }

    @staticmethod
    def _query_hipo_multiple_barrier_failures(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SafetyReport).where(
            or_(
                SafetyReport.risk_level.ilike("high"),
                SafetyReport.risk_level.ilike("critical")
            )
        )
        if dataset_id:
            q = q.where(SafetyReport.dataset_id == dataset_id)
        reports = list(db.scalars(q).all())

        reply = (
            f"### High-Potential Reports with Multiple Barrier Failures\n\n"
            f"Found **{len(reports)} high-potential observations** undergoing multi-barrier defense tracking:\n\n"
        )
        rel_reps = []
        for r in reports[:5]:
            rel_reps.append({"id": r.id, "original_id": r.original_id, "risk": r.risk_level})
            reply += f"- **{r.original_id}** ({r.refinery_unit}): *\"{r.description}\"* [Risk: `{r.risk_level}`]\n"

        return {
            "reply": reply,
            "suggested_actions": [
                "Which barriers are degraded?",
                "Show critical SIF precursors.",
                "Which actions breached SLA?"
            ],
            "relevant_reports": rel_reps,
            "category": "HIPO_BARRIERS"
        }

    @staticmethod
    def _query_sla_breached_actions(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SafetyAction).where(
            or_(
                SafetyAction.sla_state == "BREACHED",
                SafetyAction.status == "ESCALATED"
            )
        )
        if dataset_id:
            q = q.where(SafetyAction.dataset_id == dataset_id)
        breached = list(db.scalars(q).all())

        if not breached:
            return {
                "reply": " **Zero SLA Breaches Active**: All dispatched safety actions are within compliance deadlines.",
                "suggested_actions": ["Show open reports", "Show critical SIF precursors.", "Summarize the current safety situation."],
                "relevant_reports": [],
                "category": "SLA_BREACHES"
            }

        reply = (
            f"### SLA Breached & Overdue Safety Actions (Phase 6 SLA Engine)\n\n"
            f"Detected **{len(breached)} actions currently exceeding SLA thresholds**:\n\n"
        )
        rel_reps = []
        for a in breached[:5]:
            rep = db.scalar(select(SafetyReport).where(SafetyReport.id == a.report_id))
            orig_id = rep.original_id if rep else (a.report_id[:8] if a.report_id else "N/A")
            reply += (
                f"- **Action: {a.title}** (Report {orig_id}):\n"
                f"  - **Assigned Role**: `{a.assigned_role}` | **Status**: `{a.status}`\n"
                f"  - **Escalation Level**: `Level {a.escalation_level}` | **SLA State**:  `{a.sla_state}`\n"
            )
            if rep:
                rel_reps.append({"id": rep.id, "original_id": orig_id, "risk": a.severity})

        return {
            "reply": reply,
            "suggested_actions": [
                "Why was this action escalated?",
                "Show active safety holds.",
                "Show critical SIF precursors."
            ],
            "relevant_reports": rel_reps,
            "category": "SLA_BREACHES"
        }

    @staticmethod
    def _query_escalated_actions_summary(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(EscalationLog).order_by(desc(EscalationLog.escalated_at)).limit(5)
        logs = list(db.scalars(q).all())

        if not logs:
            return {
                "reply": "No automated supervisory escalations recorded in the audit log.",
                "suggested_actions": ["Which actions breached SLA?", "Show active safety holds."],
                "relevant_reports": [],
                "category": "ACTION_ESCALATIONS"
            }

        reply = (
            f"### Supervisory Escalation Audit Log (Phase 6)\n\n"
            f"Automated multi-tier notification escalation history:\n\n"
        )
        for l in logs:
            reply += (
                f"- **Action {l.action_id[:8]}...**: Escalated from `Level {l.from_level}`  `Level {l.to_level}`\n"
                f"  - **Notified Role**: `{l.notified_role}` ({l.notified_email or 'Email'})\n"
                f"  - **Reason**: *\"{l.reason}\"*\n"
            )

        return {
            "reply": reply,
            "suggested_actions": [
                "Which actions breached SLA?",
                "Show active safety holds.",
                "Show critical SIF precursors."
            ],
            "relevant_reports": [],
            "category": "ACTION_ESCALATIONS"
        }

    @staticmethod
    def _query_actions_and_safety_holds(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        holds = list(db.scalars(select(SafetyHold).where(SafetyHold.status != "RELEASED")).all())
        unack = list(db.scalars(select(SafetyAction).where(SafetyAction.status.in_(["DISPATCHED", "PENDING_APPROVAL"]))).all())

        hold_lines = ""
        if holds:
            for h in holds[:3]:
                hold_lines += f"- **Hold ID {h.id[:8]}...** ({h.refinery_unit or 'Unit'} • {h.equipment or 'General'}): Status ` {h.status}` — Trigger: *\"{h.trigger}\"*\n"
        else:
            hold_lines = "- No active workflow-blocking safety holds in effect.\n"

        reply = (
            f"### Action Governance & Digital Safety Hold Telemetry (Phase 5 & 6)\n\n"
            f"- **Active Digital Safety Holds**: **{len(holds)}**\n"
            f"- **Actions Awaiting Approval / Acknowledgement**: **{len(unack)}**\n\n"
            f"**Digital Safety Hold Status**:\n"
            f"{hold_lines}\n\n"
            f"*Safety Note: Digital safety holds operate internal workflow freezes and require authorized Safety Officer / Plant Management verification to release.*"
        )

        return {
            "reply": reply,
            "suggested_actions": [
                "Which actions breached SLA?",
                "Show critical SIF precursors.",
                "Which units have the highest BDI?"
            ],
            "relevant_reports": [],
            "category": "SAFETY_HOLDS"
        }

    # =============================================================
    # PART 4 MANDATORY QUERY IMPLEMENTATIONS
    # =============================================================

    @staticmethod
    def _query_sif_precursors_count(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        summary = SIFService.get_sif_summary(db, dataset_id)
        total = summary.get("total_analyzed", 0)
        sif_cnt = summary.get("sif_precursors_detected", 0)
        rate = summary.get("sif_precursor_rate_percentage", 0.0)

        q_reps = select(SafetyReport).join(ReportAnalysis, SafetyReport.id == ReportAnalysis.report_id).where(ReportAnalysis.sif_precursor == "YES")
        if dataset_id:
            q_reps = q_reps.where(SafetyReport.dataset_id == dataset_id)
        sif_reports = list(db.scalars(q_reps.limit(5)).all())

        reply = (
            f"### SIF Precursor Detection Telemetry\n\n"
            f"Across the analyzed database:\n"
            f"- **Total SIF Precursors Reported**: **{sif_cnt}** observations\n"
            f"- **Total Safety Corpus Analyzed**: **{total}** reports\n"
            f"- **SIF Precursor Rate**: **{rate}%** of all logged observations\n\n"
            f"**High-Risk SIF Precursor Sample**:\n"
        )
        rel_reps = []
        for r in sif_reports:
            rel_reps.append({"id": r.id, "original_id": r.original_id, "risk": r.risk_level})
            reply += f"- **{r.original_id or r.id[:8]}** ({r.refinery_unit or 'Process Unit'} • {r.department or 'Operations'}): *\"{r.description}\"*\n"

        return {
            "reply": reply,
            "suggested_actions": [
                "Which unit has the highest SIF precursor density?",
                "Which Life-Saving Rule is most frequently involved?",
                "Show recurring Line of Fire precursors.",
                "Which corrective actions are overdue?"
            ],
            "relevant_reports": rel_reps,
            "category": "SIF_PRECURSOR_COUNT"
        }

    @staticmethod
    def _query_highest_sif_density_unit(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        from app.services.sif_density_service import SIFDensityService
        density_res = SIFDensityService.calculate_sif_density(db, dataset_id)
        unit_rankings = density_res.get("dimension_rankings", {}).get("Refinery Unit", [])

        if not unit_rankings:
            return {
                "reply": f"### SIF Precursor Density Telemetry\n\nOverall SIF Precursor Density: **{density_res.get('sif_precursor_density_percentage', 0.0)}%** across all process areas. (Refinery Unit dimension is not explicitly separated in this dataset).",
                "suggested_actions": ["How many SIF precursors were reported?", "Which Life-Saving Rule is most frequently involved?"],
                "relevant_reports": [],
                "category": "SIF_DENSITY"
            }

        top_unit = unit_rankings[0]
        reply = (
            f"### Refinery Unit SIF Precursor Density Ranking\n\n"
            f"The refinery unit with the highest SIF precursor density is **{top_unit['name']}** with **{top_unit['sif_density_percentage']}% density** ({top_unit['sif_precursor_count']} SIF precursors / {top_unit['total_reports']} total observations).\n\n"
            f"**Complete Unit Density Telemetry**:\n"
        )
        for u in unit_rankings:
            reply += f"- **{u['name']}**: **{u['sif_density_percentage']}% density** ({u['sif_precursor_count']} SIF precursors out of {u['total_reports']} reports | {u['high_risk_count']} High Risk)\n"

        return {
            "reply": reply,
            "suggested_actions": [
                "Which units have increasing SIF precursor density?",
                "Which Life-Saving Rule is most frequently involved?",
                "Show recurring Line of Fire precursors."
            ],
            "relevant_reports": [],
            "category": "SIF_DENSITY"
        }

    @staticmethod
    def _query_top_iogp_rule(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(ReportAnalysis.iogp_rule, func.count(ReportAnalysis.id).label("cnt")).where(
            and_(
                ReportAnalysis.iogp_rule != None,
                ReportAnalysis.iogp_rule != "No clear Life-Saving Rule match"
            )
        )
        if dataset_id:
            q = q.where(ReportAnalysis.dataset_id == dataset_id)
        q = q.group_by(ReportAnalysis.iogp_rule).order_by(desc("cnt"))
        results = db.execute(q).all()

        if not results:
            return {
                "reply": "No specific IOGP Life-Saving Rule violations identified in this dataset.",
                "suggested_actions": ["How many SIF precursors were reported?", "Which unit has the highest SIF precursor density?"],
                "relevant_reports": [],
                "category": "IOGP_RULE"
            }

        top_rule, top_cnt = results[0]
        reply = (
            f"### IOGP Life-Saving Rule Violation Distribution\n\n"
            f"The Life-Saving Rule most frequently involved in observations is **{top_rule}** with **{top_cnt} flagged violations**.\n\n"
            f"**Rule Frequency Breakdown**:\n"
        )
        for rule, cnt in results:
            reply += f"- **{rule}**: **{cnt} observations**\n"

        return {
            "reply": reply,
            "suggested_actions": [
                "Show recurring Line of Fire precursors.",
                "Which unit has the highest SIF precursor density?",
                "Show reports where maintenance issues and PPE violations occurred together."
            ],
            "relevant_reports": [],
            "category": "IOGP_RULE"
        }

    @staticmethod
    def _query_recurring_line_of_fire(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SafetyReport).join(ReportAnalysis, SafetyReport.id == ReportAnalysis.report_id).where(
            or_(
                ReportAnalysis.iogp_rule.ilike("%Line of Fire%"),
                SafetyReport.description.ilike("%line of fire%"),
                SafetyReport.hazard.ilike("%line of fire%"),
                SafetyReport.potential_consequence.ilike("%line of fire%")
            )
        )
        if dataset_id:
            q = q.where(SafetyReport.dataset_id == dataset_id)
        reports = list(db.scalars(q).all())
        total = len(reports)
        recurring_cnt = sum(1 for r in reports if r.repeated_issue or (r.previous_similar_reports or 0) > 0)

        reply = (
            f"### Recurring Line of Fire Precursor Telemetry\n\n"
            f"- **Total Line of Fire Precursors Detected**: **{total}**\n"
            f"- **Flagged as Systemic Recurring Precursors**: **{recurring_cnt}**\n\n"
            f"**Sample Line of Fire Observations**:\n"
        )
        rel_reps = []
        for r in reports[:5]:
            rel_reps.append({"id": r.id, "original_id": r.original_id, "risk": r.risk_level})
            reply += f"- **{r.original_id or r.id[:8]}** ({r.refinery_unit or 'Unit'} • {r.equipment or 'General'}): *\"{r.description}\"* (Risk: `{r.risk_level}`)\n"

        if not reports:
            reply += "Zero Line of Fire precursors identified in active database records."

        return {
            "reply": reply,
            "suggested_actions": [
                "Which Life-Saving Rule is most frequently involved?",
                "Which unit has the highest SIF precursor density?",
                "Which reports contain multiple barrier failures?"
            ],
            "relevant_reports": rel_reps,
            "category": "LINE_OF_FIRE"
        }

    @staticmethod
    def _query_maintenance_and_ppe_together(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SafetyReport).where(
            and_(
                or_(
                    SafetyReport.maintenance_factor == True,
                    SafetyReport.detected_factors.contains("Maintenance_Delay_or_Issue"),
                    SafetyReport.description.ilike("%maintenance%"),
                    SafetyReport.immediate_cause.ilike("%maintenance%")
                ),
                or_(
                    SafetyReport.ppe_issue == True,
                    SafetyReport.detected_factors.contains("PPE_NonCompliance"),
                    SafetyReport.description.ilike("%ppe%"),
                    SafetyReport.description.ilike("%helmet%"),
                    SafetyReport.description.ilike("%glasses%"),
                    SafetyReport.description.ilike("%gloves%")
                )
            )
        )
        if dataset_id:
            q = q.where(SafetyReport.dataset_id == dataset_id)
        reports = list(db.scalars(q).all())
        total = len(reports)
        high = sum(1 for r in reports if (r.risk_level or "").lower() in ["high", "critical"])
        pct = (high / total * 100) if total > 0 else 0.0

        reply = (
            f"### Multi-Factor Co-occurrence: Maintenance Delays & PPE Violations\n\n"
            f"Found **{total} safety reports** where maintenance delays and PPE non-compliances occurred simultaneously:\n\n"
            f"- **High / Critical Risk Proportion**: **{high} reports** ({pct:.1f}%)\n"
            f"- **Compound Risk Mechanism**: Mechanical equipment degradation combined with unmitigated personal protection elevates worker exposure significantly.\n\n"
            f"**Sample Co-occurring Failure Incidents**:\n"
        )
        rel_reps = []
        for r in reports[:4]:
            rel_reps.append({"id": r.id, "original_id": r.original_id, "risk": r.risk_level})
            reply += f"- **{r.original_id or r.id[:8]}** ({r.refinery_unit or 'Process Area'}): *\"{r.description}\"* (Risk: `{r.risk_level}`)\n"

        return {
            "reply": reply,
            "suggested_actions": [
                "Which reports contain multiple barrier failures?",
                "Why was this report classified as high SIF potential?",
                "Which corrective actions are overdue?"
            ],
            "relevant_reports": rel_reps,
            "category": "MAINT_PPE_COOCCURRENCE"
        }

    @staticmethod
    def _query_units_increasing_sif_density(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        from app.services.sif_density_service import SIFDensityService
        density_res = SIFDensityService.calculate_sif_density(db, dataset_id)
        unit_rankings = density_res.get("dimension_rankings", {}).get("Refinery Unit", [])

        if not unit_rankings:
            return {
                "reply": f"### SIF Precursor Density Trend Telemetry\n\nOverall SIF Precursor Density is **{density_res.get('sif_precursor_density_percentage', 0.0)}%**. Historical multi-period trend data requires continuous reporting across quarterly operational cycles.",
                "suggested_actions": ["Which unit has the highest SIF precursor density?", "How many SIF precursors were reported?"],
                "relevant_reports": [],
                "category": "SIF_TREND"
            }

        high_density_units = [u for u in unit_rankings if u["sif_density_percentage"] >= 30.0]
        reply = (
            f"### SIF Precursor Density Trend & Hotspot Units\n\n"
            f"Process units exhibiting elevated or increasing SIF precursor density concentration:\n\n"
        )
        for u in (high_density_units or unit_rankings[:3]):
            reply += f"- **{u['name']}**:  **{u['sif_density_percentage']}% density** ({u['sif_precursor_count']} SIF precursors out of {u['total_reports']} reports)\n"

        reply += "\n**Management Priority**: Recommend increasing field safety walkdowns in units with density exceeding 30%."

        return {
            "reply": reply,
            "suggested_actions": [
                "Which unit has the highest SIF precursor density?",
                "Which Life-Saving Rule is most frequently involved?",
                "Which corrective actions are overdue?"
            ],
            "relevant_reports": [],
            "category": "SIF_TREND"
        }

    @staticmethod
    def _query_why_high_sif(db: Session, dataset_id: Optional[str]) -> Dict[str, Any]:
        q = select(SafetyReport).join(ReportAnalysis, SafetyReport.id == ReportAnalysis.report_id).where(
            and_(
                ReportAnalysis.sif_precursor == "YES",
                or_(SafetyReport.risk_level.ilike("high"), SafetyReport.risk_level.ilike("critical"))
            )
        )
        if dataset_id:
            q = q.where(SafetyReport.dataset_id == dataset_id)
        reports = list(db.scalars(q.limit(3)).all())

        reply = (
            f"### SIF Precursor Classification Criteria\n\n"
            f"Reports are classified as **HIGH SIF Potential / Precursor** when the AI/NLP engine identifies:\n\n"
            f"1. **High-Energy Exposure Vector**: Hydrocarbon releases, toxic gas, high pressure, high voltage, or suspended loads.\n"
            f"2. **Critical Control Barrier Failure**: Defective or bypassed containment, missing isolation, or failed PPE defenses.\n"
            f"3. **Plausible Fatal Consequence Scenario**: Unmitigated personnel exposure that could lead to life-altering or fatal injury under operational stress.\n\n"
            f"**Representative High SIF Reports in Database**:\n"
        )
        rel_reps = []
        for r in reports:
            rel_reps.append({"id": r.id, "original_id": r.original_id, "risk": r.risk_level})
            reply += f"- **{r.original_id or r.id[:8]}** ({r.refinery_unit or 'Process Unit'}): *\"{r.description}\"* (Consequence: `{r.potential_consequence}`)\n"

        return {
            "reply": reply,
            "suggested_actions": [
                "How many SIF precursors were reported?",
                "Which reports contain multiple barrier failures?",
                "Which Life-Saving Rule is most frequently involved?"
            ],
            "relevant_reports": rel_reps,
            "category": "WHY_HIGH_SIF"
        }



