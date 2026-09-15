import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_report_export_preview(client: TestClient, db_session: Session):
    res = client.get("/api/reports/export/preview")
    assert res.status_code == 200
    data = res.json()
    assert "total_matching_reports" in data
    assert "by_risk_level" in data
    assert "available_export_formats" in data
    assert "PDF" in data["available_export_formats"]
    assert "EXCEL" in data["available_export_formats"]
    assert "CSV" in data["available_export_formats"]


def test_pdf_report_export(client: TestClient, db_session: Session):
    res = client.get("/api/reports/export/pdf")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in res.headers.get("content-disposition", "")
    assert res.content.startswith(b"%PDF-")


def test_excel_report_export(client: TestClient, db_session: Session):
    res = client.get("/api/reports/export/excel")
    assert res.status_code == 200
    assert "spreadsheetml" in res.headers["content-type"]
    assert len(res.content) > 1000


def test_csv_report_export(client: TestClient, db_session: Session):
    res = client.get("/api/reports/export/csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    lines = res.text.strip().split("\n")
    assert len(lines) >= 1
    assert "report_id" in lines[0]
    assert "refinery_unit" in lines[0]


def test_filtered_report_export(client: TestClient, db_session: Session):
    # Test filtering by risk level
    res = client.get("/api/reports/export/preview?risk_level=High")
    assert res.status_code == 200
    data = res.json()
    assert data["active_filters_applied"]["risk_level"] == "High"

    # Test PDF with filters
    res_pdf = client.get("/api/reports/export/pdf?risk_level=High")
    assert res_pdf.status_code == 200
    assert res_pdf.content.startswith(b"%PDF-")
