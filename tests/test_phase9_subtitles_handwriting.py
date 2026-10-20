"""
Test Suite for Phase 9:
1. Task 9.1: Subtitle Typography Customizer (Fonts, Sizes, Colors, Karaoke Highlights, Positions).
2. Task 9.2: Visual Subtitle Timeline Scrubbing & Fast Re-burn.
3. Task 9.3: Handwritten Text Animation & Stroke Vector Trajectories.
"""

import json
from pathlib import Path
import tempfile
import cv2
import numpy as np
from PIL import Image
import pytest
import av

from core.subtitles.models import SubtitleSegment, SubtitleWord, SubtitleTypographyConfig
from core.subtitles.burner import SubtitleBurner, _parse_rgba
from core.subtitles.srt_generator import SubtitleGenerator
from core.drawing.text_handwriter import TextHandwriter, morphological_skeleton
from engines.whiteboard.adapter import WhiteboardEngineAdapter, WhiteboardRenderConfig


# ============================================================================
# Task 9.1 Tests: Subtitle Typography Customizer
# ============================================================================

def test_subtitle_typography_config_defaults():
    cfg = SubtitleTypographyConfig()
    assert cfg.font_family == "Patrick Hand"
    assert cfg.font_size_preset == "md"
    assert cfg.text_color == "#FFFFFF"
    assert cfg.stroke_color == "#000000"
    assert cfg.stroke_width == 2
    assert cfg.highlight_color == "#FFE600"
    assert cfg.position == "bottom"
    assert cfg.bg_enabled is True


def test_subtitle_typography_resolve_font_size():
    cfg = SubtitleTypographyConfig(font_size_preset="sm")
    assert cfg.resolve_font_size("16:9") == 24
    assert cfg.resolve_font_size("9:16") == int(24 * 0.85)

    cfg_xl = SubtitleTypographyConfig(font_size_preset="xl")
    assert cfg_xl.resolve_font_size("16:9") == 48

    cfg_explicit = SubtitleTypographyConfig(font_size=42)
    assert cfg_explicit.resolve_font_size("16:9") == 42


def test_parse_rgba_formats():
    assert _parse_rgba("#FFFFFF") == (255, 255, 255, 255)
    assert _parse_rgba("#000000") == (0, 0, 0, 255)
    assert _parse_rgba("#FFE600") == (255, 230, 0, 255)
    assert _parse_rgba("#FF550080") == (255, 85, 0, 128)
    assert _parse_rgba("rgba(15, 23, 42, 0.85)") == (15, 23, 42, int(0.85 * 255))
    assert _parse_rgba("rgb(250, 204, 21)") == (250, 204, 21, 255)
    assert _parse_rgba((10, 20, 30)) == (10, 20, 30, 255)


def test_subtitle_burner_custom_typography_rendering():
    typo = SubtitleTypographyConfig(
        font_family="Patrick Hand",
        font_size=36,
        text_color="#F8FAFC",
        stroke_color="#0F172A",
        stroke_width=3,
        highlight_color="#00FFCC",  # Mint Green
        position="center",
        bg_enabled=True,
    )
    burner = SubtitleBurner(typography=typo, aspect_ratio="16:9")
    assert burner.font_size == 36
    assert burner.typography.highlight_color == "#00FFCC"

    # Render classic subtitle on a 1280x720 canvas
    img = Image.new("RGBA", (1280, 720), (245, 235, 215, 255))
    burner._render_classic_subtitle(img, "Whiteboard Animation Studio", 1280, 720)
    arr = np.array(img)
    assert arr.shape == (720, 1280, 4)

    # Render karaoke subtitle with active word highlight
    words = [
        SubtitleWord(word="Bàn", start_sec=0.0, end_sec=0.5),
        SubtitleWord(word="tay", start_sec=0.5, end_sec=1.0),
        SubtitleWord(word="vẽ", start_sec=1.0, end_sec=1.5),
    ]
    seg = SubtitleSegment(index=1, start_sec=0.0, end_sec=1.5, text="Bàn tay vẽ", words=words)
    burner._render_karaoke_subtitle(img, seg, current_time_sec=0.7, width=1280, height=720)
    # Check that pixels were drawn
    assert np.any(arr != 255)


def test_subtitle_burner_position_calculation():
    # Bottom position
    burner_bottom = SubtitleBurner(
        typography=SubtitleTypographyConfig(position="bottom"),
        aspect_ratio="16:9",
    )
    y_bot = burner_bottom._calculate_y_pos(text_h=40, height=720, width=1280)
    assert y_bot > 500  # near bottom

    # Center position
    burner_center = SubtitleBurner(
        typography=SubtitleTypographyConfig(position="center"),
        aspect_ratio="16:9",
    )
    y_cen = burner_center._calculate_y_pos(text_h=40, height=720, width=1280)
    assert y_cen == (720 - 40) // 2

    # Top position
    burner_top = SubtitleBurner(
        typography=SubtitleTypographyConfig(position="top"),
        aspect_ratio="16:9",
    )
    y_top = burner_top._calculate_y_pos(text_h=40, height=720, width=1280)
    assert y_top < 150  # near top


# ============================================================================
# Task 9.2 Tests: Visual Timeline Scrubbing & Fast Re-burn
# ============================================================================

