import base64
from pathlib import Path
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from core.artwork.character_anchor import CharacterAnchor, extract_character_from_script
from core.artwork.filter_sketch import SketchFilter, hex_to_bgr
from core.artwork.prompt_builder import IllustrationPromptBuilder
from core.schemas.scene_graph import SceneGraph, VisualEntity


# ==============================================================================
# 1. TEST SKETCH FILTER (Task 7.3)
# ==============================================================================

def test_hex_to_bgr():
    bgr = hex_to_bgr("#F5EBD7")
    # Red: F5 (245), Green: EB (235), Blue: D7 (215)
    # OpenCV BGR -> (215, 235, 245)
    assert bgr[0] == 215
    assert bgr[1] == 235
    assert bgr[2] == 245


def test_fit_and_pad_to_canvas():
    filter_engine = SketchFilter(canvas_hex="#F5EBD7")
    # Tạo ảnh vuông 400x400
    img = np.full((400, 400, 3), (50, 150, 250), dtype=np.uint8)
    canvas = filter_engine.fit_and_pad_to_canvas(img, target_size=(1920, 1080))

    assert canvas.shape == (1080, 1920, 3)
    # Góc ngoài cùng phải có màu nền kem ấm #F5EBD7
    corner_pixel = canvas[10, 10]
    assert np.array_equal(corner_pixel, np.array([215, 235, 245], dtype=np.uint8))


def test_convert_to_pure_ink():
    filter_engine = SketchFilter(canvas_hex="#F5EBD7")
    img = np.zeros((360, 640, 3), dtype=np.uint8)
    # Vẽ các hình khối đa dạng
    cv2.circle(img, (320, 180), 80, (255, 255, 255), -1)
    cv2.rectangle(img, (100, 100), (200, 260), (180, 180, 180), -1)

    sketch = filter_engine.convert_to_pure_ink(img, contrast=1.2)
    assert sketch.shape == (360, 640, 3)

    # Đảm bảo màu nền xung quanh có xu hướng nền kem ấm #F5EBD7
    # và các nét viền có xu hướng nét mực #1A1A1A
    assert sketch.mean() > 50


def test_convert_to_watercolor_comic():
    filter_engine = SketchFilter(canvas_hex="#F5EBD7")
    img = np.full((360, 640, 3), (80, 180, 240), dtype=np.uint8)
    cv2.putText(img, "TEST LOGO", (120, 180), cv2.FONT_HERSHEY_SIMPLEX, 2.0, (0, 0, 180), 4)

    comic = filter_engine.convert_to_watercolor_comic(img, contrast=1.1, line_strength=1.3)
    assert comic.shape == (360, 640, 3)
    # Kiểm tra không bị lỗi rỗng hay overflow
    assert comic.min() >= 0
    assert comic.max() <= 255


def test_sketch_filter_transparent_png():
    filter_engine = SketchFilter(canvas_hex="#F5EBD7")
    # Ảnh RGBA với nền trong suốt (alpha = 0) và hình tròn đỏ ở giữa (alpha = 255)
    rgba = np.zeros((200, 200, 4), dtype=np.uint8)
    cv2.circle(rgba, (100, 100), 50, (0, 0, 255, 255), -1)

    processed = filter_engine.process_image(
        image_input=rgba,
        style="watercolor_comic",
        target_size=(640, 360),
    )
    assert processed.shape == (360, 640, 3)
    # Vùng ngoài phải là màu nền giấy kem ấm
    corner = processed[10, 10]
    diff = np.abs(corner.astype(int) - np.array([215, 235, 245])).sum()
    assert diff < 35


# ==============================================================================
# 2. TEST CHARACTER CONSISTENCY ANCHOR (Task 7.2)
# ==============================================================================

def test_character_anchor_prompt_building():
    anchor = CharacterAnchor(
        name="Anh Nam",
        gender="male",
        age_group="adult",
        hair_style="short black hair parted neatly",
        facial_features="round black-rimmed spectacles, friendly expression",
        clothing="navy blue blazer over white collared shirt",
        seed=100,
    )
    prompt_clause = anchor.build_anchor_prompt()

    assert "Anh Nam" in prompt_clause
    assert "navy blue blazer" in prompt_clause
    assert "spectacles" in prompt_clause
    assert "[Character Identity Consistency]" in prompt_clause


