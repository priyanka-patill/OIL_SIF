import os
from app.services.dataset_service import DatasetService


def test_reports_api_flow(client, db_session, ppe_excel_path):
    # Ingest PPE dataset first
    with open(ppe_excel_path, "rb") as f:
        file_bytes = f.read()

    dataset = DatasetService.ingest_dataset(
        db=db_session,
        file_bytes=file_bytes,
        filename=os.path.basename(ppe_excel_path),
        file_type="xlsx",
        dataset_name="Reports API Test Dataset"
    )

    # 1. Get all reports paginated
    res = client.get("/api/reports?page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 75
    assert len(data["items"]) == 10
    assert data["total_pages"] == 8

    # 2. Filter by Risk Level
    res_high = client.get("/api/reports?risk_level=High")
    assert res_high.status_code == 200
    high_data = res_high.json()
    for item in high_data["items"]:
        assert item["risk_level"].lower() == "high"

    # 3. Filter by Action Status
    res_open = client.get("/api/reports?action_status=Open")
    assert res_open.status_code == 200
    open_data = res_open.json()
    for item in open_data["items"]:
        assert item["action_status"].lower() == "open"

    # 4. Search by keyword
    res_search = client.get("/api/reports?search=helmet")
    assert res_search.status_code == 200
    search_data = res_search.json()
    assert search_data["total"] > 0
    for item in search_data["items"]:
        assert "helmet" in item["description"].lower() or "helmet" in str(item).lower()

    # 5. Get report counts breakdown
    res_counts = client.get("/api/reports/count")
    assert res_counts.status_code == 200
    counts = res_counts.json()
    assert counts["total_reports"] == 75
    assert "Low" in counts["by_risk_level"] or "Medium" in counts["by_risk_level"] or "High" in counts["by_risk_level"]
    assert len(counts["by_department"]) > 0

    # 6. Get single report detail (verifying raw_data exists)
    first_id = data["items"][0]["id"]
    res_detail = client.get(f"/api/reports/{first_id}")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert detail["id"] == first_id
    assert "raw_data" in detail
    assert "PPE_NonCompliance" in detail["raw_data"]
    assert detail["raw_data"]["PPE_NonCompliance"] is True
