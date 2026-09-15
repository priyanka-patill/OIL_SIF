import re
from typing import Dict, Any, List, Optional, Tuple


class NLPEngine:
    """Dynamic NLP and entity extraction engine for industrial safety narratives."""

    PPE_VOCABULARY = {
        "safety helmet": [r"\bhelmet\b", r"\bhard\s?hat\b", r"\bhead\s?protection\b"],
        "safety shoes": [r"\bsafety\s?shoes?\b", r"\bboots?\b", r"\bfootwear\b", r"\bsteel\s?toe\b"],
        "face shield": [r"\bface\s?shield\b", r"\bvisor\b"],
        "safety goggles": [r"\bgoggles?\b", r"\bsafety\s?glasses\b", r"\beye\s?protection\b", r"\beye\s?wear\b"],
        "fire-resistant clothing": [r"\bfire[\s-]resistant\b", r"\bfr[\s-]clothing\b", r"\bfr[\s-]suit\b", r"\bcoverall\b", r"\bnomex\b"],
        "safety gloves": [r"\bgloves?\b", r"\bhand\s?protection\b"],
        "ear protection": [r"\bear\s?protection\b", r"\bear\s?plugs?\b", r"\bearmuffs?\b", r"\bhearing\s?protection\b"],
        "respirator": [r"\brespirator\b", r"\bdust\s?mask\b", r"\bmask\b", r"\bscba\b", r"\bbreathing\s?apparatus\b"],
        "safety harness": [r"\bharness\b", r"\bfall\s?arrest\b", r"\blanyard\b", r"\bsafety\s?belt\b"]
    }

    VIOLATION_PATTERNS = {
        "MISSING_PPE": [
            r"\bwithout\b", r"\bno\b", r"\bnot\s+wearing\b", r"\bmissing\b",
            r"\blacking\b", r"\babsent\b", r"\bfailure\s+to\s+wear\b", r"\bfailed\s+to\s+use\b"
        ],
        "DAMAGED_PPE": [
            r"\bdamaged\b", r"\bbroken\b", r"\bcracked\b", r"\btorn\b",
            r"\bdefective\b", r"\bworn\s+out\b", r"\bdeteriorated\b"
        ],
        "IMPROPER_PPE": [
            r"\bimproper\b", r"\bincorrect\b", r"\bwrong\s+type\b",
            r"\binappropriate\b", r"\bunrated\b", r"\bloose\b"
        ],
        "BYPASS_PPE": [
            r"\bbypassed\b", r"\bremoved\b", r"\brefused\b", r"\bdisregarded\b", r"\bignored\b"
        ]
    }

    ENERGY_HAZARD_PATTERNS = {
        "Thermal / Flash Fire": [r"\bwelder\b", r"\bwelding\b", r"\bhot\s?work\b", r"\bflash\s?fire\b", r"\bflame\b", r"\bspark\b", r"\bfire\b", r"\bignition\b"],
        "Chemical / Toxic Gas": [r"\bhydrogen\b", r"\bh2s\b", r"\bsulfur\b", r"\btoxic\b", r"\bacid\b", r"\bchemical\b", r"\bgas\s?leak\b", r"\bvapor\b"],
        "High Energy Mechanical / Rotating": [r"\bpump\b", r"\bcompressor\b", r"\bturbine\b", r"\brotating\b", r"\bmachinery\b", r"\bpressure\b", r"\bhydraulic\b"],
        "Falling Object / Impact": [r"\boverhead\b", r"\bfalling\b", r"\bimpact\b", r"\bprojectile\b", r"\bcrane\b", r"\brigger\b", r"\bpipe\s?rack\b"],
        "Confined Space": [r"\bconfined\s?space\b", r"\bvessel\s?entry\b", r"\btank\s?interior\b"],
        "Fall from Height": [r"\bheight\b", r"\bscaffold\b", r"\belevated\b", r"\bladder\b"]
    }

    @classmethod
    def extract_text_fields(cls, report: Any) -> Dict[str, str]:
        """Dynamically collect all non-empty descriptive text fields available on report."""
        text_data = {}
        # Check canonical attributes
        for attr in ["description", "hazard", "unsafe_act", "unsafe_condition", "immediate_cause", "potential_consequence", "corrective_action"]:
            val = getattr(report, attr, None)
            if val and str(val).strip():
                text_data[attr] = str(val).strip()

        # Check raw_data keys if canonical attributes were empty
        if hasattr(report, "raw_data") and isinstance(report.raw_data, dict):
            for k, v in report.raw_data.items():
                if v and isinstance(v, str) and len(v.strip()) > 3:
                    if k.lower() not in [k2.lower() for k2 in text_data.keys()]:
                        text_data[k] = v.strip()

        return text_data

    @classmethod
    def extract_ppe_items(cls, combined_text: str) -> List[str]:
        found_items = []
        text_lower = combined_text.lower()
        for ppe_name, patterns in cls.PPE_VOCABULARY.items():
            for pat in patterns:
                if re.search(pat, text_lower):
                    found_items.append(ppe_name)
                    break
        return found_items

    @classmethod
    def detect_violation_modality(cls, combined_text: str) -> str:
        text_lower = combined_text.lower()
        for modality, patterns in cls.VIOLATION_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, text_lower):
                    return modality
        return "MISSING_PPE"  # Default for PPE non-compliance near misses

    @classmethod
    def identify_hazard_and_exposure(
        cls,
        combined_text: str,
        department: Optional[str] = None,
        work_type: Optional[str] = None,
        refinery_unit: Optional[str] = None,
        ppe_items: List[str] = None
    ) -> Tuple[str, str]:
        text_lower = combined_text.lower()
        
        # 1. Detect Energy Hazard
        detected_hazards = []
        for hazard_type, patterns in cls.ENERGY_HAZARD_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, text_lower):
                    detected_hazards.append(hazard_type)
                    break

        # Context-based hazard inference if text didn't match directly
        if not detected_hazards:
            if work_type and "hot work" in work_type.lower():
                detected_hazards.append("Thermal / Flash Fire")
            elif work_type and "confined space" in work_type.lower():
                detected_hazards.append("Confined Space Atmospheric / Toxic Hazard")
            elif work_type and "height" in work_type.lower():
                detected_hazards.append("Fall from Elevated Structure")
            elif refinery_unit and ("hydrogen" in refinery_unit.lower() or "hydrotreat" in refinery_unit.lower()):
                detected_hazards.append("High-Pressure Hydrocarbon & Flammable Gas Exposure")
            elif refinery_unit and "sulfur" in refinery_unit.lower():
                detected_hazards.append("Toxic H2S & Chemical Vapor Hazard")
            else:
                detected_hazards.append("Process Area Overhead Impact / Mechanical Hazard")

        hazard_str = " & ".join(detected_hazards)

        # 2. Identify Exposure Target
        dept_str = department if department else "Field Personnel"
        wt_str = f" during {work_type}" if work_type else ""
        ppe_str = f" without {', '.join(ppe_items)}" if ppe_items else " with compromised protective barrier"
        
        exposure_str = f"{dept_str} executing operations{wt_str}{ppe_str}"

        return hazard_str, exposure_str
