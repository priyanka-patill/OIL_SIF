"""
Centralized Risk Classification Utility for OIL_SIF.
Single source of truth for normalizing and classifying safety report risk levels.

Primary Risk Levels:
- HIGH
- MEDIUM
- LOW

SIF Precursor (YES/NO) and High Potential Near Miss (YES/NO) are separate independent metrics.
"""

from typing import Dict, Any, Optional, List


def normalize_risk_level(val: Optional[str], fallback_item: Optional[Dict[str, Any]] = None) -> str:
    """
    Safely normalizes any risk level string to strictly one of: 'HIGH', 'MEDIUM', 'LOW'.
    If missing or invalid, calculates an explainable fallback risk level if fallback_item is provided.
    """
    if val is not None and str(val).strip() != "":
        cleaned = str(val).strip().upper()
        
        if cleaned in ("HIGH", "HIGH RISK") or cleaned.startswith("HIGH"):
            return "HIGH"
        if cleaned in ("MEDIUM", "MEDIUM RISK", "MED") or cleaned.startswith("MED"):
            return "MEDIUM"
        if cleaned in ("LOW", "LOW RISK") or cleaned.startswith("LOW"):
            return "LOW"
            
        if cleaned in ("CRITICAL", "SERIOUS", "SEVERE", "FATAL"):
            return "HIGH"
        if cleaned in ("SIGNIFICANT", "MODERATE", "ELEVATED"):
            return "MEDIUM"
        if cleaned in ("MINIMAL", "MINOR", "NEGLIGIBLE"):
            return "LOW"

    # If value is missing or unmapped, calculate fallback from item fields if available
    if fallback_item:
        return classify_risk_from_fields(fallback_item)

    return "MEDIUM"


def get_risk_label(val: Optional[str], fallback_item: Optional[Dict[str, Any]] = None) -> str:
    """Returns normalized risk label: 'HIGH', 'MEDIUM', or 'LOW'."""
    return normalize_risk_level(val, fallback_item)


def get_risk_color(val: Optional[str]) -> str:
    """Returns standard semantic hex color for risk level."""
    norm = normalize_risk_level(val)
    if norm == "HIGH":
        return "#D64545"  # Red / Orange
    if norm == "MEDIUM":
        return "#E5A11A"  # Amber / Yellow
    return "#2E8B57"  # Green


def classify_risk_from_fields(item: Dict[str, Any]) -> str:
    """
    Explainable risk classification based on combination of:
    Severity + Exposure + Existing Controls + Unsafe Condition + Potential Consequence + Recurrence.
    
    Returns strictly 'HIGH', 'MEDIUM', or 'LOW'.
    """
    desc = str(item.get("description") or item.get("Observation") or item.get("Near_Miss_Description") or "").lower()
    hazard = str(item.get("hazard") or "").lower()
    cause = str(item.get("immediate_cause") or item.get("ImmediateCause") or item.get("Immediate_Cause") or "").lower()
    consequence = str(item.get("potential_consequence") or item.get("PotentialConsequence") or item.get("Potential_Consequence") or "").lower()
    work_type = str(item.get("work_type") or item.get("WorkType") or item.get("Work_Type") or "").lower()
    unit = str(item.get("refinery_unit") or item.get("RefineryUnit") or item.get("Refinery_Unit") or "").lower()
    report_type = str(item.get("report_type") or item.get("ReportType") or "").lower()

    high_potential = bool(item.get("high_potential") or item.get("High_Potential_Near_Miss"))
    sif_flag = bool(item.get("sif_precursor") or item.get("SIF_Precursor"))
    
    # 1. HIGH RISK EVALUATION
    # Fatalities, major energy release, critical work without protection, severe consequences
    high_consequence_keywords = [
        "fatality", "death", "severe injury", "lost-time", "lost time",
        "explosion", "fire", "bleve", "hydrocarbon release", "gas leak", "sour gas", "h2s",
        "toxic", "toxic release", "collapse", "electrocution", "amputation", "blowout"
    ]
    high_hazard_work_types = [
        "hot work", "confined space", "work at height", "height", "energy isolation",
        "loto", "electrical", "high pressure", "crane", "heavy lift", "line break"
    ]

    has_high_consequence = any(kw in consequence for kw in high_consequence_keywords) or any(kw in desc for kw in high_consequence_keywords)
    has_high_work_type = any(kw in work_type for kw in high_hazard_work_types) or any(kw in desc for kw in high_hazard_work_types)

    # Multi-factor failure co-occurrence
    factors_count = 0
    if item.get("ppe_issue") or item.get("PPE_NonCompliance") or item.get("ppe_items"):
        factors_count += 1
    if item.get("supervisor_factor") or item.get("Supervisor_Negligence"):
        factors_count += 1
    if item.get("maintenance_factor") or item.get("Maintenance_Delay_or_Issue"):
        factors_count += 1
    if item.get("repeated_issue") or item.get("Repeated_Issue_Ignored"):
        factors_count += 1

    prev_reports = item.get("previous_similar_reports") or item.get("Previous_Similar_Reports") or 0
    try:
        prev_reports = int(prev_reports)
    except (ValueError, TypeError):
        prev_reports = 0

    if has_high_consequence or (has_high_work_type and (sif_flag or high_potential or factors_count >= 2)) or (high_potential and factors_count >= 2) or factors_count >= 3 or (prev_reports >= 3 and has_high_work_type):
        return "HIGH"

    # 2. MEDIUM RISK EVALUATION
    # Meaningful PPE non-compliance, equipment degradation, moderate exposure, recurring issues
    medium_consequence_keywords = [
        "minor injury", "first aid", "equipment damage", "leak", "spill",
        "degradation", "corrosion", "overdue", "malfunction", "uncontained", "exposure"
    ]
    has_medium_consequence = any(kw in consequence for kw in medium_consequence_keywords) or any(kw in desc for kw in medium_consequence_keywords)
    
    if has_medium_consequence or factors_count >= 1 or has_high_work_type or high_potential or sif_flag or prev_reports >= 1 or "unsafe" in report_type:
        return "MEDIUM"

    # 3. LOW RISK EVALUATION
    return "LOW"

