"""
Tests for Phase 4: Semantic Multi-Region Reveal & Custom Drawing Tools (Multi-Brush)
"""

import json
from pathlib import Path
import pytest
import numpy as np
import cv2
from PIL import Image
from fastapi.testclient import TestClient

from core.annotation.auto_segment import (
    auto_segment_image,
    _detect_ink_contours,
    RegionBox,
    RevealPlan,
    HandPath,
)
from apps.api.main import app
from apps.api.routers.export import RenderExportRequest, ExportSceneItem, _create_scene_annotation
from engines.whiteboard.adapter import WhiteboardRenderConfig


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_drawing_tools_png_assets_exist():
    """Kiểm tra 4 file bàn tay / bút vẽ RGBA được tạo và tồn tại trong thư mục assets/drawing-tools/."""
    tools_dir = PROJECT_ROOT / "assets" / "drawing-tools"
    assert tools_dir.exists() and tools_dir.is_dir()

    expected_assets = [
        "hand-pen-modern.png",
        "hand-marker.png",
        "hand-quill-vintage.png",
        "hand-calligraphy.png",
    ]

    for asset_name in expected_assets:
        asset_file = tools_dir / asset_name
        assert asset_file.exists(), f"Thiếu asset: {asset_name}"
        # Đọc bằng PIL kiểm tra định dạng RGBA và kích thước
        with Image.open(asset_file) as img:
            assert img.mode == "RGBA", f"Asset {asset_name} phải là ảnh RGBA có kênh alpha"
            assert img.width >= 300 and img.height >= 300


def test_drawing_tools_api_endpoint():
    """Kiểm tra API GET /assets/drawing-tools trả về danh sách 5 công cụ bút vẽ và bàn tay."""
    client = TestClient(app)
    resp = client.get("/assets/drawing-tools")
    assert resp.status_code == 200
    tools = resp.json()

    assert len(tools) == 5
    tool_ids = [t["id"] for t in tools]
    assert "hand-pen-modern" in tool_ids
    assert "hand-marker" in tool_ids
    assert "hand-quill-vintage" in tool_ids
    assert "hand-calligraphy" in tool_ids
    assert "no_hand" in tool_ids

    # Kiểm tra default tool là hand-pen-modern
    default_tool = next(t for t in tools if t["id"] == "hand-pen-modern")
    assert default_tool["is_default"] is True
    assert default_tool["preview_url"] == "/assets/drawing-tools/hand-pen-modern.png"

    # Kiểm tra no_hand
    no_hand = next(t for t in tools if t["id"] == "no_hand")
    assert no_hand["is_default"] is False


def test_auto_segment_multi_regions_synthetic(tmp_path: Path):
    """
    Kiểm tra thuật toán auto_segment_image phân tách ảnh thành 3 vùng ngữ nghĩa
    (background_setup -> main_character -> fine_details).
    """
    canvas_w, canvas_h = 1280, 720
    # Nền kem giấy whiteboard cổ điển (RGB: 245, 235, 215 -> BGR: 215, 235, 245)
    img_bgr = np.full((canvas_h, canvas_w, 3), (215, 235, 245), dtype=np.uint8)

    # 1. Vẽ khung cảnh nền (hộp lớn góc trái trên)
    cv2.rectangle(img_bgr, (80, 80), (450, 400), (30, 30, 30), 4)

    # 2. Vẽ nhân vật chính (hình tròn lớn dày ở trung tâm)
    cv2.circle(img_bgr, (640, 360), 120, (20, 20, 20), -1)

    # 3. Vẽ chi tiết phụ (ngôi sao / hình chữ nhật nhỏ góc phải dưới)
    cv2.rectangle(img_bgr, (900, 500), (1050, 620), (40, 40, 40), 3)

    img_file = tmp_path / "test_scene_semantic.png"
    cv2.imwrite(str(img_file), img_bgr)

    # Phân đoạn ngữ nghĩa
    result = auto_segment_image(
        scene_id="scene_semantic_01",
        image_path=img_file,
        duration_ms=6000,
        aspect_ratio="16:9",
    )

    assert result["sceneId"] == "scene_semantic_01"
    assert result["canvas"]["width"] == 1280
    assert result["canvas"]["height"] == 720
    assert result["sceneDurationMs"] == 6000

    elements = result["elements"]
    assert len(elements) == 3, f"Phải phát hiện 3 phân vùng ngữ nghĩa, nhận được {len(elements)}"

    labels = [el["label"] for el in elements]
    assert labels == ["background_setup", "main_character", "fine_details"]

    # Kiểm tra thứ tự tuần tự và thời gian không âm
    for idx, el in enumerate(elements):
        assert el["sequence"] == idx + 1
        assert el["reveal"]["startMs"] >= 0
        assert el["reveal"]["durationMs"] > 0

        # Kiểm tra handPath
        hp = el["handPath"]
        assert "start" in hp and "end" in hp
        start_x, start_y = hp["start"]
        end_x, end_y = hp["end"]
        assert 0 <= start_x <= canvas_w
        assert 0 <= start_y <= canvas_h
        assert 0 <= end_x <= canvas_w
        assert 0 <= end_y <= canvas_h

    # Kiểm tra protectedRegions
    assert len(elements[0]["reveal"]["protectedRegions"]) > 0, "Vùng nền phải bảo vệ vùng nhân vật"


