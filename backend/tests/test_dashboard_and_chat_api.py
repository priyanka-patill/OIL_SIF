import pytest
import os

def test_dashboard_serving(client):
    # Test Root serves HTML dashboard
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "OIL SIF Intelligence Platform" in response.text
    assert "ReactDOM.createRoot" in response.text

    # Test /dashboard serves HTML dashboard
    dash_response = client.get("/dashboard")
    assert dash_response.status_code == 200
    assert "text/html" in dash_response.headers["content-type"]
    assert "OIL SIF Intelligence Platform" in dash_response.text

def test_chat_api_endpoint(client, ppe_excel_path):
    # Ingest dataset
    with open(ppe_excel_path, "rb") as f:
        file_bytes = f.read()

    client.post(
        "/api/datasets/upload",
        files={"file": (os.path.basename(ppe_excel_path), file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"dataset_name": "PPE Chat Test", "description": "For chat test"}
    )

    # Test Chat query on SIF rate
    res = client.post("/api/chat", json={"message": "What is the SIF precursor rate?"})
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert "suggested_actions" in data
    assert "SIF" in data["reply"]

    # Test Chat query on Overdue actions
    res2 = client.post("/api/chat", json={"message": "Show overdue corrective actions"})
    assert res2.status_code == 200
    data2 = res2.json()
    assert "overdue" in data2["reply"].lower() or "action" in data2["reply"].lower()

def test_metadata_fields_api(client):
    res = client.get("/api/metadata/fields")
    assert res.status_code == 200
    data = res.json()
    assert "available_filters" in data
    assert "canonical_schema" in data
    assert isinstance(data["available_filters"], list)
    assert len(data["canonical_schema"]) > 0
