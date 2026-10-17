"""Integration test for Export SSE Stream and Status endpoints."""
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from core.storage.job_store import global_job_store


@pytest.fixture
def client():
    return TestClient(app)


def test_export_stream_sse_flow(client):
    job_id = "test-export-sse-01"
    global_job_store.save_export_job(
        job_id,
        {
            "job_id": job_id,
            "project_id": "test_proj",
            "title": "SSE Test Video",
            "status": "completed",
            "stage": "Rendering completed",
            "progress_percent": 100.0,
            "video_url": "/output/test.mp4",
        },
    )

    # 1. Test status endpoint
    status_resp = client.get(f"/export/status/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["job_id"] == job_id
    assert status_data["status"] == "completed"
    assert status_data["progress_percent"] == 100.0

    # 2. Test SSE stream endpoint
    stream_resp = client.get(f"/export/stream/{job_id}")
    assert stream_resp.status_code == 200
    assert "text/event-stream" in stream_resp.headers["content-type"]
    assert "data: " in stream_resp.text
    assert '"status": "completed"' in stream_resp.text
    assert '"progress_percent": 100.0' in stream_resp.text

    # Cleanup
    global_job_store.delete_export_job(job_id)