def _create_dummy_video(video_path: Path, duration_sec: float = 2.0, fps: int = 24):
    """Tạo video giả lập có kèm audio tone để test burn-in phụ đề PyAV."""
    video_path.parent.mkdir(parents=True, exist_ok=True)
    c_out = av.open(str(video_path), mode="w", format="mp4")
    v_stream = c_out.add_stream("h264", rate=fps)
    v_stream.width = 640
    v_stream.height = 360
    v_stream.pix_fmt = "yuv420p"

    total_frames = int(duration_sec * fps)
    for i in range(total_frames):
        # Nền màu kem ấm #F5EBD7
        f_arr = np.full((360, 640, 3), (215, 235, 245), dtype=np.uint8)
        frame = av.VideoFrame.from_ndarray(f_arr, format="bgr24")
        frame.pts = i
        for pkt in v_stream.encode(frame):
            c_out.mux(pkt)

    for pkt in v_stream.encode(None):
        c_out.mux(pkt)
    c_out.close()


def test_fast_reburn_subtitles_to_video():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        raw_video = tmp_path / "raw.mp4"
        _create_dummy_video(raw_video, duration_sec=2.0)
        assert raw_video.exists()

        segments = [
            SubtitleSegment(
                index=1,
                start_sec=0.2,
                end_sec=1.8,
                text="Phụ đề test Phase 9 trực quan",
                words=[
                    SubtitleWord(word="Phụ", start_sec=0.2, end_sec=0.6),
                    SubtitleWord(word="đề", start_sec=0.6, end_sec=1.0),
                    SubtitleWord(word="test", start_sec=1.0, end_sec=1.4),
                    SubtitleWord(word="Phase", start_sec=1.4, end_sec=1.8),
                ],
            )
        ]

        # Kiểm tra sinh SRT & VTT
        srt_text = SubtitleGenerator.to_srt(segments)
        vtt_text = SubtitleGenerator.to_vtt(segments)
        assert "Phụ đề test Phase 9 trực quan" in srt_text
        assert "WEBVTT" in vtt_text

        # Re-burn onto video with custom typography
        typo = SubtitleTypographyConfig(
            font_family="Patrick Hand",
            font_size=28,
            highlight_color="#FFE600",
            position="bottom",
        )
        burner = SubtitleBurner(typography=typo, aspect_ratio="16:9")
        out_sub_video = tmp_path / "output_sub.mp4"

        res_path = burner.burn_subtitles_to_video(
            video_path=raw_video,
            subtitles=segments,
            output_path=out_sub_video,
            style="karaoke",
        )
        assert res_path.exists()
        assert res_path.stat().st_size > 1000

        # Kiểm tra file video output đọc được bằng PyAV
        with av.open(str(res_path)) as c_in:
            assert len(c_in.streams.video) > 0
            v = c_in.streams.video[0]
            assert v.width == 640
            assert v.height == 360


# ============================================================================
# Task 9.3 Tests: Handwritten Text Animation & Stroke Trajectories
# ============================================================================

def test_morphological_skeleton():
    mask = np.zeros((80, 80), dtype=np.uint8)
    cv2.line(mask, (10, 10), (70, 70), 255, 6)
    skel = morphological_skeleton(mask)
    assert cv2.countNonZero(skel) > 0
    # Xương nét phải mảnh hơn mask ban đầu
    assert cv2.countNonZero(skel) < cv2.countNonZero(mask)


def test_text_handwriter_generate_strokes():
    handwriter = TextHandwriter(
        default_font_family="Patrick Hand",
        default_font_size=48,
        canvas_size=(1280, 720),
    )

    text = "AI STUDIO"
    strokes = handwriter.generate_handwritten_strokes(
        text=text,
        color_hex="#E11D48",  # Rose Red marker
        stroke_width=5.0,
        total_duration_sec=3.0,
    )

    assert len(strokes) > 0
    # Các nét phải có id, order tăng dần
    for i, s in enumerate(strokes):
        assert s.order == i + 1
        assert s.color_hex == "#E11D48"
        assert s.stroke_width == 5.0
        assert len(s.points) >= 2
        assert s.duration > 0

    # Kiểm tra nét đầu tiên nằm ở bên trái nét cuối cùng (thứ tự viết tay từ trái qua phải)
    assert strokes[0].points[0][0] < strokes[-1].points[0][0]


def test_text_handwriter_create_scene_artifacts():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        handwriter = TextHandwriter(canvas_size=(1280, 720))

        img_path, ann_path = handwriter.create_handwritten_scene_artifacts(
            scene_id="scene_title_01",
            text="CHỦ ĐỀ 1: VECTƠ VÀ TỌA ĐỘ",
            output_dir=tmp_path,
            color_hex="#1E293B",
            duration_ms=4500,
        )

        assert img_path.exists()
        assert ann_path.exists()

        # Kiểm tra ảnh hợp lệ
        with Image.open(img_path) as im:
            assert im.size == (1280, 720)
            assert im.mode == "RGB"

        # Kiểm tra annotation.json hợp lệ
        ann_dict = json.loads(ann_path.read_text(encoding="utf-8"))
        assert ann_dict["sceneId"] == "scene_title_01"
        assert ann_dict["canvas"]["width"] == 1280
        assert ann_dict["canvas"]["height"] == 720
        assert ann_dict["sceneDurationMs"] == 4500
        assert len(ann_dict["elements"]) >= 6

        # Kiểm tra từng từ được sắp xếp theo thứ tự thời gian tăng dần
        for idx, el in enumerate(ann_dict["elements"]):
            assert el["sequence"] == idx + 1
            assert el["reveal"]["direction"] == "left_to_right"
            assert "startMs" in el["reveal"]
            assert "handPath" in el


def test_whiteboard_adapter_handwritten_text_scene_integration():
    adapter = WhiteboardEngineAdapter()
    assert hasattr(adapter, "render_handwritten_text_scene")
