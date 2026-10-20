from __future__ import annotations

import math
from pathlib import Path

import cv2
import numpy as np
import pytest

from core.drawing.vectorizer import (
    BitmapStrokeVectorizer,
    VectorStrokeSegment,
    chaikin_smooth,
    compute_polyline_length,
    ramer_douglas_peucker,
)
from core.drawing.stroke_order import NaturalStrokeSorter
from core.drawing.hand_path import HandPathPlanner
from core.schemas.drawing import DrawingStroke
from core.transitions.eraser import WhiteboardEraserTransition
from scripts.render_stream_whiteboard import TOOL_TIP_CALIBRATION
import scripts.stream_render as sr


# ==============================================================================
# 1. TEST VECTORIZER (Task 6.1)
# ==============================================================================

def test_rdp_simplification():
    """Kiểm tra thuật toán RDP giảm bớt điểm thẳng hàng dư thừa."""
    # Đường thẳng 10 điểm cùng nằm trên y=50
    straight_line = [(float(x), 50.0) for x in range(0, 100, 10)]
    simplified = ramer_douglas_peucker(straight_line, epsilon=1.0)
    # Đường thẳng hoàn hảo chỉ cần điểm đầu và điểm cuối
    assert len(simplified) == 2
    assert simplified[0] == straight_line[0]
    assert simplified[-1] == straight_line[-1]


def test_chaikin_smooth():
    """Kiểm tra thuật toán cắt góc Chaikin làm mềm mại đường cong gấp khúc."""
    sharp_corner = [(0.0, 0.0), (50.0, 100.0), (100.0, 0.0)]
    smoothed = chaikin_smooth(sharp_corner, iterations=2)
    assert len(smoothed) > len(sharp_corner)
    # Điểm đầu và điểm cuối được giữ nguyên
    assert smoothed[0] == sharp_corner[0]
    assert smoothed[-1] == sharp_corner[-1]
    # Chiều dài sau khi bo góc phải hợp lý
    orig_len = compute_polyline_length(sharp_corner)
    smooth_len = compute_polyline_length(smoothed)
    assert 0 < smooth_len <= orig_len


def test_bitmap_stroke_vectorizer():
    """Kiểm tra trích xuất nét vẽ vector từ ảnh raster tổng hợp."""
    # Tạo ảnh trắng 400x400 có 2 nét vẽ đen
    canvas = np.full((400, 400, 3), 255, dtype=np.uint8)
    # Nét 1: Nét cong dài (outline)
    pts1 = np.array([[50, 50], [150, 80], [250, 50], [350, 100]], dtype=np.int32)
    cv2.polylines(canvas, [pts1], isClosed=False, color=(20, 20, 20), thickness=4)
    # Nét 2: Nét ngắn chi tiết (detail)
    cv2.line(canvas, (100, 250), (130, 250), (20, 20, 20), thickness=3)

    vectorizer = BitmapStrokeVectorizer(min_stroke_length=5.0)
    segments = vectorizer.vectorize_image(canvas, asset_id="test_art")

    assert len(segments) >= 1, "Phải trích xuất được ít nhất 1 nét vẽ vector"
    for seg in segments:
        assert seg.id.startswith("test_art_stroke_")
        assert len(seg.points) >= 2
        assert seg.length > 0
        assert seg.category in ["outline", "structure", "detail", "shading"]

    # Chuyển đổi sang DrawingStroke
    drawing_strokes = vectorizer.to_drawing_strokes(segments, asset_id="test_art")
    assert len(drawing_strokes) == len(segments)
    assert all(isinstance(s, DrawingStroke) for s in drawing_strokes)


# ==============================================================================
# 2. TEST NATURAL STROKE ORDER & TSP OPTIMIZATION (Task 6.1)
# ==============================================================================

