import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.models.safety_report import SafetyReport
from app.utils.risk_classifier import normalize_risk_level


class DataNormalizer:
    """Transforms raw DataFrame rows into both raw JSON records and 
    canonical SafetyReport models without mutating original data."""

    @staticmethod
    def _clean_val(val: Any) -> Any:
        if pd.isna(val) or val is None:
            return None
        if isinstance(val, (np.bool_, bool)):
            return bool(val)
        if isinstance(val, (np.integer, int)):
            return int(val)
        if isinstance(val, (np.floating, float)):
            return float(val)
        if isinstance(val, (pd.Timestamp, datetime)):
            return val
        val_str = str(val).strip()
        return val_str if val_str != "" else None

    @staticmethod
    def _parse_bool(val: Any) -> Optional[bool]:
        if val is None or pd.isna(val):
            return None
        if isinstance(val, (bool, np.bool_)):
            return bool(val)
        val_str = str(val).strip().lower()
        if val_str in ("true", "1", "yes", "t", "y"):
            return True
        if val_str in ("false", "0", "no", "f", "n"):
            return False
        return None

    @staticmethod
    def _parse_datetime(val: Any) -> Optional[datetime]:
        if val is None or pd.isna(val):
            return None
        if isinstance(val, datetime):
            return val
        if isinstance(val, pd.Timestamp):
            return val.to_pydatetime()
        try:
            dt = pd.to_datetime(val)
            if pd.isna(dt):
                return None
            return dt.to_pydatetime() if isinstance(dt, pd.Timestamp) else dt
        except Exception:
            return None

    @classmethod
    def normalize_dataframe(
        cls,
        df: pd.DataFrame,
        dataset_id: str,
        dataset_name: str,
        columns_meta: List[Dict[str, Any]]
    ) -> List[SafetyReport]:
        """Convert DataFrame rows into SafetyReport ORM objects."""
        # Create mapping of canonical field to source column name
        canonical_to_source = {}
        for col in columns_meta:
            canonical_field = col.get("mapped_canonical_field")
            if canonical_field:
                canonical_to_source[canonical_field] = col["original_name"]

        reports: List[SafetyReport] = []

        for idx, row in df.iterrows():
            # Build 100% complete source raw_data representation
            raw_dict = {}
            for col_name in df.columns:
                raw_val = row[col_name]
                cleaned = cls._clean_val(raw_val)
                # Ensure datetime is string-formatted for JSON serialization
                if isinstance(cleaned, (datetime, pd.Timestamp)):
                    raw_dict[col_name] = cleaned.isoformat()
                else:
                    raw_dict[col_name] = cleaned

            # Extract canonical fields strictly from mapped source columns
            def get_field(canonical_name: str) -> Any:
                src_col = canonical_to_source.get(canonical_name)
                if src_col is not None and src_col in row:
                    return cls._clean_val(row[src_col])
                return None

            # Parse types appropriately
            orig_id = get_field("original_id")
            if orig_id is not None:
                orig_id = str(orig_id)

            report_date = cls._parse_datetime(get_field("report_date"))
            
            prev_reports = get_field("previous_similar_reports")
            if prev_reports is not None:
                try:
                    prev_reports = int(float(prev_reports))
                except (ValueError, TypeError):
                    prev_reports = None

            # Detect active safety factors for this specific record
            detected_factors_list = []
            if cls._parse_bool(get_field("ppe_issue")) is True:
                detected_factors_list.append("PPE_NonCompliance")
            if cls._parse_bool(get_field("supervisor_factor")) is True:
                detected_factors_list.append("Supervisor_Negligence")
            if cls._parse_bool(get_field("maintenance_factor")) is True:
                detected_factors_list.append("Maintenance_Delay_or_Issue")
            if cls._parse_bool(get_field("repeated_issue")) is True:
                detected_factors_list.append("Repeated_Issue_Ignored")

            # Check for any dynamic factor columns not in standard 4
            for col_name in df.columns:
                if col_name not in ["PPE_NonCompliance", "Supervisor_Negligence", "Maintenance_Delay_or_Issue", "Repeated_Issue_Ignored", "High_Potential_Near_Miss"]:
                    if any(term in col_name.lower() for term in ["violation", "failure", "negligence", "delay", "hazard_factor", "factor"]):
                        raw_val = row[col_name]
                        if cls._parse_bool(raw_val) is True:
                            detected_factors_list.append(col_name)

            factor_cnt = len(detected_factors_list)
            is_hipo = cls._parse_bool(get_field("high_potential")) is True
            
            # Determine relationship type
            if factor_cnt > 1:
                rel_type = "derived_combination"
            elif is_hipo:
                rel_type = "high_potential"
            else:
                rel_type = "independent_observation"

            raw_risk = get_field("risk_level")
            normalized_risk = normalize_risk_level(raw_risk, fallback_item=raw_dict)

            report = SafetyReport(
                dataset_id=dataset_id,
                original_id=orig_id,
                raw_data=raw_dict,
                source_dataset=dataset_name,
                report_date=report_date,
                location=str(get_field("location")) if get_field("location") else None,
                refinery_unit=str(get_field("refinery_unit")) if get_field("refinery_unit") else None,
                equipment=str(get_field("equipment")) if get_field("equipment") else None,
                work_type=str(get_field("work_type")) if get_field("work_type") else None,
                department=str(get_field("department")) if get_field("department") else None,
                report_type=str(get_field("report_type")) if get_field("report_type") else None,
                description=str(get_field("description")) if get_field("description") else None,
                hazard=str(get_field("hazard")) if get_field("hazard") else None,
                unsafe_act=str(get_field("unsafe_act")) if get_field("unsafe_act") else None,
                unsafe_condition=str(get_field("unsafe_condition")) if get_field("unsafe_condition") else None,
                ppe_issue=cls._parse_bool(get_field("ppe_issue")),
                immediate_cause=str(get_field("immediate_cause")) if get_field("immediate_cause") else None,
                potential_consequence=str(get_field("potential_consequence")) if get_field("potential_consequence") else None,
                risk_level=normalized_risk,
                sif_precursor=cls._parse_bool(get_field("sif_precursor")),
                high_potential=cls._parse_bool(get_field("high_potential")),
                previous_similar_reports=prev_reports,
                repeated_issue=cls._parse_bool(get_field("repeated_issue")),
                supervisor_factor=cls._parse_bool(get_field("supervisor_factor")),
                maintenance_factor=cls._parse_bool(get_field("maintenance_factor")),
                corrective_action=str(get_field("corrective_action")) if get_field("corrective_action") else None,
                action_status=str(get_field("action_status")) if get_field("action_status") else None,
                detected_factors=detected_factors_list,
                factor_count=factor_cnt,
                relationship_type=rel_type,
                related_report_ids=[]
            )
            reports.append(report)

        return reports
