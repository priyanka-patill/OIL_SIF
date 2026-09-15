import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Tuple
from app.utils.validators import sanitize_column_name


class SchemaDetector:
    """Dynamically analyzes DataFrame columns to infer physical data types, 
    detect constant fields, nullity, and sample values."""

    @staticmethod
    def detect_column_type(series: pd.Series) -> str:
        # Drop NA to analyze active values
        non_null = series.dropna()
        if non_null.empty:
            return "STRING"

        # Check for boolean
        if pd.api.types.is_bool_dtype(series):
            return "BOOLEAN"
        
        # Check if values are boolean-like strings/integers
        unique_lower = set(str(v).strip().lower() for v in non_null.unique())
        if unique_lower.issubset({"true", "false", "yes", "no", "t", "f", "1", "0"}) and len(unique_lower) <= 2:
            # If all are boolean terms or 0/1
            if unique_lower.issubset({"true", "false"}):
                return "BOOLEAN"

        # Check for datetime
        if pd.api.types.is_datetime64_any_dtype(series):
            return "DATETIME"
        
        # Try datetime conversion if string
        if pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series):
            # Sample first 20 non-null values to test date parsing
            sample = non_null.head(20)
            date_matches = 0
            for val in sample:
                val_str = str(val).strip()
                if len(val_str) >= 8 and any(sep in val_str for sep in ["-", "/", "."]):
                    try:
                        pd.to_datetime(val_str)
                        date_matches += 1
                    except (ValueError, TypeError):
                        pass
            if len(sample) > 0 and date_matches / len(sample) >= 0.8:
                return "DATETIME"

        # Check for numeric
        if pd.api.types.is_integer_dtype(series):
            return "INTEGER"
        
        if pd.api.types.is_float_dtype(series):
            # Check if all floats are actually integer representations (e.g. 2.0)
            if (non_null % 1 == 0).all():
                return "INTEGER"
            return "FLOAT"

        # Check for text length (Narrative vs short string)
        if pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series):
            avg_len = non_null.astype(str).str.len().mean()
            max_len = non_null.astype(str).str.len().max()
            if max_len > 120 or avg_len > 60:
                return "TEXT"
            return "STRING"

        return "STRING"

    @classmethod
    def analyze_schema(cls, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Inspect all columns in the DataFrame and return comprehensive metadata."""
        columns_meta = []
        total_rows = len(df)

        for idx, col in enumerate(df.columns):
            series = df[col]
            clean_name = str(col).strip()
            sanitized = sanitize_column_name(clean_name)
            detected_type = cls.detect_column_type(series)
            
            # Missing value count
            null_count = int(series.isna().sum())
            is_nullable = null_count > 0
            
            # Unique non-null values
            non_null_series = series.dropna()
            unique_vals = non_null_series.unique()
            unique_count = int(len(unique_vals))
            
            # Constant field detection
            is_constant = False
            constant_value = None
            if unique_count == 1:
                is_constant = True
                val = unique_vals[0]
                # Serialize properly
                if isinstance(val, (datetime, pd.Timestamp)):
                    constant_value = val.isoformat()
                else:
                    constant_value = str(val)
            elif unique_count == 0:
                # Column is entirely null
                is_constant = True
                constant_value = None

            # Sample values (up to 5 representative samples)
            sample_list = []
            for item in unique_vals[:5]:
                if isinstance(item, (datetime, pd.Timestamp)):
                    sample_list.append(item.isoformat())
                elif isinstance(item, (np.integer, int)):
                    sample_list.append(int(item))
                elif isinstance(item, (np.floating, float)):
                    sample_list.append(float(item))
                elif isinstance(item, (np.bool_, bool)):
                    sample_list.append(bool(item))
                else:
                    sample_list.append(str(item))

            columns_meta.append({
                "column_index": idx,
                "original_name": clean_name,
                "sanitized_name": sanitized,
                "detected_data_type": detected_type,
                "is_nullable": is_nullable,
                "null_count": null_count,
                "unique_count": unique_count,
                "is_constant": is_constant,
                "constant_value": constant_value,
                "sample_values": sample_list
            })

        return columns_meta
