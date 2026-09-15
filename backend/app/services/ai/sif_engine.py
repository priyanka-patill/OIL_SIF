from typing import Dict, Any, List, Optional, Tuple


class SIFPrecursorEngine:
    """Evaluates SIF (Serious Injury & Fatality) precursor potential, assigns 
    AI predicted risk, and generates explainable human-readable justifications."""

    HIGH_ENERGY_CONSEQUENCES = [
        "hydrocarbon release",
        "fire",
        "explosion",
        "lost-time injury",
        "fatality",
        "severe chemical exposure"
    ]

    HIGH_RISK_WORK_TYPES = [
        "hot work",
        "confined space",
        "work at height",
        "breakdown maintenance"
    ]

    HIGH_RISK_UNITS = [
        "hydrogen unit",
        "hydrotreating unit",
        "fcc",
        "sulfur recovery unit",
        "cdu",
        "vdu"
    ]

    @classmethod
    def evaluate_sif(
        cls,
        hazard_identified: str,
        ppe_items: List[str],
        violation_type: str,
        recorded_risk: str,
        potential_consequence: Optional[str],
        immediate_cause: Optional[str],
        work_type: Optional[str],
        refinery_unit: Optional[str],
        previous_similar_reports: Optional[int],
        action_status: Optional[str],
        supervisor_factor: Optional[bool] = False,
        maintenance_factor: Optional[bool] = False,
        repeated_issue: Optional[bool] = False,
        high_potential_flag: Optional[bool] = False
    ) -> Tuple[str, str, str, float, List[str], List[str]]:
        """
        Returns:
            (sif_precursor, sif_category, ai_risk_level, confidence, reasoning, org_factors)
        """
        reasons: List[str] = []
        org_factors: List[str] = []
        consequence_lower = (potential_consequence or "").lower().strip()
        work_type_lower = (work_type or "").lower().strip()
        unit_lower = (refinery_unit or "").lower().strip()
        recorded_lower = (recorded_risk or "Medium").capitalize()

        # 1. Analyze Organizational & Multi-Factor Failure Controls
        active_factor_count = 0
        if supervisor_factor:
            active_factor_count += 1
            org_factors.append("Supervisor factor / negligence recorded on observation.")
            reasons.append("Supervisory barrier failure identified in operational oversight.")
        if maintenance_factor:
            active_factor_count += 1
            org_factors.append("Equipment maintenance delay or mechanical defect present.")
            reasons.append("Unresolved maintenance degradation contributed to exposure.")
        if repeated_issue:
            active_factor_count += 1
            org_factors.append("Known recurring safety issue previously flagged and ignored.")
            reasons.append("Systemic recurrence: repeated issue previously documented without effective mitigation.")
        if ppe_items or (violation_type and violation_type != "NONE"):
            active_factor_count += 1

        if active_factor_count >= 3:
            reasons.append(f"Multi-Barrier Collapse: {active_factor_count} safety control barriers failed simultaneously (Compound Precursor Pattern).")

        if previous_similar_reports and previous_similar_reports > 0:
            org_factors.append(f"{previous_similar_reports} previous similar safety observation(s) on record.")
            reasons.append(f"Historical recurrence: {previous_similar_reports} prior similar event(s) recorded for this area/equipment.")
        if action_status and action_status.lower() == "overdue":
            org_factors.append("Assigned corrective action status is currently OVERDUE.")
            reasons.append("Remediation barrier compromised due to overdue corrective action closure.")
        if high_potential_flag:
            org_factors.append("Formally flagged as HIGH POTENTIAL near miss.")
            reasons.append("High Potential Near Miss (HiPo): Credible precursor with potential for catastrophic escalation.")

        # 2. Categorize SIF Exposure
        sif_category = "PPE Integrity & Physical Protection Barrier"
        if "fire" in hazard_identified.lower() or "thermal" in hazard_identified.lower() or "fire" in consequence_lower:
            sif_category = "Thermal / Flash Fire Hazard"
        elif "hydrocarbon" in consequence_lower or "gas" in hazard_identified.lower() or "chemical" in hazard_identified.lower() or "toxic" in consequence_lower:
            sif_category = "Chemical / Hydrocarbon / Toxic Gas Exposure"
        elif "confined" in work_type_lower or "confined" in hazard_identified.lower():
            sif_category = "Confined Space Atmospheric Hazard"
        elif "height" in work_type_lower or "fall" in hazard_identified.lower():
            sif_category = "Work at Height / Fall Hazard"
        elif "rotating" in hazard_identified.lower() or "pump" in hazard_identified.lower() or "vibration" in hazard_identified.lower():
            sif_category = "High Energy Rotating Equipment Hazard"
        elif "overhead" in hazard_identified.lower() or "impact" in hazard_identified.lower() or "helmet" in ppe_items:
            sif_category = "Overhead Impact & Falling Object Hazard"

        # 3. Assess SIF Precursor Potential
        has_high_energy = any(h in hazard_identified.lower() for h in ["thermal", "fire", "hydrocarbon", "gas", "rotating", "impact", "confined", "height", "leakage", "vibration", "explosion"])
        has_critical_consequence = any(c in consequence_lower for c in cls.HIGH_ENERGY_CONSEQUENCES) or ("multiple casualties" in consequence_lower) or ("bleve" in consequence_lower)
        is_critical_work = any(w in work_type_lower for w in cls.HIGH_RISK_WORK_TYPES)
        is_critical_unit = any(u in unit_lower for u in cls.HIGH_RISK_UNITS)

        # Baseline SIF Precursor decision
        if high_potential_flag or has_critical_consequence or (active_factor_count >= 3) or (has_high_energy and (is_critical_work or is_critical_unit)):
            sif_precursor = "YES"
            reasons.append(f"High-energy hazard vector present ({hazard_identified}) in active process environment.")
            if consequence_lower:
                reasons.append(f"Credible potential consequence of high severity: '{potential_consequence}'.")
            if ppe_items:
                reasons.append(f"Physical barrier ({', '.join(ppe_items)}) missing, damaged, or bypassed.")
        elif has_high_energy or is_critical_work or is_critical_unit or (active_factor_count >= 2):
            sif_precursor = "UNCERTAIN"
            reasons.append("Moderate energy exposure identified; escalation contingent on process conditions.")
        else:
            sif_precursor = "NO"
            reasons.append("Low immediate energy transfer potential; localized non-compliance without direct SIF vector.")

        # 4. Assess AI Predicted Risk Level (Preserving Recorded Risk)
        if sif_precursor == "YES":
            if (("multiple casualties" in consequence_lower) or ("major fire" in consequence_lower) or ("bleve" in consequence_lower) or (recorded_lower == "Critical") or (high_potential_flag and active_factor_count >= 3)):
                ai_risk_level = "CRITICAL"
                reasons.append("AI Risk rated CRITICAL due to multi-barrier failure, high potential classification, and catastrophic consequence exposure.")
            elif ("fire" in consequence_lower or "hydrocarbon" in consequence_lower) and (action_status and action_status.lower() == "overdue" or (previous_similar_reports and previous_similar_reports > 1)):
                ai_risk_level = "CRITICAL"
                reasons.append("AI Risk elevated to CRITICAL due to combination of SIF precursor, severe energy consequence, and unresolved/overdue corrective actions.")
            elif any(c in consequence_lower for c in cls.HIGH_ENERGY_CONSEQUENCES) or recorded_lower == "High" or active_factor_count >= 3 or high_potential_flag:
                ai_risk_level = "HIGH"
                reasons.append("AI Risk rated HIGH based on presence of direct SIF precursor and credible severe consequence.")
            else:
                ai_risk_level = "MEDIUM"
                reasons.append("AI Risk evaluated as MEDIUM; significant exposure but contained operational scope.")
        elif sif_precursor == "UNCERTAIN":
            ai_risk_level = "MEDIUM"
            reasons.append("AI Risk rated MEDIUM due to unmitigated behavioral exposure under active refinery operating conditions.")
        else:
            ai_risk_level = "LOW"
            reasons.append("AI Risk evaluated as LOW with minimal escalation probability.")

        # Note any upgrade in risk vs recorded risk
        if recorded_lower == "Low" and ai_risk_level in ["MEDIUM", "HIGH", "CRITICAL"]:
            reasons.append(f"Risk Upgrade Note: Recorded risk is '{recorded_lower}', while AI Pattern Risk is '{ai_risk_level}' due to compound precursor indicators.")
        elif recorded_lower == "Medium" and ai_risk_level in ["HIGH", "CRITICAL"]:
            reasons.append(f"Risk Upgrade Note: Recorded risk is '{recorded_lower}', while AI Pattern Risk is '{ai_risk_level}' given high-consequence potential in {refinery_unit or 'process area'}.")

        # 5. Confidence Score Calculation
        confidence = 0.82
        if len(reasons) >= 3:
            confidence += 0.08
        if has_critical_consequence:
            confidence += 0.05
        if high_potential_flag:
            confidence += 0.03
        confidence = min(0.98, round(confidence, 2))

        return sif_precursor, sif_category, ai_risk_level, confidence, reasons, org_factors
