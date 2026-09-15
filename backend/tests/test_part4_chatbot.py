import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.safety_report import SafetyReport
from app.services.sif_service import SIFService


@pytest.fixture(autouse=True)
def populate_dataset(client: TestClient, ppe_excel_path: str):
    with open(ppe_excel_path, "rb") as f:
        file_bytes = f.read()

    res = client.post(
        "/api/datasets/upload",
        files={"file": (os.path.basename(ppe_excel_path), file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"dataset_name": "PPE Chat Test", "description": "For Part 4 chat test"}
    )
    assert res.status_code == 201


def test_chatbot_database_grounded_queries(client: TestClient, db_session: Session):
    # 1. Total reports
    total_db = db_session.scalar(select(func.count(SafetyReport.id))) or 0
    assert total_db > 0
    res = client.post("/api/chat", json={"message": "How many reports are there?"})
    assert res.status_code == 200
    data = res.json()
    assert str(total_db) in data["reply"]
    assert "Database Record Telemetry" in data["reply"]

    # 2. High-risk reports count
    high_db = db_session.scalar(select(func.count(SafetyReport.id)).where(func.lower(SafetyReport.risk_level) == "high")) or 0
    res = client.post("/api/chat", json={"message": "How many high-risk reports?"})
    assert res.status_code == 200
    data = res.json()
    assert str(high_db) in data["reply"]
    assert "High-Risk Observations Telemetry" in data["reply"]

    # 3. PPE Problems query
    res = client.post("/api/chat", json={"message": "What are the most common PPE problems?"})
    assert res.status_code == 200
    data = res.json()
    assert "Most Common PPE Problems" in data["reply"]
    assert len(data["suggested_actions"]) > 0

    # 4. Top refinery unit query
    res = client.post("/api/chat", json={"message": "Which refinery unit has the most reports?"})
    assert res.status_code == 200
    data = res.json()
    assert "Refinery Unit Analysis" in data["reply"]

    # 5. Top department query
    res = client.post("/api/chat", json={"message": "Which department has the most observations?"})
    assert res.status_code == 200
    data = res.json()
    assert "Department Observation Telemetry" in data["reply"]

    # 6. Common immediate causes query
    res = client.post("/api/chat", json={"message": "What are the most common immediate causes?"})
    assert res.status_code == 200
    data = res.json()
    assert "Most Common Immediate Causes" in data["reply"]

    # 7. Common consequences query
    res = client.post("/api/chat", json={"message": "What consequences are most common?"})
    assert res.status_code == 200
    data = res.json()
    assert "Most Common Potential Consequences" in data["reply"]

    # 8. Open reports query
    res = client.post("/api/chat", json={"message": "Which reports are open?"})
    assert res.status_code == 200
    data = res.json()
    assert "Open Safety Actions Telemetry" in data["reply"]

    # 9. Recurring reports query
    res = client.post("/api/chat", json={"message": "Which reports are recurring?"})
    assert res.status_code == 200
    data = res.json()
    assert "Recurring Issues" in data["reply"]

    # 10. High-risk PPE reports
    res = client.post("/api/chat", json={"message": "Show high-risk PPE reports."})
    assert res.status_code == 200
    data = res.json()
    assert "High-Risk PPE Safety Observations" in data["reply"]

    # 11. Safety summary
    res = client.post("/api/chat", json={"message": "Summarize the current safety situation."})
    assert res.status_code == 200
    data = res.json()
    assert "Executive Safety Intelligence Summary" in data["reply"]
    assert "Strategic HSE Focus" in data["reply"]


def test_chatbot_natural_language_filtering(client: TestClient, db_session: Session):
    # 1. "Show high-risk reports from the Hydrogen Unit."
    res = client.post("/api/chat", json={"message": "Show high-risk reports from the Hydrogen Unit."})
    assert res.status_code == 200
    data = res.json()
    assert "Hydrogen Unit" in data["reply"] or "high-risk" in data["reply"].lower()

    # 2. "Show PPE observations from Maintenance."
    res = client.post("/api/chat", json={"message": "Show PPE observations from Maintenance."})
    assert res.status_code == 200
    data = res.json()
    assert "Maintenance" in data["reply"]

    # 3. "Show reports where previous similar reports are greater than 2."
    res = client.post("/api/chat", json={"message": "Show reports where previous similar reports are greater than 2."})
    assert res.status_code == 200
    data = res.json()
    assert "previous_similar_reports > 2" in data["reply"]


def test_chatbot_report_specific_qa(client: TestClient, db_session: Session):
    report = db_session.scalar(select(SafetyReport).limit(1))
    assert report is not None

    # Ensure report has AI analysis
    analysis = SIFService.analyze_report(db_session, report.id)

    # 1. "Why is this report important?"
    res = client.post("/api/chat", json={"message": "Why is this report important?", "report_id": report.id})
    assert res.status_code == 200
    data = res.json()
    assert "Report Importance Assessment" in data["reply"]
    assert (report.original_id or report.id) in data["reply"]

    # 2. "What is the potential safety consequence?"
    res = client.post("/api/chat", json={"message": "What is the potential safety consequence?", "report_id": report.id})
    assert res.status_code == 200
    data = res.json()
    assert "Potential Safety Consequence Analysis" in data["reply"]

    # 3. "What immediate action is recommended?"
    res = client.post("/api/chat", json={"message": "What immediate action is recommended?", "report_id": report.id})
    assert res.status_code == 200
    data = res.json()
    assert "Recommended Actions for Report" in data["reply"]

    # 4. "Is this issue recurring?"
    res = client.post("/api/chat", json={"message": "Is this issue recurring?", "report_id": report.id})
    assert res.status_code == 200
    data = res.json()
    assert "Recurrence Telemetry" in data["reply"]

    # 5. "What could happen if this remains unresolved?"
    res = client.post("/api/chat", json={"message": "What could happen if this remains unresolved?", "report_id": report.id})
    assert res.status_code == 200
    data = res.json()
    assert "Unresolved Escalation Progression" in data["reply"]
