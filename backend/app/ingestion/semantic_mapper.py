import re
from typing import Dict, Any, Optional, Tuple
from app.utils.constants import SEMANTIC_PATTERNS


class SemanticMapper:
    """Intelligently detects semantic meaning of fields and maps source columns 
    to the canonical safety report model."""

    SEMANTIC_TYPE_MAP = {
        "original_id": "ID",
        "report_date": "DATE",
        "refinery_unit": "LOCATION",
        "location": "LOCATION",
        "equipment": "EQUIPMENT",
        "work_type": "WORK_TYPE",
        "department": "DEPARTMENT",
        "description": "NARRATIVE",
        "hazard": "NARRATIVE",
        "unsafe_act": "NARRATIVE",
        "unsafe_condition": "NARRATIVE",
        "ppe_issue": "FLAG",
        "supervisor_factor": "FLAG",
        "maintenance_factor": "FLAG",
        "repeated_issue": "FLAG",
        "high_potential": "FLAG",
        "sif_precursor": "FLAG",
        "previous_similar_reports": "NUMERIC",
        "immediate_cause": "CAUSE",
        "potential_consequence": "CONSEQUENCE",
        "risk_level": "RISK_LEVEL",
        "corrective_action": "ACTION",
        "action_status": "STATUS"
    }

    @classmethod
    def match_column(cls, col_name: str, detected_data_type: str) -> Tuple[Optional[str], str]:
        """Returns (canonical_field_name, semantic_type)."""
        clean_name = col_name.strip().lower()
        normalized_name = re.sub(r"[\s_]+", "_", clean_name)

        # 1. Exact or regex match against known semantic patterns
        for canonical_field, patterns in SEMANTIC_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, normalized_name, re.IGNORECASE) or re.match(pattern, clean_name, re.IGNORECASE):
                    semantic_type = cls.SEMANTIC_TYPE_MAP.get(canonical_field, "UNKNOWN")
                    return canonical_field, semantic_type

        # 2. Heuristic fallback based on keywords in column name
        if "id" in normalized_name or "no" in normalized_name or "code" in normalized_name:
            if "equip" in normalized_name:
                return "equipment", "EQUIPMENT"
            if "unit" in normalized_name:
                return "refinery_unit", "LOCATION"
            return "original_id", "ID"
        
        if "date" in normalized_name or "time" in normalized_name:
            return "report_date", "DATE"
        
        if "unit" in normalized_name or "plant" in normalized_name:
            return "refinery_unit", "LOCATION"
            
        if "dept" in normalized_name or "contractor" in normalized_name:
            return "department", "DEPARTMENT"

        if "desc" in normalized_name or "narrative" in normalized_name or "summary" in normalized_name:
            return "description", "NARRATIVE"

        # 3. Fallback semantic type based on data type
        if detected_data_type == "DATETIME":
            return None, "DATE"
        elif detected_data_type == "BOOLEAN":
            return None, "FLAG"
        elif detected_data_type in ["INTEGER", "FLOAT"]:
            return None, "NUMERIC"
        elif detected_data_type == "TEXT":
            return None, "NARRATIVE"
        
        return None, "UNKNOWN"

    @classmethod
    def enrich_column_metadata(cls, column_meta: Dict[str, Any]) -> Dict[str, Any]:
        """Attach detected semantic type and canonical field mapping to column metadata."""
        canonical_field, semantic_type = cls.match_column(
            column_meta["original_name"],
            column_meta["detected_data_type"]
        )
        column_meta["semantic_type"] = semantic_type
        column_meta["mapped_canonical_field"] = canonical_field
        return column_meta
