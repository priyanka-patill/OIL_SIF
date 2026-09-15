import pandas as pd
from app.ingestion.schema_detector import SchemaDetector
from app.analytics.profiler import DataQualityEngine


def test_data_quality_perfect_dataset():
    df = pd.DataFrame({
        "Near_Miss_ID": ["NM-1", "NM-2", "NM-3"],
        "Date": ["2025-01-01", "2025-01-02", "2025-01-03"],
        "Department": ["HSE", "Operations", "Maintenance"],
        "Risk_Level": ["Low", "Medium", "High"]
    })
    meta = SchemaDetector.analyze_schema(df)
    for m in meta:
        if m["original_name"] == "Near_Miss_ID":
            m["mapped_canonical_field"] = "original_id"
        elif m["original_name"] == "Date":
            m["mapped_canonical_field"] = "report_date"

    quality = DataQualityEngine.calculate_quality_summary(df, "test-ds-1", meta)
    assert quality.total_rows == 3
    assert quality.total_columns == 4
    assert quality.missing_values_count == 0
    assert quality.duplicate_ids_count == 0
    assert quality.invalid_dates_count == 0
    assert quality.data_quality_score == 100.0


def test_data_quality_flawed_dataset():
    df = pd.DataFrame({
        "Near_Miss_ID": ["NM-1", "NM-1", None],  # 1 duplicate, 1 missing
        "Date": ["2025-01-01", "invalid-date-string", None],  # 1 invalid date, 1 missing
        "Constant_Flag": [True, True, True],  # Constant field
        "Empty_Col": [None, None, None]  # 100% missing empty column
    })
    meta = SchemaDetector.analyze_schema(df)
    for m in meta:
        if m["original_name"] == "Near_Miss_ID":
            m["mapped_canonical_field"] = "original_id"
        elif m["original_name"] == "Date":
            m["mapped_canonical_field"] = "report_date"

    quality = DataQualityEngine.calculate_quality_summary(df, "test-ds-2", meta)
    assert quality.total_rows == 3
    assert quality.total_columns == 4
    assert quality.missing_values_count > 0
    assert quality.duplicate_ids_count == 1
    assert quality.invalid_dates_count >= 1
    assert quality.constant_fields_count >= 1
    assert quality.empty_columns_count == 1
    assert quality.data_quality_score < 100.0
