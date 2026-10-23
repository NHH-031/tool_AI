import numpy as np
import pytest
from core.artwork.filter_sketch import SketchFilter
from core.artwork.gemini_director import GeminiScriptDirector
from core.artwork.prompt_builder import IllustrationPromptBuilder, StructuredIllustrationPrompt
from core.artwork.style_profile import WhiteboardVisualStyleProfile
from core.artwork.translator import create_whiteboard_art_prompt
from core.drawing.stroke_order import NaturalStrokeSorter
from core.schemas.drawing import DrawingStroke
from core.schemas.scene_graph import SceneGraph, VisualEntity


def test_drawing_order_dual_layer_extraction():
    """Kiểm tra tính năng tách 2 lớp (Line-art vẽ trước, Color wash fade-in sau) trong SketchFilter."""
    filter_engine = SketchFilter()
    dummy_img = np.full((100, 100, 3), 128, dtype=np.uint8)
    dummy_img[45:55, :, :] = 0

    # 1. extract_dual_layers giữ nguyên kích thước ảnh đầu vào
    lineart, color = filter_engine.extract_dual_layers(dummy_img, contrast=1.2, line_strength=1.3)
    assert lineart.shape == (100, 100, 3)
    assert color.shape == (100, 100, 3)

    # Line-art layer có nền giấy kem #F5EBD7 (BGR: 215, 235, 245) và nét mực đen
    assert lineart[0, 0, 0] > 180  # B
    assert lineart[0, 0, 1] > 200  # G
    assert lineart[0, 0, 2] > 200  # R

    # 2. process_image với style="lineart", style="color", style="dual_layer" chuẩn hóa canvas 1080p
    proc_lineart = filter_engine.process_image(dummy_img, style="lineart")
    assert proc_lineart.shape == (1080, 1920, 3)

    proc_color = filter_engine.process_image(dummy_img, style="color")
    assert proc_color.shape == (1080, 1920, 3)

    dl_lineart, dl_color = filter_engine.process_image(dummy_img, style="dual_layer")
    assert dl_lineart.shape == (1080, 1920, 3)
    assert dl_color.shape == (1080, 1920, 3)


def test_stroke_order_color_fill_priority():
    """Kiểm tra priority của color_fill = 90 (vẽ sau nét outline, structure, detail, shading)."""
    assert "color_fill" in NaturalStrokeSorter.CATEGORY_PRIORITY
    assert NaturalStrokeSorter.CATEGORY_PRIORITY["color_fill"] == 90
    assert NaturalStrokeSorter.CATEGORY_PRIORITY["color_fill"] > NaturalStrokeSorter.CATEGORY_PRIORITY["shading"]
    assert NaturalStrokeSorter.CATEGORY_PRIORITY["color_fill"] > NaturalStrokeSorter.CATEGORY_PRIORITY["outline"]

    # Test sắp xếp với nét color_fill
    s_outline = DrawingStroke(
        id="s1",
        asset_id="a1",
        path="",
        order=1,
        duration=0.5,
        start_point=(10.0, 10.0),
        end_point=(20.0, 20.0),
        semantic_purpose="outline",
        points=[(10.0, 10.0), (20.0, 20.0)],
        length=14.0,
    )
    s_shading = DrawingStroke(
        id="s2",
        asset_id="a1",
        path="",
        order=2,
        duration=0.5,
        start_point=(30.0, 30.0),
        end_point=(40.0, 40.0),
        semantic_purpose="shading",
        points=[(30.0, 30.0), (40.0, 40.0)],
        length=14.0,
    )
    s_color = DrawingStroke(
        id="s3",
        asset_id="a1",
        path="",
        order=3,
        duration=0.5,
        start_point=(50.0, 50.0),
        end_point=(60.0, 60.0),
        semantic_purpose="color_fill",
        points=[(50.0, 50.0), (60.0, 60.0)],
        length=14.0,
    )

    ordered = NaturalStrokeSorter.sort_strokes_naturally([s_color, s_shading, s_outline])
    ordered_ids = [s.id for s in ordered]
    assert ordered_ids == ["s1", "s2", "s3"], f"Expected outline -> shading -> color_fill, got {ordered_ids}"


def test_manga_2d_style_keywords():
    """Kiểm tra các từ khóa phong cách Manga 2D và Negative constraints chống 3D/CGI."""
    # 1. StructuredIllustrationPrompt defaults
    prompt_struct = StructuredIllustrationPrompt(subject="a young hero")
    assert "manga" in prompt_struct.line_style.lower()
    assert "manga" in prompt_struct.whiteboard_style.lower()
    assert "no 3d render" in prompt_struct.negative_constraints.lower()
    assert "no cgi" in prompt_struct.negative_constraints.lower()

    # 2. WhiteboardVisualStyleProfile
    profile = WhiteboardVisualStyleProfile()
    assert "manga" in profile.character_style.lower()

    # 3. GeminiScriptDirector DEFAULT_STYLE_SUFFIX
    assert "manga" in GeminiScriptDirector.DEFAULT_STYLE_SUFFIX.lower()
    assert "strictly no 3d rendering" in GeminiScriptDirector.DEFAULT_STYLE_SUFFIX.lower()

    # 4. create_whiteboard_art_prompt in translator.py
    art_prompt = create_whiteboard_art_prompt("cậu bé dắt trâu trên đồng cỏ")
    assert "manga" in art_prompt.lower()
    assert "strictly 2d flat art" in art_prompt.lower()
    assert "no 3d render" in art_prompt.lower()


def test_object_fidelity_secondary_entities():
    """Kiểm tra độ chuẩn xác của vật thể tương tác (Object Fidelity) trong Scene Graph sang prompt."""
    sg = SceneGraph(
        scene_id="scene_test_cup",
        title="Bà lão làm rơi cốc nước",
        entities=[
            VisualEntity(
                id="e1",
                label="old_woman",
                visual_role="main_character",
                category="character",
                actions=["accidentally_dropping"],
            ),
            VisualEntity(
                id="e2",
                label="glass_of_water",
                visual_role="object",
                category="object",
                actions=["falling_mid_air"],
            ),
        ],
    )

    prompt = IllustrationPromptBuilder.build_from_scene_graph(sg)
    full_prompt_text = prompt.full_prompt

    # Vật thể phụ (cốc nước) BẮT BUỘC phải xuất hiện rõ ràng kèm trạng thái và chỉ thị "MUST be prominently shown"
    assert "glass of water" in full_prompt_text
    assert "falling mid air" in full_prompt_text
    assert "MUST be prominently shown" in full_prompt_text
    assert "old woman" in full_prompt_text
    assert "accidentally dropping" in full_prompt_text
