from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_templates_catalog():
    res = client.get("/templates")
    assert res.status_code == 200
    templates = res.json()
    assert len(templates) >= 4
    assert any(t["id"] == "notion_minimal" for t in templates)


def test_assets_catalog():
    res = client.get("/assets")
    assert res.status_code == 200
    assets = res.json()
    assert len(assets) >= 3
    assert any(a["name"] == "monkey" for a in assets)
    assert any(a["name"] == "tree" for a in assets)
    assert any(a["name"] == "banana" for a in assets)


def test_voices_catalog():
    res = client.get("/voices")
    assert res.status_code == 200
    voices = res.json()
    assert len(voices) >= 4
    assert any("vi-VN" in v["locale"] for v in voices)


def test_music_catalog():
    res = client.get("/music")
    assert res.status_code == 200
    tracks = res.json()
    assert len(tracks) >= 4
    assert any(m["id"] == "whimsical_play" for m in tracks)


def test_projects_crud():
    # List projects
    res = client.get("/projects")
    assert res.status_code == 200
    projects = res.json()
    assert len(projects) >= 1

    # Create new project
    res_create = client.post(
        "/projects",
        json={"title": "Video Bài Giảng Toán Học", "description": "Giải thích định lý Pythagoras"},
    )
    assert res_create.status_code == 201
    created = res_create.json()
    assert created["title"] == "Video Bài Giảng Toán Học"


def test_job_review_and_regenerate():
    # Review demo job
    res = client.get("/jobs/job-monkey-banana-demo/review")
    assert res.status_code == 200
    data = res.json()
    assert data["job_id"] == "job-monkey-banana-demo"
    assert "review_data" in data
    assert "visual_entities" in data["review_data"]
    assert "script" in data["review_data"]

    # Regenerate script
    res_regen = client.post(
        "/jobs/job-monkey-banana-demo/regenerate",
        json={"target": "script", "instructions": "Viết ngắn gọn hơn"},
    )
    assert res_regen.status_code == 200
    job = res_regen.json()
    assert job["status"] == "completed"
