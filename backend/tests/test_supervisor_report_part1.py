import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch

from app.models.safety_report import SafetyReport
from app.models.dataset import Dataset
from app.services.report_service import ReportService
from app.schemas.report import SafetyReportCreate, SafetyReportUpdate


def test_01_create_valid_supervisor_report(db_session: Session, client: TestClient):
    """
    Test valid supervisor report submission:
    1. Validates post payload
    2. Generates formatted Report ID (OIL-YYYY-XXXXXX)
    3. Preserves original text exactly
    4. Sets analysis status COMPLETED
    5. Returns 201 Created
    """
    payload = {
        "description": "During flange bolt tightening on CDU-1 heat exchanger V-101, worker operated without face shield. High pressure thermal fluid was isolated.",
        "report_type": "Unsafe Act",
        "refinery_unit": "Crude Distillation Unit (CDU-1)",
        "equipment": "V-101",
        "work_type": "Flange Bolting",
        "department": "Maintenance",
        "ppe_issue": True,
        "supervisor_factor": False,
        "maintenance_factor": True,
        "immediate_cause": "Missing mandatory secondary face shield",
        "potential_consequence": "Severe thermal burn or eye injury",
        "submitting_user": "Supervisor (John Doe)",
        "submitting_role": "Supervisor"
    }

    response = client.post("/api/reports", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()

    assert data["id"] is not None
    assert data["original_id"].startswith("OIL-")
    assert data["description"] == payload["description"]
    assert data["refinery_unit"] == "Crude Distillation Unit (CDU-1)"
    assert data["equipment"] == "V-101"
    assert data["submitting_user"] == "Supervisor (John Doe)"
    assert data["submitting_role"] == "Supervisor"
    assert data["analysis_status"] in ["COMPLETED", "IN_PROGRESS"]
    assert data["raw_data"]["Observation"] == payload["description"]

    # Verify persisted in database
    db_report = db_session.query(SafetyReport).filter(SafetyReport.id == data["id"]).first()
    assert db_report is not None
    assert db_report.description == payload["description"]


def test_02_invalid_meaningless_description_rejection(client: TestClient):
    """
    Test rejection of meaningless or empty observation descriptions (e.g. 'unsafe', 'problem', 'issue').
    """
    invalid_inputs = [
        "unsafe",
        "problem",
        "issue",
        "bad",
        "danger",
        "  short  "
    ]

    for term in invalid_inputs:
        payload = {
            "description": term,
            "report_type": "Unsafe Act"
        }
        response = client.post("/api/reports", json=payload)
        assert response.status_code == 422, f"Failed for term '{term}': {response.text}"
        data = response.json()
        assert "Please describe what you observed" in str(data)


def test_03_ai_failure_does_not_delete_report(db_session: Session):
    """
    Verify that if the AI analysis engine raises an exception during submission, 
    the original report remains safely saved in the database with analysis_status='FAILED'.
    """
    payload = SafetyReportCreate(
        description="High pressure steam valve packing leakage in Boiler House area B-02.",
        refinery_unit="Boiler House",
        equipment="B-02",
        submitting_user="Supervisor (Test)",
        submitting_role="Supervisor"
    )

    with patch("app.services.sif_service.SIFService.analyze_report", side_effect=RuntimeError("Mock AI NLP Engine Crash")):
        report = ReportService.create_report(db=db_session, report_data=payload)

    assert report is not None
    assert report.id is not None
    assert report.analysis_status == "FAILED"
    assert report.description == "High pressure steam valve packing leakage in Boiler House area B-02."

    # Verify report is safely in database
    fetched = db_session.query(SafetyReport).filter(SafetyReport.id == report.id).first()
    assert fetched is not None
    assert fetched.analysis_status == "FAILED"


def test_04_retry_analysis_endpoint(db_session: Session, client: TestClient):
    """
    Test retrying analysis for a report with failed analysis status.
    """
    # Create a report with FAILED status
    report = SafetyReport(
        dataset_id=db_session.query(Dataset).first().id if db_session.query(Dataset).first() else "dummy",
        original_id="OIL-2026-TESTRETRY",
        raw_data={"Observation": "Gas detector alarm triggered near compressor C-102. Seal gas pressure low."},
        description="Gas detector alarm triggered near compressor C-102. Seal gas pressure low.",
        refinery_unit="Hydrocracker Unit",
        equipment="C-102",
        analysis_status="FAILED",
        submitting_user="Supervisor",
        submitting_role="Supervisor",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)

    # Retry analysis via POST /api/reports/{id}/analyze
    response = client.post(f"/api/reports/{report.id}/analyze")
    assert response.status_code == 200, response.text

    # Re-fetch report from DB
    db_session.refresh(report)
    assert report.analysis_status == "COMPLETED"


def test_05_submitted_report_appears_in_reports_list_and_count(db_session: Session, client: TestClient):
    """
    Verify newly submitted report dynamically appears in GET /api/reports and count updates.
    """
    initial_count = client.get("/api/reports/count").json()["total_reports"]

    payload = {
        "description": "Scaffolding structure in CDU-2 lacked toe boards and double handrails during overhead pipe inspection.",
        "refinery_unit": "CDU-2",
        "department": "Civil",
        "submitting_user": "Supervisor (Site)",
        "submitting_role": "Supervisor"
    }

    create_res = client.post("/api/reports", json=payload)
    assert create_res.status_code == 201
    new_report_id = create_res.json()["id"]

    # Verify in list
    list_res = client.get("/api/reports?search=Scaffolding")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(r["id"] == new_report_id for r in list_data["items"])

    # Verify count incremented
    new_count = client.get("/api/reports/count").json()["total_reports"]
    assert new_count == initial_count + 1
