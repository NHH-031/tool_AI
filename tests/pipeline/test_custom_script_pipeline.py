"""
PHASE 10.2: CUSTOM SCRIPT INPUT PIPELINE TESTS
Kiểm thử toàn diện: Kịch bản người dùng mới phải thực sự đi xuyên suốt pipeline,
tạo ra video và entity chính xác theo kịch bản, loại bỏ hoàn toàn hardcoded monkey regression.
"""
from __future__ import annotations

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from core.pipeline.whiteboard_pipeline import WhiteboardPipeline
from core.qa.media_probe import MediaProbe

client = TestClient(app)
OUTPUT_BASE = Path("output/phase_10_2_tests")


@pytest.fixture(scope="session", autouse=True)
def setup_test_dirs():
    OUTPUT_BASE.mkdir(parents=True, exist_ok=True)


@pytest.mark.asyncio
async def test_custom_script_dog_running_after_ball():
    """
    Test 1: Input 'Con chó đang chạy theo quả bóng.'
    Expected: dog, ball
    KHÔNG được có: monkey, banana, tree
    """
    pipeline = WhiteboardPipeline()
    out_dir = OUTPUT_BASE / "test_dog_ball"
    script = "Con chó đang chạy theo quả bóng."

    res = await pipeline.run(
        script=script,
        input_mode="SCRIPT",
        output_dir=out_dir,
    )

    assert res.is_success is True
    assert Path(res.final_mp4_path).exists()
    assert res.script_text == script

    entities = res.metadata.get("entities", [])
    assert "dog" in entities
    assert "ball" in entities
    assert "monkey" not in entities
    assert "banana" not in entities
    assert "tree" not in entities

    # Verify actual MP4 with MediaProbe
    report = MediaProbe.inspect_media(res.final_mp4_path)
    assert report.is_valid_mp4 is True
    assert report.video_codec == "h264"
    assert report.audio_codec == "aac"
    assert report.frame_count > 0


@pytest.mark.asyncio
async def test_custom_script_earth_orbiting_sun():
    """
    Test 2: Input 'Trái Đất quay quanh Mặt Trời.'
    Expected: earth, sun, orbit
    KHÔNG được có: monkey, banana, tree
    """
    pipeline = WhiteboardPipeline()
    out_dir = OUTPUT_BASE / "test_earth_sun"
    script = "Trái Đất quay quanh Mặt Trời."

    res = await pipeline.run(
        script=script,
        input_mode="SCRIPT",
        output_dir=out_dir,
    )

    assert res.is_success is True
    assert Path(res.final_mp4_path).exists()
    assert res.script_text == script

    entities = res.metadata.get("entities", [])
    assert "earth" in entities
    assert "sun" in entities
    assert "orbit" in entities
    assert "monkey" not in entities
    assert "banana" not in entities
    assert "tree" not in entities


@pytest.mark.asyncio
async def test_custom_script_farmer_planting_tree():
    """
    Test 3: Input 'Người nông dân đang trồng một cái cây.'
    Expected: farmer, tree, ground
    KHÔNG được có: monkey, banana
    """
    pipeline = WhiteboardPipeline()
    out_dir = OUTPUT_BASE / "test_farmer_tree"
    script = "Người nông dân đang trồng một cái cây."

    res = await pipeline.run(
        script=script,
        input_mode="SCRIPT",
        output_dir=out_dir,
    )

    assert res.is_success is True
    assert Path(res.final_mp4_path).exists()
    assert res.script_text == script

    entities = res.metadata.get("entities", [])
    assert "farmer" in entities
    assert "tree" in entities
    assert "ground" in entities
    assert "monkey" not in entities
    assert "banana" not in entities


@pytest.mark.asyncio
async def test_job_isolation_dog_and_earth():
    """
    Test 4: Job Isolation
    Tạo hai jobs song song: Job A (Dog/Ball) và Job B (Earth/Sun).
    Verify Job A chỉ có dog/ball, Job B chỉ có earth/sun.
    Không bị rò rỉ dữ liệu hoặc dùng chung state.
    """
    pipeline = WhiteboardPipeline()

    res_a = await pipeline.run(
        script="Con chó đang chạy theo quả bóng.",
        input_mode="SCRIPT",
        output_dir=OUTPUT_BASE / "job_a",
        job_id="job-isolation-a",
    )

    res_b = await pipeline.run(
        script="Trái Đất quay quanh Mặt Trời.",
        input_mode="SCRIPT",
        output_dir=OUTPUT_BASE / "job_b",
        job_id="job-isolation-b",
    )

    ents_a = res_a.metadata.get("entities", [])
    ents_b = res_b.metadata.get("entities", [])

    assert "dog" in ents_a and "ball" in ents_a
    assert "earth" not in ents_a and "sun" not in ents_a

    assert "earth" in ents_b and "sun" in ents_b
    assert "dog" not in ents_b and "ball" not in ents_b

    assert res_a.metadata.get("script_hash") != res_b.metadata.get("script_hash")
    assert res_a.final_mp4_path != res_b.final_mp4_path


@pytest.mark.asyncio
async def test_regression_monkey_fixture_still_works():
    """
    Test 5: Explicit Regression Test
    Kịch bản monkey-banana-demo vẫn phải hoạt động chính xác khi được gọi tường minh.
    """
    pipeline = WhiteboardPipeline()
    out_dir = OUTPUT_BASE / "test_monkey_regression"
    script = "Con khỉ đang trèo lên cây để lấy một quả chuối."

    res = await pipeline.run(
        script=script,
        input_mode="SCRIPT",
        output_dir=out_dir,
    )

    assert res.is_success is True
    entities = res.metadata.get("entities", [])
    assert "monkey" in entities
    assert "tree" in entities
    assert "banana" in entities


def test_api_empty_script_rejected_400():
    """
    Test 6: Empty script rejection
    Backend phải trả về HTTP 400 Bad Request, không được tự ý fallback về monkey demo.
    """
    res = client.post("/jobs", json={"title": "Empty Script Video", "prompt": "   ", "script": ""})
    assert res.status_code == 400
    assert "Script is required" in res.json().get("detail", "")


def test_api_create_job_and_review_with_custom_script():
    """
    Test 7: Full API integration test
    Gửi request tạo video với kịch bản chó đuổi bóng,
    xác thực Review API trả về đúng entities dog, ball, không có monkey.
    """
    script = "Con chó đang chạy theo quả bóng."
    create_res = client.post(
        "/jobs",
        json={
            "title": "Chó Đuổi Bóng",
            "prompt": script,
            "script": script,
            "input_mode": "SCRIPT",
            "auto_run": True,
        },
    )
    assert create_res.status_code == 201
    job_data = create_res.json()
    job_id = job_data["id"]

    assert job_data["script"] == script
    assert job_data["status"] == "completed"

    # Lấy thông tin Review
    rev_res = client.get(f"/jobs/{job_id}/review")
    assert rev_res.status_code == 200
    rev_data = rev_res.json()["review_data"]

    assert rev_data["script"]["full_text"] == script
    entity_names = [e["name"] for e in rev_data["visual_entities"]]
    assert "dog" in entity_names
    assert "ball" in entity_names
    assert "monkey" not in entity_names
    assert "banana" not in entity_names
