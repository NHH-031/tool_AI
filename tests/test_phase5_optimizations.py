"""
Tests for Phase 5: Parallel Multi-Scene Rendering, Quick Single-Scene Preview, and Auto-Translator
"""

import json
from pathlib import Path
import pytest
import numpy as np
import cv2
from PIL import Image
from fastapi.testclient import TestClient

from apps.api.main import app
from core.artwork.translator import (
    auto_translate_vi_to_en,
    create_whiteboard_art_prompt,
    _TRANSLATION_CACHE,
)
from apps.api.routers.export import PreviewSceneRequest, PreviewSceneResponse

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_auto_translator_vi_to_en():
    """Kiểm tra module auto_translate dịch tiếng Việt sang tiếng Anh tự động."""
    sample_text = "Pin năng lượng mặt trời hấp thụ ánh sáng."
    translated = auto_translate_vi_to_en(sample_text)
    assert translated is not None and isinstance(translated, str)
    assert len(translated.strip()) > 0
    # Kiểm tra đã lưu vào cache
    assert sample_text in _TRANSLATION_CACHE

    # Kiểm tra lời nhắc tranh vẽ chuẩn SKILL.md
    prompt_16_9 = create_whiteboard_art_prompt(sample_text, scene_index=1, aspect_ratio="16:9")
    assert "#F5EBD7" in prompt_16_9
    assert "16:9 widescreen" in prompt_16_9
    assert "no 3D render" in prompt_16_9
    assert translated in prompt_16_9

    prompt_9_16 = create_whiteboard_art_prompt(sample_text, scene_index=2, aspect_ratio="9:16")
    assert "9:16 vertical" in prompt_9_16
    assert "#F5EBD7" in prompt_9_16


def test_scripts_analyze_with_auto_translation(monkeypatch):
    """Kiểm tra API /scripts/analyze tự động phân tách và dịch sang prompt tiếng Anh chuẩn khi không có Gemini key."""
    monkeypatch.setattr("core.artwork.gemini_director.GeminiScriptDirector.is_available", lambda: False)
    client = TestClient(app)
    payload = {
        "text": "Con robot thông minh dạo bước trong thành phố tương lai. Nó quan sát bầu trời đầy sao và mỉm cười.",
        "input_mode": "TEXT",
        "has_color": True,
        "aspect_ratio": "9:16",
    }
    resp = client.post("/scripts/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert "scenes" in data
    assert len(data["scenes"]) >= 1
    first_scene = data["scenes"][0]
    assert first_scene["scene_index"] == 1
    assert "prompt" in first_scene and len(first_scene["prompt"]) > 20
    # Prompt phải chứa quy chuẩn mỹ học bảng trắng và tỷ lệ 9:16
    assert "#F5EBD7" in first_scene["prompt"]
    assert "9:16" in first_scene["prompt"]


def test_preview_scene_endpoint(tmp_path: Path):
    """Kiểm tra endpoint POST /export/preview-scene dựng video hoạt họa 3 giây cực nhanh."""
    client = TestClient(app)

    # 1. Tạo một ảnh giả lập đơn giản cho phân cảnh
    img_dir = PROJECT_ROOT / "output" / "storyboard" / "test_preview_proj"
    img_dir.mkdir(parents=True, exist_ok=True)
    test_img_path = img_dir / "scene_1.png"

    canvas_w, canvas_h = 640, 360
    img_bgr = np.full((canvas_h, canvas_w, 3), (215, 235, 245), dtype=np.uint8)
    cv2.circle(img_bgr, (320, 180), 60, (30, 30, 30), 3)
    cv2.imwrite(str(test_img_path), img_bgr)

    # 2. Gửi request xem trước phân cảnh
    payload = {
        "project_id": "test_preview_proj",
        "scene_index": 1,
        "text": "Khảo sát và thử nghiệm xem trước nét vẽ phân cảnh",
        "image_url": f"/media/storyboard/test_preview_proj/scene_1.png",
        "aspect_ratio": "16:9",
        "hand_tool_id": "hand-pen-modern",
        "has_color": True,
    }

    resp = client.post("/export/preview-scene", json=payload)
    assert resp.status_code == 200
    res_data = resp.json()

    assert res_data["status"] == "completed"
    assert res_data["duration_sec"] == 3.0
    assert res_data["scene_index"] == 1
    assert "preview_url" in res_data
    assert res_data["preview_url"].startswith("/media/previews/")
    assert res_data["preview_url"].endswith(".mp4")

    # Kiểm tra file video thực tế trên đĩa
    file_rel = res_data["preview_url"][len("/media/"):]
    real_video_path = PROJECT_ROOT / "output" / file_rel
    assert real_video_path.exists(), f"File video preview không tồn tại tại {real_video_path}"
    assert real_video_path.stat().st_size > 500


def test_preview_scene_vertical_9_16():
    """Kiểm tra preview phân cảnh dạng dọc 9:16 (TikTok/Shorts)."""
    client = TestClient(app)

    # Tạo ảnh giả lập dọc 360x640
    img_dir = PROJECT_ROOT / "output" / "storyboard" / "test_preview_proj_vert"
    img_dir.mkdir(parents=True, exist_ok=True)
    test_img_path = img_dir / "scene_vert_1.png"

    canvas_w, canvas_h = 360, 640
    img_bgr = np.full((canvas_h, canvas_w, 3), (215, 235, 245), dtype=np.uint8)
    cv2.rectangle(img_bgr, (50, 100), (310, 540), (20, 20, 20), 3)
    cv2.imwrite(str(test_img_path), img_bgr)

    payload = {
        "project_id": "test_preview_proj_vert",
        "scene_index": 1,
        "text": "Xem trước video dọc TikTok",
        "image_url": "/media/storyboard/test_preview_proj_vert/scene_vert_1.png",
        "aspect_ratio": "9:16",
        "hand_tool_id": "no_hand",
    }
    resp = client.post("/export/preview-scene", json=payload)
    assert resp.status_code == 200
    res_data = resp.json()

    assert res_data["status"] == "completed"
    assert res_data["resolution"] == "360x640@15fps"
    assert res_data["preview_url"].endswith(".mp4")
