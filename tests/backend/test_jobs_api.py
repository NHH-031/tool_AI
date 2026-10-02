from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_create_and_get_job():
    # Tạo job
    res = client.post("/jobs", json={"title": "Video Giới Thiệu AI", "prompt": "Video hoạt hình ngắn"})
    assert res.status_code == 201
    job = res.json()
    job_id = job["id"]
    assert job["title"] == "Video Giới Thiệu AI"
    assert job["status"] == "pending"
    assert len(job["stages"]) == 8

    # Lấy chi tiết job
    res_get = client.get(f"/jobs/{job_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == job_id

    # Danh sách jobs
    res_list = client.get("/jobs")
    assert res_list.status_code == 200
    assert any(j["id"] == job_id for j in res_list.json())


def test_get_nonexistent_job():
    res = client.get("/jobs/nonexistent-id-12345")
    assert res.status_code == 404
