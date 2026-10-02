from pathlib import Path
import pytest

from core.drawing.debug_renderer import DebugRenderer
from core.drawing.extractor import SVGStrokeExtractor
from core.drawing.hand_path import HandPathPlanner, transform_strokes_to_canvas
from core.drawing.sorter import StrokeOrderPlanner
from core.schemas.drawing import DrawingStroke


@pytest.fixture
def tree_svg_path():
    return Path("assets/library/svg/tree_palm.svg")


@pytest.fixture
def monkey_climb_svg_path():
    return Path("assets/library/svg/monkey_climbing.svg")


@pytest.fixture
def banana_svg_path():
    return Path("assets/library/svg/banana_bunch.svg")


def test_stroke_extraction_tree(tree_svg_path):
    """Kiểm tra trích xuất nét vẽ từ file SVG cây dừa."""
    strokes, view_box = SVGStrokeExtractor.extract_strokes_from_svg(
        tree_svg_path, asset_id="tree_palm", asset_name="tree"
    )
    assert len(strokes) >= 10, "Tree SVG phải trích xuất được ít nhất 10 nét vẽ"
    assert view_box == "0 0 600 800"

    # Kiểm tra tính hợp lệ của từng nét vẽ
    for s in strokes:
        assert s.id != ""
        assert s.asset_id == "tree_palm"
        assert len(s.points) >= 2
        assert s.length > 0.0
        assert s.start_point == s.points[0]
        assert s.end_point == s.points[-1]
        assert s.duration > 0.0


def test_stroke_order_tree(tree_svg_path):
    """Kiểm tra thứ tự vẽ logic của cây: trunk -> branches -> leaves."""
    strokes, _ = SVGStrokeExtractor.extract_strokes_from_svg(
        tree_svg_path, asset_id="tree_palm", asset_name="tree"
    )
    ordered_strokes = StrokeOrderPlanner.sort_and_time_strokes(
        strokes, asset_name="tree", total_duration_sec=3.0
    )

    # Lấy danh sách semantic purpose theo thứ tự order
    purposes = [s.semantic_purpose for s in ordered_strokes]
    assert "trunk" in purposes
    assert "leaves" in purposes

    first_trunk_idx = purposes.index("trunk")
    last_leaves_idx = len(purposes) - 1 - purposes[::-1].index("leaves")

    # Trunk phải được vẽ trước leaves
    assert first_trunk_idx < last_leaves_idx, "Thân cây (trunk) phải được vẽ trước tán lá (leaves)"


def test_stroke_order_monkey(monkey_climb_svg_path):
    """Kiểm tra thứ tự vẽ của chú khỉ: body/head trước, sau đó đến limbs (arms/legs)."""
    strokes, _ = SVGStrokeExtractor.extract_strokes_from_svg(
        monkey_climb_svg_path, asset_id="monkey_climbing", asset_name="monkey"
    )
    ordered_strokes = StrokeOrderPlanner.sort_and_time_strokes(
        strokes, asset_name="monkey", total_duration_sec=3.0
    )

    purposes = [s.semantic_purpose for s in ordered_strokes]
    assert "body" in purposes or "head" in purposes

    if "body" in purposes and "arms" in purposes:
        assert purposes.index("body") < purposes.index("arms"), "Thân mình (body) phải vẽ trước tay (arms)"


def test_stroke_order_banana(banana_svg_path):
    """Kiểm tra thứ tự vẽ của chuối: banana_body trước stem."""
    strokes, _ = SVGStrokeExtractor.extract_strokes_from_svg(
        banana_svg_path, asset_id="banana_bunch", asset_name="banana"
    )
    ordered_strokes = StrokeOrderPlanner.sort_and_time_strokes(
        strokes, asset_name="banana", total_duration_sec=2.0
    )

    purposes = [s.semantic_purpose for s in ordered_strokes]
    assert "banana_body" in purposes
    assert "stem" in purposes
    assert purposes.index("banana_body") < purposes.index("stem"), "Thân quả chuối phải vẽ trước cuống chuối"