def test_character_auto_extraction_vietnamese():
    script_text = (
        "Anh Nam là một kỹ sư phần mềm tại Hà Nội. "
        "Anh đeo kính cận và luôn mặc áo khoác hoodie màu tối khi làm việc."
    )
    anchor = extract_character_from_script(script_text)

    assert anchor is not None
    assert anchor.gender == "male"
    assert "kính" in anchor.facial_features or "spectacles" in anchor.facial_features
    assert "hoodie" in anchor.clothing


def test_prompt_builder_with_character_anchor():
    anchor = CharacterAnchor(
        name="Dr. Helen",
        gender="female",
        age_group="adult",
        hair_style="long curly brown hair",
        clothing="white lab coat",
        seed=42,
    )
    scene_graph = SceneGraph(
        scene_id="scene-01",
        title="Phòng thí nghiệm",
        entities=[
            VisualEntity(id="e1", label="Dr._Helen", visual_role="main_character"),
            VisualEntity(id="e2", label="microscope", visual_role="secondary"),
        ],
    )
    prompt_result = IllustrationPromptBuilder.build_from_scene_graph(
        scene_graph=scene_graph,
        character_anchor=anchor,
    )

    assert "[Character Identity Consistency]" in prompt_result.full_prompt
    assert "Dr. Helen" in prompt_result.full_prompt
    assert "white lab coat" in prompt_result.full_prompt


# ==============================================================================
# 3. TEST DOODLE VAULT (Task 7.4)
# ==============================================================================

def test_doodle_vault_presence():
    doodle_dir = Path(__file__).resolve().parent.parent / "assets" / "doodles"
    assert doodle_dir.exists(), "Thư mục assets/doodles phải tồn tại"

    svg_files = list(doodle_dir.glob("*.svg"))
    assert len(svg_files) >= 12, f"Cần có ít nhất 12 biểu tượng vector doodle, hiện có {len(svg_files)}"

    for f in svg_files:
        content = f.read_text(encoding="utf-8")
        assert "<svg" in content
        assert "</svg>" in content


# ==============================================================================
# 4. TEST STORYBOARD API ENDPOINTS (Task 7.1, 7.3, 7.4)
# ==============================================================================

client = TestClient(app)

def test_api_list_doodles():
    response = client.get("/storyboard/doodles/list")
    assert response.status_code == 200
    doodles = response.json()
    assert isinstance(doodles, list)
    assert len(doodles) >= 12
    assert "svg_content" in doodles[0]
    assert "category" in doodles[0]


def test_api_save_canvas_edit(tmp_path):
    # Tạo một ảnh canvas base64 đơn giản
    test_img = np.full((200, 300, 3), (215, 235, 245), dtype=np.uint8)
    cv2.putText(test_img, "EDITED", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (26, 26, 26), 2)
    _, buf = cv2.imencode(".png", test_img)
    b64_str = "data:image/png;base64," + base64.b64encode(buf.tobytes()).decode("utf-8")

    payload = {
        "project_id": "test_phase7_proj",
        "scene_id": "scene-1",
        "scene_index": 1,
        "image_data_base64": b64_str,
    }
    response = client.post("/storyboard/save-canvas-edit", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["scene_id"] == "scene-1"
    assert "scene_1.png" in data["image_url"]


def test_api_upload_custom_image_with_sketch_filter():
    # Tạo logo giả lập để upload
    logo = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.circle(logo, (100, 100), 60, (0, 255, 255), -1)
    _, buf = cv2.imencode(".png", logo)
    b64_str = "data:image/png;base64," + base64.b64encode(buf.tobytes()).decode("utf-8")

    payload = {
        "project_id": "test_phase7_proj",
        "scene_id": "scene-2",
        "scene_index": 2,
        "image_data_base64": b64_str,
        "apply_sketch_filter": True,
        "sketch_style": "watercolor_comic",
        "contrast": 1.2,
        "line_strength": 1.3,
        "aspect_ratio": "16:9",
    }
    response = client.post("/storyboard/upload-custom-image", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["scene_index"] == 2
    assert "scene_2.png" in data["image_url"]
