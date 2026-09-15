import uuid
from datetime import datetime
from sqlalchemy import select, text
from app.models.dataset import Dataset
from app.models.dataset_column import DatasetColumn
from app.models.safety_report import SafetyReport
from app.models.audit_log import AuditLog


def test_database_connection(db_session):
    result = db_session.execute(text("SELECT 1")).scalar()
    assert result == 1


def test_dataset_model_creation(db_session):
    ds_id = str(uuid.uuid4())
    dataset = Dataset(
        id=ds_id,
        dataset_name="Test Dataset",
        original_filename="test.xlsx",
        file_type="xlsx",
        file_size_bytes=1024,
        row_count=10,
        column_count=5,
        status="ready"
    )
    db_session.add(dataset)
    db_session.flush()

    fetched = db_session.scalar(select(Dataset).where(Dataset.id == ds_id))
    assert fetched is not None
    assert fetched.dataset_name == "Test Dataset"
    assert fetched.row_count == 10
    assert fetched.column_count == 5


def test_dataset_column_relationship(db_session):
    ds_id = str(uuid.uuid4())
    dataset = Dataset(
        id=ds_id,
        dataset_name="Column Test Dataset",
        original_filename="cols.xlsx",
        file_type="xlsx"
    )
    col = DatasetColumn(
        id=str(uuid.uuid4()),
        dataset_id=ds_id,
        column_index=0,
        original_name="Risk_Level",
        sanitized_name="risk_level",
        detected_data_type="STRING",
        semantic_type="RISK_LEVEL",
        is_constant=False,
        unique_count=3
    )
    db_session.add(dataset)
    db_session.add(col)
    db_session.flush()

    fetched = db_session.scalar(select(Dataset).where(Dataset.id == ds_id))
    assert len(fetched.columns) == 1
    assert fetched.columns[0].original_name == "Risk_Level"
    assert fetched.columns[0].detected_data_type == "STRING"


def test_safety_report_raw_data_preservation(db_session):
    ds_id = str(uuid.uuid4())
    dataset = Dataset(
        id=ds_id,
        dataset_name="Report Test Dataset",
        original_filename="rep.xlsx",
        file_type="xlsx"
    )
    raw_payload = {
        "Custom_Field_1": "Specific Value",
        "Legacy_Code": 9942,
        "Is_Active": True
    }
    report = SafetyReport(
        id=str(uuid.uuid4()),
        dataset_id=ds_id,
        original_id="REP-001",
        raw_data=raw_payload,
        risk_level="High",
        department="Operations"
    )
    db_session.add(dataset)
    db_session.add(report)
    db_session.flush()

    fetched = db_session.scalar(select(SafetyReport).where(SafetyReport.original_id == "REP-001"))
    assert fetched is not None
    assert fetched.raw_data == raw_payload
    assert fetched.raw_data["Custom_Field_1"] == "Specific Value"
    assert fetched.raw_data["Legacy_Code"] == 9942
    assert fetched.risk_level == "High"
