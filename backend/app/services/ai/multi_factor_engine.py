import re
from typing import Dict, Any, List, Optional, Tuple
from app.models.safety_report import SafetyReport


class MultiFactorEngine:
    """
    Multi-Factor Swiss Cheese Correlation & Escalation Engine.
    Detects situations where multiple weak controls or risk factors align simultaneously,
    evaluating compound risk escalation and providing evidence-linked explanations.
    """

    FACTOR_PATTERNS = {
        "PPE Non-Compliance": [r"\bppe\b", r"\bhelmet\b", r"\bgoggles?\b", r"\bgloves?\b", r"\bboots?\b", r"\bharness\b", r"\bvisor\b", r"\bmask\b"],
        "Maintenance Delay or Defect": [r"\bmaintenance\b", r"\bdelay(ed)?\b", r"\bdefect(ive)?\b", r"\bbroken\b", r"\bleak(age)?\b", r"\bvibration\b", r"\bworn\s+out\b"],
        "Repeated Issue Ignored": [r"\brepeat(ed)?\b", r"\brecurr(ing|ence)\b", r"\bprevious(ly)?\b", r"\bignored\b", r"\bflagged\s+before\b"],
        "Weak Supervisory Oversight": [r"\bsupervis(or|ion)\b", r"\boversight\b", r"\bnegligence\b", r"\bunsupervised\b", r"\black\s+of\s+supervision\b"],
        "Contractor Involvement": [r"\bcontractor\b", r"\bvendor\b", r"\bthird[\s-]party\b", r"\bsub[\s-]contractor\b"],
        "Work Authorization Defect": [r"\bpermit\b", r"\bptw\b", r"\bjsa\b", r"\bunauthorized\b", r"\bwithout\s+permit\b", r"\bexpired\s+permit\b"],
        "Missing Energy Isolation": [r"\bloto\b", r"\bisolat(ed|ion)\b", r"\benergized\b", r"\bde[\s-]energiz(ed|ation)\b", r"\bzero\s+energy\b"],
        "Missing Barricading": [r"\bbarricade\b", r"\bwarning\s+tape\b", r"\bflagging\b", r"\bunfenced\b", r"\bopen\s+grating\b"],
        "High-Energy Process Exposure": [r"\bpressur(e|ized)\b", r"\bhigh[\s-]voltage\b", r"\bflammable\b", r"\btoxic\b", r"\bhydrocarbon\b", r"\bhot\s+work\b", r"\bheight\b", r"\bconfined\b"],
        "Unresolved Corrective Action": [r"\boverdue\b", r"\bunresolved\b", r"\bopen\s+action\b", r"\bpending\s+remediation\b"],
        "Repeated Near Miss": [r"\bnear\s+miss\b", r"\bhipo\b", r"\bhigh\s+potential\b", r"\bsimilar\s+event\b"]
    }

    @classmethod
    def evaluate_multi_factor_exposure(
        cls,
        report: SafetyReport,
        hazard_identified: str,
        ppe_items: List[str],
        iogp_rule: str,
        is_recurring: bool
    ) -> Dict[str, Any]:
        """
        Evaluates report narrative, flags, and metadata for compound factor alignment.
        Returns:
            {
                "compound_factor_count": int,
                "detected_compound_factors": List[str],
                "multi_barrier_degradation": bool,
                "critical_sif_precursor": bool,
                "risk_escalation_contributors": List[str],
                "escalation_summary": str
            }
        """
        combined_text = f"{report.description or ''} {report.immediate_cause or ''} {report.potential_consequence or ''} {hazard_identified or ''}".lower()
        detected_factors = []
        contributors = []

        # 1. PPE non-compliance
        if ppe_items or report.ppe_issue or any(re.search(pat, combined_text) for pat in cls.FACTOR_PATTERNS["PPE Non-Compliance"]):
            detected_factors.append("PPE Non-Compliance")
            ppe_name = ", ".join(ppe_items) if ppe_items else "required protective barrier"
            contributors.append(f"Physical Protection Failure: Worker exposed without {ppe_name}.")

        # 2. Maintenance delay or issue
        if report.maintenance_factor or any(re.search(pat, combined_text) for pat in cls.FACTOR_PATTERNS["Maintenance Delay or Defect"]):
            detected_factors.append("Maintenance Delay or Defect")
            contributors.append("Asset Integrity Compromise: Unresolved equipment maintenance delay or mechanical defect.")

        # 3. Repeated issue / historical recurrence
        if is_recurring or report.repeated_issue or (report.previous_similar_reports or 0) > 0:
            detected_factors.append("Repeated Issue Ignored")
            prev_cnt = report.previous_similar_reports or 1
            contributors.append(f"Institutional Recurrence: Known safety hazard previously recorded ({prev_cnt} prior report(s)).")

        # 4. Weak supervisory oversight
        if report.supervisor_factor or any(re.search(pat, combined_text) for pat in cls.FACTOR_PATTERNS["Weak Supervisory Oversight"]):
            detected_factors.append("Weak Supervisory Oversight")
            contributors.append("Administrative Control Failure: Inadequate supervisory field check or oversight.")

        # 5. Contractor involvement
        if any(re.search(pat, combined_text) for pat in cls.FACTOR_PATTERNS["Contractor Involvement"]):
            detected_factors.append("Contractor Involvement")
            contributors.append("Workforce Transition Vector: Contractor / third-party personnel executing high-risk task.")

        # 6. Work authorization defect
        if any(re.search(pat, combined_text) for pat in cls.FACTOR_PATTERNS["Work Authorization Defect"]) or iogp_rule == "Work Authorisation":
            detected_factors.append("Work Authorization Defect")
            contributors.append("Procedural Control Failure: Operation conducted without verified Permit-To-Work (PTW).")

        # 7. Missing energy isolation
        if any(re.search(pat, combined_text) for pat in cls.FACTOR_PATTERNS["Missing Energy Isolation"]) or iogp_rule == "Energy Isolation":
            detected_factors.append("Missing Energy Isolation")
            contributors.append("Energy Barrier Breached: Line breakdown or maintenance active without verified LOTO isolation.")

        # 8. Missing barricading
        if any(re.search(pat, combined_text) for pat in cls.FACTOR_PATTERNS["Missing Barricading"]):
            detected_factors.append("Missing Barricading")
            contributors.append("Exclusion Zone Failure: Active work zone lacks physical warning barricades or warning tape.")

        # 9. High energy process exposure
        if any(re.search(pat, combined_text) for pat in cls.FACTOR_PATTERNS["High-Energy Process Exposure"]) or iogp_rule in ["Hot Work", "Confined Space", "Working at Height", "Line of Fire"]:
            detected_factors.append("High-Energy Process Exposure")
            contributors.append(f"Severe Energy Hazard Vector: Active exposure in process operating environment ({hazard_identified}).")

        # 10. Unresolved corrective action
        if (report.action_status or "").lower() == "overdue":
            detected_factors.append("Unresolved Corrective Action")
            contributors.append("Remediation Lag: Assigned corrective action is overdue and unverified.")

        # Deduplicate factor lists
        unique_factors = list(dict.fromkeys(detected_factors))
        compound_count = len(unique_factors)

        multi_barrier_degradation = compound_count >= 2
        critical_sif_precursor = compound_count >= 3 or bool(report.high_potential)

        if compound_count >= 4:
            summary = f"CRITICAL SIF PRECURSOR & MULTI-FACTOR BARRIER DEGRADATION: Severe alignment of {compound_count} simultaneous control failures."
        elif compound_count >= 3:
            summary = f"CRITICAL SIF PRECURSOR: Compound interaction between {compound_count} distinct barrier failure vectors."
        elif compound_count == 2:
            summary = f"MULTI-FACTOR BARRIER DEGRADATION: Dual-factor compound interaction between {unique_factors[0]} and {unique_factors[1]}."
        else:
            summary = "Single-factor safety observation with localized exposure envelope."

        return {
            "compound_factor_count": compound_count,
            "detected_compound_factors": unique_factors,
            "multi_barrier_degradation": multi_barrier_degradation,
            "critical_sif_precursor": critical_sif_precursor,
            "risk_escalation_contributors": contributors,
            "escalation_summary": summary
        }
