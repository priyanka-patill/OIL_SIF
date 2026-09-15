import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.models.data_quality import DataQualitySummary


class DataQualityEngine:
    """Comprehensive data quality profiling engine calculating completeness, 
    uniqueness, validity, constant fields, and health score."""

    @classmethod
    def calculate_quality_summary(
        cls,
        df: pd.DataFrame,
        dataset_id: str,
        columns_meta: List[Dict[str, Any]]
    ) -> DataQualitySummary:
        total_rows = len(df)
        total_columns = len(df.columns)
        
        if total_rows == 0:
            return DataQualitySummary(
                dataset_id=dataset_id,
                total_rows=0,
                total_columns=total_columns,
                valid_records_count=0,
                missing_values_count=0,
                duplicate_ids_count=0,
                invalid_dates_count=0,
                constant_fields_count=0,
                empty_columns_count=total_columns,
                data_quality_score=0.0,
                column_metrics={}
            )

        # 1. Missing values calculation
        total_cells = total_rows * total_columns
        total_missing = int(df.isna().sum().sum())
        missing_rate = (total_missing / total_cells) if total_cells > 0 else 0.0

        # 2. Constant & Empty columns
        constant_fields_count = 0
        empty_columns_count = 0
        column_metrics = {}

        for col_meta in columns_meta:
            col_name = col_meta["original_name"]
            nulls = col_meta["null_count"]
            uniques = col_meta["unique_count"]
            is_const = col_meta["is_constant"]

            if is_const:
                constant_fields_count += 1
            if nulls == total_rows:
                empty_columns_count += 1

            null_pct = round((nulls / total_rows) * 100, 2) if total_rows > 0 else 0.0

            column_metrics[col_name] = {
                "detected_type": col_meta.get("detected_data_type", "STRING"),
                "semantic_type": col_meta.get("semantic_type", "UNKNOWN"),
                "mapped_canonical_field": col_meta.get("mapped_canonical_field"),
                "null_count": nulls,
                "null_percentage": null_pct,
                "unique_count": uniques,
                "is_constant": is_const,
                "constant_value": col_meta.get("constant_value"),
                "sample_values": col_meta.get("sample_values", [])
            }

        # 3. Duplicate ID check
        duplicate_ids_count = 0
        id_col = None
        for col_meta in columns_meta:
            if col_meta.get("mapped_canonical_field") == "original_id":
                id_col = col_meta["original_name"]
                break
        
        if id_col and id_col in df.columns:
            non_null_ids = df[id_col].dropna()
            duplicate_ids_count = int(len(non_null_ids) - len(non_null_ids.unique()))
        else:
            # Check full row duplicates
            duplicate_ids_count = int(df.duplicated().sum())

        # 4. Date validation & date range
        invalid_dates_count = 0
        date_range_start = None
        date_range_end = None
        date_col = None

        for col_meta in columns_meta:
            if col_meta.get("mapped_canonical_field") == "report_date":
                date_col = col_meta["original_name"]
                break
        
        if date_col and date_col in df.columns:
            series = df[date_col].dropna()
            parsed_dates = []
            for d in series:
                try:
                    if isinstance(d, (datetime, pd.Timestamp)):
                        parsed_dates.append(d)
                    else:
                        parsed = pd.to_datetime(d)
                        if not pd.isna(parsed):
                            parsed_dates.append(parsed)
                        else:
                            invalid_dates_count += 1
                except Exception:
                    invalid_dates_count += 1
            
            if parsed_dates:
                min_dt = min(parsed_dates)
                max_dt = max(parsed_dates)
                date_range_start = min_dt.to_pydatetime() if isinstance(min_dt, pd.Timestamp) else min_dt
                date_range_end = max_dt.to_pydatetime() if isinstance(max_dt, pd.Timestamp) else max_dt

        # 5. Valid records count (records with non-null ID and valid core fields)
        if id_col and id_col in df.columns:
            valid_mask = df[id_col].notna() & (df[id_col].astype(str).str.strip() != "")
            valid_records_count = int(valid_mask.sum())
        else:
            valid_records_count = total_rows - int(df.isna().all(axis=1).sum())

        # 6. Overall Data Quality Score (0 to 100)
        # Deduct penalties for missingness, duplicate IDs, invalid dates, and completely empty columns
        completeness_score = max(0.0, 100.0 - (missing_rate * 100.0))
        uniqueness_penalty = (duplicate_ids_count / total_rows * 40.0) if total_rows > 0 else 0.0
        date_validity_penalty = (invalid_dates_count / total_rows * 30.0) if total_rows > 0 else 0.0
        empty_col_penalty = (empty_columns_count / total_columns * 30.0) if total_columns > 0 else 0.0

        raw_score = completeness_score - uniqueness_penalty - date_validity_penalty - empty_col_penalty
        quality_score = max(0.0, min(100.0, round(raw_score, 1)))

        return DataQualitySummary(
            dataset_id=dataset_id,
            calculated_at=datetime.utcnow(),
            total_rows=total_rows,
            total_columns=total_columns,
            valid_records_count=valid_records_count,
            missing_values_count=total_missing,
            duplicate_ids_count=duplicate_ids_count,
            invalid_dates_count=invalid_dates_count,
            constant_fields_count=constant_fields_count,
            empty_columns_count=empty_columns_count,
            data_quality_score=quality_score,
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            column_metrics=column_metrics
        )
