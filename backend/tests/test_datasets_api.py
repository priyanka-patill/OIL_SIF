import io
import os


def test_health_api(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["service"] == "OIL SIF Intelligence Platform"
    assert "database" in data


def test_dataset_upload_and_lifecycle(client, ppe_excel_path):
    with open(ppe_excel_path, "rb") as f:
        file_bytes = f.read()

    # 1. Upload PPE dataset via multipart API
    res_upload = client.post(
        "/api/datasets/upload",
        files={"file": (os.path.basename(ppe_excel_path), file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"dataset_name": "API Uploaded PPE Dataset", "description": "Uploaded via test"}
    )
    assert res_upload.status_code == 201
    dataset = res_upload.json()
    dataset_id = dataset["id"]
    assert dataset["row_count"] == 75
    assert dataset["column_count"] == 18

    # 2. List datasets
    res_list = client.get("/api/datasets")
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert list_data["total"] >= 1
    assert any(d["id"] == dataset_id for d in list_data["items"])

    # 3. Get single dataset details
    res_get = client.get(f"/api/datasets/{dataset_id}")
    assert res_get.status_code == 200
    detail = res_get.json()
    assert detail["id"] == dataset_id
    assert len(detail["columns"]) == 18

    # 4. Get dataset schema
    res_schema = client.get(f"/api/datasets/{dataset_id}/schema")
    assert res_schema.status_code == 200
    schema = res_schema.json()
    assert schema["dataset_id"] == dataset_id
    assert len(schema["columns"]) == 18
    assert len(schema["constant_fields"]) >= 5

    # 5. Get data quality scorecard
    res_quality = client.get(f"/api/data-quality/{dataset_id}")
    assert res_quality.status_code == 200
    quality = res_quality.json()
    assert quality["dataset_id"] == dataset_id
    assert quality["total_rows"] == 75
    assert quality["total_columns"] == 18
    assert quality["data_quality_score"] > 0
    assert len(quality["constant_fields"]) >= 5

    # 6. Dynamic Metadata Fields API
    res_meta = client.get("/api/metadata/fields")
    assert res_meta.status_code == 200
    meta = res_meta.json()
    assert len(meta["available_filters"]) > 0
    assert len(meta["canonical_schema"]) > 0

    # 7. Delete dataset
    res_del = client.delete(f"/api/datasets/{dataset_id}")
    assert res_del.status_code == 200

    # Verify not found after delete
    res_get_after = client.get(f"/api/datasets/{dataset_id}")
    assert res_get_after.status_code == 404
