"""
Tests for Phase 3: Aspect Ratio Support (16:9 Landscape vs 9:16 Vertical TikTok/Shorts/Reels)
"""

import json
from pathlib import Path
import pytest
import numpy as np
from PIL import Image

from core.artwork.prompt_builder import StructuredIllustrationPrompt
from apps.api.routers.export import RenderExportRequest, ExportSceneItem, _create_scene_annotation
from engines.whiteboard.adapter import WhiteboardRenderConfig
from core.subtitles import SubtitleGenerator, SubtitleBurner


def test_structured_illustration_prompt_aspect_ratio():
    """Kiểm tra schema StructuredIllustrationPrompt hỗ trợ aspect_ratio."""
    prompt_default = StructuredIllustrationPrompt(
        subject="Robot",
        action="drawing on whiteboard",
        scene_context="modern classroom",
    )
    assert prompt_default.aspect_ratio == "16:9"

    prompt_vertical = StructuredIllustrationPrompt(
        subject="Robot",
        action="drawing on whiteboard",
        scene_context="modern classroom",
        aspect_ratio="9:16",
    )
    assert prompt_vertical.aspect_ratio == "9:16"


def test_render_export_request_aspect_ratio():
    """Kiểm tra RenderExportRequest nhận aspect_ratio 9:16 và mặc định 16:9."""
    dummy_scene = ExportSceneItem(id="scene-1", scene_index=1, text="Xin chào thế giới")
    req_default = RenderExportRequest(
        project_id="test_proj",
        title="Test Video",
        scenes=[dummy_scene],
    )
    assert req_default.aspect_ratio == "16:9"

    req_vertical = RenderExportRequest(
        project_id="test_proj",
        title="Test TikTok Video",
        scenes=[dummy_scene],
        aspect_ratio="9:16",
    )
    assert req_vertical.aspect_ratio == "9:16"


def test_create_scene_annotation_vertical(tmp_path: Path):
    """Kiểm tra file annotation sinh ra cho 9:16 điều chỉnh tọa độ bàn tay an toàn."""
    img_path = tmp_path / "test_vertical.png"
    # Tạo ảnh giả lập dọc 720x1280
    dummy_img = Image.new("RGB", (720, 1280), color=(245, 235, 215))
    dummy_img.save(img_path)

    annot_path = tmp_path / "test_vertical.annotation.json"
    _create_scene_annotation(
        scene_id="scene_vertical_1",
        image_path=img_path,
        duration_ms=5000,
        output_annot_path=annot_path,
        aspect_ratio="9:16",
    )

    assert annot_path.exists()
    data = json.loads(annot_path.read_text(encoding="utf-8"))
    assert data["canvas"]["width"] == 720
    assert data["canvas"]["height"] == 1280

    element = data["elements"][0]
    hand_start = element["handPath"]["start"]
    hand_end = element["handPath"]["end"]

    # Với dọc 9:16: hand_start = [w * 0.25, h * 0.18], hand_end = [w * 0.75, h * 0.82]
    assert hand_start[0] == int(720 * 0.25)
    assert hand_start[1] == int(1280 * 0.18)
    assert hand_end[0] == int(720 * 0.75)
    assert hand_end[1] == int(1280 * 0.82)


def test_create_scene_annotation_horizontal(tmp_path: Path):
    """Kiểm tra file annotation sinh ra cho 16:9 giữ tỷ lệ chuẩn widescreen."""
    img_path = tmp_path / "test_horizontal.png"
    dummy_img = Image.new("RGB", (1280, 720), color=(245, 235, 215))
    dummy_img.save(img_path)

    annot_path = tmp_path / "test_horizontal.annotation.json"
    _create_scene_annotation(
        scene_id="scene_horizontal_1",
        image_path=img_path,
        duration_ms=4000,
        output_annot_path=annot_path,
        aspect_ratio="16:9",
    )

    assert annot_path.exists()
    data = json.loads(annot_path.read_text(encoding="utf-8"))
    assert data["canvas"]["width"] == 1280
    assert data["canvas"]["height"] == 720

    element = data["elements"][0]
    hand_start = element["handPath"]["start"]
    hand_end = element["handPath"]["end"]

    assert hand_start[0] == int(1280 * 0.2)
    assert hand_start[1] == int(720 * 0.25)


def test_whiteboard_render_config_aspect_ratio():
    """Kiểm tra WhiteboardRenderConfig hỗ trợ aspect_ratio."""
    cfg = WhiteboardRenderConfig(
        fps=24,
        cap_long_edge=1280,
        aspect_ratio="9:16",
    )
    assert cfg.aspect_ratio == "9:16"
    assert cfg.cap_long_edge == 1280


def test_subtitle_burner_safe_zone_vertical():
    """Kiểm tra SubtitleBurner tính toán lề an toàn (safe-zone) cao hơn cho video 9:16 để tránh che bởi UI TikTok."""
    burner_vertical = SubtitleBurner(font_size=28, aspect_ratio="9:16")
    burner_horizontal = SubtitleBurner(font_size=32, aspect_ratio="16:9")

    # Giả lập frame dọc 720x1280 trong suốt
    img_v = Image.new("RGBA", (720, 1280), (0, 0, 0, 0))
    burner_vertical._render_classic_subtitle(img_v, "Kiểm tra phụ đề TikTok", 720, 1280)

    # Lấy alpha layer để xác định vị trí y của phụ đề
    alpha_v = np.array(img_v.split()[-1])
    active_rows_v = np.where(np.any(alpha_v > 0, axis=1))[0]
    assert len(active_rows_v) > 0
    y_min_v, y_max_v = active_rows_v[0], active_rows_v[-1]
    bottom_dist_v = 1280 - y_max_v

    # Khoảng cách từ đáy màn hình phải xấp xỉ ~16% của 1280 (~200px) thay vì chỉ 8% (~100px)
    assert bottom_dist_v >= int(1280 * 0.14)

    # Giả lập frame ngang 1280x720 trong suốt
    img_h = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    burner_horizontal._render_classic_subtitle(img_h, "Kiểm tra phụ đề YouTube", 1280, 720)
    alpha_h = np.array(img_h.split()[-1])
    active_rows_h = np.where(np.any(alpha_h > 0, axis=1))[0]
    y_max_h = active_rows_h[-1]
    bottom_dist_h = 720 - y_max_h

    # Tỷ lệ lề đáy của video dọc phải lớn hơn video ngang để tránh che bởi UI TikTok
    assert (bottom_dist_v / 1280) > (bottom_dist_h / 720)


def test_subtitle_segments_for_vertical_short_words():
    """Kiểm tra sinh phụ đề với max_words_per_segment=4 cho 9:16 để tránh tràn dòng."""
    scenes_data = [
        {
            "scene_index": 1,
            "text": "Pin năng lượng mặt trời hấp thụ ánh sáng và chuyển hóa thành điện năng sinh hoạt.",
            "duration_sec": 5.0,
        }
    ]
    segments_vertical = SubtitleGenerator.generate_project_subtitles(
        scenes_data,
        max_words_per_segment=4,
    )
    assert len(segments_vertical) >= 3
    for seg in segments_vertical:
        word_count = len(seg.text.split())
        assert word_count <= 4