def test_auto_segment_vertical_9_16(tmp_path: Path):
    """Kiểm tra auto_segment_image cho khung hình dọc 9:16 (TikTok/Shorts)."""
    canvas_w, canvas_h = 720, 1280
    img_bgr = np.full((canvas_h, canvas_w, 3), (215, 235, 245), dtype=np.uint8)

    # Vẽ nét ở nửa trên và nửa dưới
    cv2.rectangle(img_bgr, (50, 100), (650, 400), (20, 20, 20), 4)
    cv2.circle(img_bgr, (360, 800), 100, (20, 20, 20), -1)

    img_file = tmp_path / "test_vertical_semantic.png"
    cv2.imwrite(str(img_file), img_bgr)

    result = auto_segment_image(
        scene_id="scene_vert_01",
        image_path=img_file,
        duration_ms=5000,
        aspect_ratio="9:16",
    )

    assert result["canvas"]["width"] == 720
    assert result["canvas"]["height"] == 1280
    assert len(result["elements"]) >= 2

    # Tọa độ bàn tay phải nằm trong canvas dọc
    for el in result["elements"]:
        hp = el["handPath"]
        for pt in [hp["start"], hp["end"]]:
            assert 0 <= pt[0] <= 720
            assert 0 <= pt[1] <= 1280


def test_auto_segment_blank_image_fallback(tmp_path: Path):
    """Kiểm tra trường hợp ảnh trống không có nét mực, fallback tạo 1 element an toàn."""
    canvas_w, canvas_h = 1280, 720
    img_bgr = np.full((canvas_h, canvas_w, 3), (215, 235, 245), dtype=np.uint8)

    img_file = tmp_path / "test_blank.png"
    cv2.imwrite(str(img_file), img_bgr)

    result = auto_segment_image(
        scene_id="scene_blank",
        image_path=img_file,
        duration_ms=4000,
        aspect_ratio="16:9",
    )

    assert len(result["elements"]) == 1
    assert result["elements"][0]["label"] == "main_artwork"
    assert result["elements"][0]["reveal"]["durationMs"] == int(round(4000 * 0.85))


def test_render_export_request_hand_tool():
    """Kiểm tra RenderExportRequest nhận hand_tool_id và mặc định là hand-pen-modern."""
    dummy_scene = ExportSceneItem(id="scene-1", scene_index=1, text="Nội dung thử nghiệm")
    req_default = RenderExportRequest(
        project_id="test_p",
        title="Test Title",
        scenes=[dummy_scene],
    )
    assert req_default.hand_tool_id == "hand-pen-modern"

    req_custom = RenderExportRequest(
        project_id="test_p",
        title="Test Title",
        scenes=[dummy_scene],
        hand_tool_id="hand-marker",
    )
    assert req_custom.hand_tool_id == "hand-marker"

    req_no_hand = RenderExportRequest(
        project_id="test_p",
        title="Test Title",
        scenes=[dummy_scene],
        hand_tool_id="no_hand",
    )
    assert req_no_hand.hand_tool_id == "no_hand"


def test_whiteboard_render_config_hand_tool():
    """Kiểm tra WhiteboardRenderConfig cấu hình hand_tool_id và bare_tip."""
    cfg = WhiteboardRenderConfig(
        hand_tool_id="hand-quill-vintage",
        bare_tip=False,
    )
    assert cfg.hand_tool_id == "hand-quill-vintage"
    assert cfg.bare_tip is False

    cfg_no_hand = WhiteboardRenderConfig(
        hand_tool_id="no_hand",
        bare_tip=True,
    )
    assert cfg_no_hand.hand_tool_id == "no_hand"
    assert cfg_no_hand.bare_tip is True


def test_create_scene_annotation_integration(tmp_path: Path):
    """Kiểm tra _create_scene_annotation sinh file annotation đa vùng ngữ nghĩa và đọc lại đúng."""
    img_path = tmp_path / "scene_annot.png"
    img_bgr = np.full((720, 1280, 3), (215, 235, 245), dtype=np.uint8)
    cv2.rectangle(img_bgr, (100, 100), (500, 500), (0, 0, 0), 3)
    cv2.imwrite(str(img_path), img_bgr)

    annot_path = tmp_path / "scene_annot.annotation.json"
    _create_scene_annotation(
        scene_id="sc_test_01",
        image_path=img_path,
        duration_ms=4500,
        output_annot_path=annot_path,
        aspect_ratio="16:9",
    )

    assert annot_path.exists()
    with open(annot_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["sceneId"] == "sc_test_01"
    assert data["sceneDurationMs"] == 4500
    assert len(data["elements"]) >= 1
    assert "handPath" in data["elements"][0]