def test_natural_stroke_sorter_hierarchy():
    """Kiểm tra thứ tự ưu tiên mỹ thuật: outline -> structure -> detail -> shading."""
    s_shading = DrawingStroke(
        id="s1", asset_id="a1", path="", order=1, duration=0.2,
        start_point=(100, 100), end_point=(110, 110),
        semantic_purpose="shading", points=[(100, 100), (110, 110)], length=15.0,
    )
    s_outline = DrawingStroke(
        id="s2", asset_id="a1", path="", order=2, duration=0.5,
        start_point=(200, 200), end_point=(350, 350),
        semantic_purpose="outline", points=[(200, 200), (350, 350)], length=200.0,
    )
    s_detail = DrawingStroke(
        id="s3", asset_id="a1", path="", order=3, duration=0.3,
        start_point=(150, 150), end_point=(180, 180),
        semantic_purpose="detail", points=[(150, 150), (180, 180)], length=40.0,
    )

    ordered = NaturalStrokeSorter.sort_strokes_naturally([s_shading, s_outline, s_detail])
    purposes = [s.semantic_purpose for s in ordered]
    assert purposes == ["outline", "detail", "shading"], "Outline phải vẽ trước detail, shading vẽ cuối cùng"


def test_natural_stroke_sorter_tsp_reverse():
    """Kiểm tra tối ưu hành trình nhấc bút: tự động đảo chiều nét nếu điểm cuối gần hơn."""
    # Nét 1: từ (10, 10) đến (100, 100)
    stroke1 = DrawingStroke(
        id="st1", asset_id="art", path="", order=1, duration=0.5,
        start_point=(10.0, 10.0), end_point=(100.0, 100.0),
        semantic_purpose="outline", points=[(10.0, 10.0), (100.0, 100.0)], length=127.0,
    )
    # Nét 2: được định nghĩa từ (300, 300) đến (102, 102) -> điểm cuối gần điểm kết thúc của Nét 1 hơn rất nhiều!
    stroke2 = DrawingStroke(
        id="st2", asset_id="art", path="", order=2, duration=0.5,
        start_point=(300.0, 300.0), end_point=(102.0, 102.0),
        semantic_purpose="outline", points=[(300.0, 300.0), (102.0, 102.0)], length=280.0,
    )

    ordered = NaturalStrokeSorter.sort_strokes_naturally([stroke1, stroke2], allow_reverse_direction=True)
    assert len(ordered) == 2
    # Nét 2 phải được tự động đảo chiều: điểm bắt đầu mới phải gần (100, 100)
    assert ordered[1].start_point == (102.0, 102.0), "Nét vẽ tiếp theo phải được đảo chiều để điểm xuất phát gần đầu bút nhất"


# ==============================================================================
# 3. TEST PEN TIP CALIBRATION & HAND DYNAMICS (Task 6.2)
# ==============================================================================

def test_tool_tip_calibration_registry():
    """Kiểm tra bảng căn chỉnh tọa độ ngòi bút của các công cụ vẽ."""
    expected_tools = [
        "hand-pen-modern",
        "hand-marker",
        "hand-calligraphy",
        "hand-quill-vintage",
        "hand-highlighter",
        "hand-eraser",
    ]
    for tool in expected_tools:
        assert tool in TOOL_TIP_CALIBRATION
        ax, ay = TOOL_TIP_CALIBRATION[tool]
        assert 0.0 <= ax <= 1.0
        assert 0.0 <= ay <= 1.0


def test_tip_overlay_with_angle_rotation():
    """Kiểm tra TipOverlay xoay góc ngòi bút mượt mà quanh điểm neo (tangential rotation)."""
    # Tạo dummy hand và mask
    hand_bgr = np.full((100, 80, 3), (50, 150, 220), dtype=np.uint8)
    mask = np.ones((100, 80), dtype=np.float32)

    overlay = sr.TipOverlay(hand_bgr, mask, tip_anchor_x=0.1, tip_anchor_y=0.05)
    canvas = np.zeros((300, 300, 3), dtype=np.uint8)

    # Thử nghiệm dập ngòi với góc xoay 10 độ
    stamped = overlay.stamp(canvas.copy(), 150, 150, angle_deg=10.0)
    assert stamped.shape == (300, 300, 3)
    # Vùng xung quanh (150, 150) phải được vẽ lên
    assert np.any(stamped[140:160, 140:160] > 0)