def test_stroke_duration_and_timing(tree_svg_path):
    """Kiểm tra tính toán thời lượng nét vẽ tỉ lệ theo chiều dài hình học."""
    strokes, _ = SVGStrokeExtractor.extract_strokes_from_svg(tree_svg_path)
    target_dur = 4.0
    ordered = StrokeOrderPlanner.sort_and_time_strokes(strokes, total_duration_sec=target_dur)

    total_stroke_dur = sum(s.duration for s in ordered)
    # Tổng thời lượng xấp xỉ target_dur (cho phép sai số làm tròn tối thiểu mỗi nét 0.05s)
    assert abs(total_stroke_dur - target_dur) < 1.0
    assert all(s.duration >= 0.05 for s in ordered)


def test_coordinate_conversion():
    """Kiểm tra hàm transform_strokes_to_canvas chuyển đổi đúng hệ tọa độ."""
    test_stroke = DrawingStroke(
        id="s1",
        points=[(0.0, 0.0), (300.0, 400.0)],
        start_point=(0.0, 0.0),
        end_point=(300.0, 400.0),
        length=500.0,
    )
    # ViewBox 0 0 600 800 -> Canvas Box (100, 200, 300, 400)
    transformed = transform_strokes_to_canvas(
        [test_stroke],
        view_box="0 0 600 800",
        target_x=100.0,
        target_y=200.0,
        target_width=300.0,
        target_height=400.0,
    )
    assert len(transformed) == 1
    t_s = transformed[0]
    # Kiểm tra các điểm nằm trọn trong vùng target
    for pt in t_s.points:
        assert 100.0 <= pt[0] <= 400.0
        assert 200.0 <= pt[1] <= 600.0


def test_hand_position_computation(monkey_climb_svg_path):
    """Kiểm tra tính toán tọa độ bàn tay tại các mốc thời gian khác nhau."""
    strokes, _ = SVGStrokeExtractor.extract_strokes_from_svg(monkey_climb_svg_path)
    ordered = StrokeOrderPlanner.sort_and_time_strokes(strokes, total_duration_sec=2.0)
    planner = HandPathPlanner(ordered, travel_duration_sec=0.05)

    # 1. Tại thời điểm t = 0 (bắt đầu nét đầu tiên)
    state_start = planner.get_hand_state(0.0)
    assert state_start.is_drawing is True
    assert state_start.x == ordered[0].start_point[0]
    assert state_start.y == ordered[0].start_point[1]
    assert state_start.stroke_id == ordered[0].id

    # 2. Tại thời điểm kết thúc
    state_end = planner.get_hand_state(planner.total_duration_sec)
    assert state_end.x == ordered[-1].end_point[0]
    assert state_end.y == ordered[-1].end_point[1]

    # 3. Lấy mẫu trajectory 30 fps
    samples = planner.sample_trajectory(fps=30)
    assert len(samples) > 30
    assert any(s.is_drawing for s in samples)


def test_debug_renderer_5_modes(tree_svg_path):
    """Kiểm tra xuất bản thành công đầy đủ cả 5 chế độ của DebugRenderer."""
    content = tree_svg_path.read_text(encoding="utf-8")
    strokes, view_box = SVGStrokeExtractor.extract_strokes_from_svg(tree_svg_path)
    ordered = StrokeOrderPlanner.sort_and_time_strokes(strokes, asset_name="tree", total_duration_sec=3.0)

    # Mode A: Original SVG
    mode_a = DebugRenderer.render_mode_a(content)
    assert "<svg" in mode_a and "</svg>" in mode_a

    # Mode B: Stroke Order
    mode_b = DebugRenderer.render_mode_b(ordered, view_box)
    assert "badges_layer" in mode_b
    assert "hsl(" in mode_b

    # Mode C: Animated Stroke Drawing (Kiểm tra nét xuất hiện dần, không hiển thị toàn bộ cùng lúc)
    mode_c = DebugRenderer.render_mode_c(ordered, view_box, total_duration_sec=3.0)
    assert "stroke-dasharray" in mode_c
    assert "stroke-dashoffset" in mode_c
    assert "anim-stroke" in mode_c

    # Mode D: Hand Following Stroke
    mode_d = DebugRenderer.render_mode_d(ordered, view_box, total_duration_sec=3.0)
    assert "hand_layer" in mode_d
    assert "drawing-hand" in mode_d

    # Mode E: Final Drawing
    mode_e = DebugRenderer.render_mode_e(ordered, view_box)
    assert "Final Completed Drawing" in mode_e
    assert "</svg>" in mode_e
