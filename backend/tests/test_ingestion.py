import os
import json
import pandas as pd
from app.services.dataset_service import DatasetService
from app.models.safety_report import SafetyReport
from sqlalchemy import select


def test_ppe_dataset_ingestion_accuracy(db_session, ppe_excel_path):
    with open(ppe_excel_path, "rb") as f:
        file_bytes = f.read()

    filename = os.path.basename(ppe_excel_path)
    dataset = DatasetService.ingest_dataset(
        db=db_session,
        file_bytes=file_bytes,
        filename=filename,
        file_type="xlsx",
        dataset_name="PPE Non-Compliance Verification",
        client_host="test_runner"
    )

    # 1. Verify Dataset metadata
    assert dataset is not None
    assert dataset.row_count == 75
    assert dataset.column_count == 18
    assert dataset.status == "ready"

    # 2. Verify Columns detection
    schema_info = DatasetService.get_dataset_schema(db_session, dataset.id)
    assert len(schema_info["columns"]) == 18

    # 3. Verify Constant fields detection (exactly 5 in PPE dataset)
    constant_col_names = {c.original_name for c in schema_info["constant_fields"]}
    expected_constants = {
        "PPE_NonCompliance",
        "Supervisor_Negligence",
        "Maintenance_Delay_or_Issue",
        "Repeated_Issue_Ignored",
        "High_Potential_Near_Miss"
    }
    assert expected_constants.issubset(constant_col_names)

    # 4. Verify Reports count and integrity
    reports = list(db_session.scalars(select(SafetyReport).where(SafetyReport.dataset_id == dataset.id)).all())
    assert len(reports) == 75

    # 5. Check sample report preservation
    sample = reports[0]
    assert sample.raw_data is not None
    assert len(sample.raw_data.keys()) == 18
    assert "Near_Miss_ID" in sample.raw_data
    assert "PPE_NonCompliance" in sample.raw_data
    assert sample.original_id.startswith("01_P-")
    assert sample.refinery_unit is not None
    assert sample.department is not None
    assert sample.risk_level in ["Low", "Medium", "High", "LOW", "MEDIUM", "HIGH"]


def test_csv_and_json_ingestion(db_session):
    # Test CSV Ingestion
    csv_data = """Record_ID,Incident_Date,Plant_Area,Hazard_Description,Risk_Rating
R-101,2025-05-10,Hydrocracker,Worker observed without eye protection,Medium
R-102,2025-05-11,Crude Distillation,Slippery oil spill near pump,High
"""
    csv_bytes = csv_data.encode("utf-8")
    ds_csv = DatasetService.ingest_dataset(
        db=db_session,
        file_bytes=csv_bytes,
        filename="custom_near_miss.csv",
        file_type="csv",
        dataset_name="CSV Test Dataset"
    )
    assert ds_csv.row_count == 2
    assert ds_csv.column_count == 5

    # Test JSON Ingestion
    json_data = [
        {"id": "J-1", "date": "2025-06-01", "unit": "Sulfur", "details": "Valve leak detected", "severity": "Low"},
        {"id": "J-2", "date": "2025-06-02", "unit": "Alkylation", "details": "Corroded piping", "severity": "High"}
    ]
    json_bytes = json.dumps(json_data).encode("utf-8")
    ds_json = DatasetService.ingest_dataset(
        db=db_session,
        file_bytes=json_bytes,
        filename="custom_reports.json",
        file_type="json",
        dataset_name="JSON Test Dataset"
    )
    assert ds_json.row_count == 2
    assert ds_json.column_count == 5