# ==============================================================================
# 4. TEST MULTI-PEN ASSETS & TOOLS (Task 6.3)
# ==============================================================================

def test_highlighter_asset_presence():
    """Kiểm tra file asset hand-highlighter.png tồn tại và có kênh alpha hợp lệ."""
    hl_path = Path("assets/drawing-tools/hand-highlighter.png")
    assert hl_path.exists(), "Asset hand-highlighter.png phải tồn tại"
    img = cv2.imread(str(hl_path), cv2.IMREAD_UNCHANGED)
    assert img is not None
    assert img.shape[2] == 4, "Highlighter phải là ảnh 4 kênh RGBA"
    assert np.any(img[:, :, 3] > 0), "Kênh alpha phải có nội dung"


def test_eraser_asset_presence():
    """Kiểm tra file asset hand-eraser.png tồn tại và có kênh alpha hợp lệ."""
    eraser_path = Path("assets/drawing-tools/hand-eraser.png")
    assert eraser_path.exists(), "Asset hand-eraser.png phải tồn tại"
    img = cv2.imread(str(eraser_path), cv2.IMREAD_UNCHANGED)
    assert img is not None
    assert img.shape[2] == 4, "Eraser phải là ảnh 4 kênh RGBA"
    assert np.any(img[:, :, 3] > 0), "Kênh alpha phải có nội dung"


def test_eraser_sfx_presence():
    """Kiểm tra file âm thanh tiếng giẻ lau bảng eraser_wipe.mp3 tồn tại."""
    sfx_path = Path("assets/audio/sfx/eraser_wipe.mp3")
    assert sfx_path.exists(), "Asset âm thanh eraser_wipe.mp3 phải tồn tại"
    assert sfx_path.stat().st_size > 1000, "File eraser_wipe.mp3 không được rỗng"


# ==============================================================================
# 5. TEST WHITEBOARD ERASER TRANSITION (Task 6.4)
# ==============================================================================

def test_whiteboard_eraser_transition_generation(tmp_path):
    """Kiểm tra sinh hiệu ứng lau bảng chuyển cảnh (Whiteboard Eraser Wipe)."""
    # Khung hình 1: Đầy nét vẽ màu
    frame1 = np.full((360, 640, 3), (40, 120, 200), dtype=np.uint8)
    cv2.putText(frame1, "SCENE 1 OLD", (100, 180), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 3)

    # Khung hình 2: Tranh phân cảnh tiếp theo
    frame2 = np.full((360, 640, 3), (215, 235, 245), dtype=np.uint8)  # #F5EBD7
    cv2.putText(frame2, "SCENE 2 NEW", (100, 180), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (20, 20, 20), 3)

    transition = WhiteboardEraserTransition(fps=15, duration_sec=0.5)
    frames = transition.generate_transition_frames(frame1, frame2)

    assert len(frames) == int(round(15 * 0.5))
    assert frames[0].shape == (360, 640, 3)

    # Khung hình đầu tiên chủ yếu là cảnh 1
    # Khung hình cuối cùng phải được lau sạch
    last_frame = frames[-1]
    # Kiểm tra màu nền giấy kem ấm #F5EBD7 xuất hiện chiếm đa số
    cream_diff = np.abs(last_frame.astype(np.int16) - np.array([215, 235, 245])).sum(axis=2)
    # Phần lớn canvas cuối cùng phải sạch sẽ
    assert np.mean(cream_diff < 50) > 0.40

    # Kết xuất video mp4 thử nghiệm
    out_mp4 = tmp_path / "test_transition.mp4"
    res_path = transition.render_transition_video(frame1, frame2, out_mp4)
    assert res_path.exists()
    assert res_path.stat().st_size > 500
