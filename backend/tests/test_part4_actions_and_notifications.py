import os
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.safety_report import SafetyReport
from app.models.action_history import ActionHistory
from app.models.email_log import EmailLog


@pytest.fixture(autouse=True)
def populate_dataset(client: TestClient, ppe_excel_path: str):
    with open(ppe_excel_path, "rb") as f:
        file_bytes = f.read()

    res = client.post(
        "/api/datasets/upload",
        files={"file": (os.path.basename(ppe_excel_path), file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"dataset_name": "PPE Actions Test", "description": "For Part 4 actions test"}
    )
    assert res.status_code == 201


def test_action_center_apis(client: TestClient, db_session: Session):
    # 1. Get Actions list
    res = client.get("/api/actions")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data

    # 2. Get Action Stats
    res = client.get("/api/actions/stats")
    assert res.status_code == 200
    stats = res.json()
    assert "total_actions" in stats
    assert "open_count" in stats
    assert "in_progress_count" in stats
    assert "closed_count" in stats
    assert "overdue_count" in stats

    # 3. Update / Assign Action
    report = db_session.scalar(select(SafetyReport).limit(1))
    assert report is not None

    due_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    update_payload = {
        "action_status": "In Progress",
        "assigned_to": "John Field Supervisor",
        "assigned_department": "Maintenance",
        "due_date": due_date,
        "action_comments": "Assigned crew to repair valve gasket and install guard.",
        "actor_name": "Senior HSE Inspector",
        "actor_role": "Safety Officer"
    }
    res = client.patch(f"/api/actions/{report.id}", json=update_payload)
    assert res.status_code == 200
    updated = res.json()
    assert updated["action_status"] == "In Progress"
    assert updated["assigned_to"] == "John Field Supervisor"
    assert updated["assigned_department"] == "Maintenance"

    # 4. Check Action History Audit Log
    res = client.get(f"/api/actions/{report.id}/history")
    assert res.status_code == 200
    hist = res.json()
    assert len(hist) > 0
    assert hist[0]["actor_name"] == "Senior HSE Inspector"
    assert hist[0]["new_status"] == "In Progress"

    # 5. Mark Completed & Verify Closure
    close_payload = {
        "action_status": "Closed",
        "closure_verified_by": "Plant Safety Manager",
        "action_comments": "Field barrier verified. Hazard mitigated.",
        "actor_name": "Plant Safety Manager",
        "actor_role": "Management"
    }
    res = client.patch(f"/api/actions/{report.id}", json=close_payload)
    assert res.status_code == 200
    closed = res.json()
    assert closed["action_status"] == "Closed"
    assert closed["closure_verified_by"] == "Plant Safety Manager"


def test_notification_and_escalation_system(client: TestClient, db_session: Session):
    report = db_session.scalar(select(SafetyReport).limit(1))
    assert report is not None

    # 1. Get Notification Configs
    res = client.get("/api/notifications/config")
    assert res.status_code == 200
    configs = res.json()
    assert len(configs) >= 1

    # 2. Add New Config
    new_cfg = {
        "tier": "MANAGEMENT",
        "role_name": "VP Refining Operations",
        "department": "All",
        "email_address": "vp.operations@refinery.oil.internal",
        "notify_on_high_risk": True,
        "notify_on_overdue": True,
        "notify_on_assignment": False,
        "is_active": True
    }
    res = client.post("/api/notifications/config", json=new_cfg)
    assert res.status_code == 201
    created_cfg = res.json()
    cfg_id = created_cfg["id"]
    assert created_cfg["role_name"] == "VP Refining Operations"

    # 3. Generate Email Preview (Mandatory Review)
    preview_req = {
        "report_id": report.id,
        "notification_type": "HIGH_RISK",
        "target_tier": "MANAGEMENT"
    }
    res = client.post("/api/notifications/preview", json=preview_req)
    assert res.status_code == 200
    preview = res.json()
    assert "recorded_information" in preview
    assert "ai_recommendations" in preview
    assert "rendered_html" in preview
    assert "rendered_plain_text" in preview
    assert "Recorded Field Information" in preview["rendered_html"]
    assert "AI SIF Risk Assessment" in preview["rendered_html"]

    # 4. Dispatch Email and Verify Audit Log
    send_req = {
        "report_id": report.id,
        "notification_type": "HIGH_RISK",
        "recipient_emails": ["vp.operations@refinery.oil.internal"],
        "subject": preview["subject"],
        "body_html": preview["rendered_html"],
        "triggered_by": "Safety Officer",
        "escalation_tier": "MANAGEMENT"
    }
    res = client.post("/api/notifications/send", json=send_req)
    assert res.status_code == 200
    send_data = res.json()
    assert send_data["success"] is True

    # 5. Check Email Logs API
    res = client.get(f"/api/notifications/logs?report_id={report.id}")
    assert res.status_code == 200
    logs = res.json()
    assert logs["total"] >= 1
    assert logs["items"][0]["recipient_email"] == "vp.operations@refinery.oil.internal"

    # 6. Delete Test Config
    res = client.delete(f"/api/notifications/config/{cfg_id}")
    assert res.status_code == 204


def test_audit_logs_api(client: TestClient, db_session: Session):
    res = client.get("/api/audit-logs")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data

    res = client.get("/api/audit-logs/actions")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
