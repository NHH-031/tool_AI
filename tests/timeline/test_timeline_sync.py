import pytest
from pathlib import Path

from core.assets.providers import LocalAssetProvider
from core.schemas.scene_graph import Position, SceneGraph, VisualEntity, VisualRelationship
from core.schemas.timeline import DrawingTimeline, DrawingTimelineEvent
from core.schemas.tts import NarrationTiming, WordTiming
from core.timeline.synchronizer import DrawingTimelineSynchronizer


@pytest.fixture
def monkey_banana_scene_graph() -> SceneGraph:
    """Fixture tạo SceneGraph cho câu chuyện Con khỉ trèo cây lấy chuối."""
    sg = SceneGraph(
        scene_id="scene_monkey_banana_demo",
        description="Con khỉ đang trèo lên cây để lấy một quả chuối.",
    )
    sg.add_entity(
        VisualEntity(
            id="entity_tree",
            name="tree",
            label="tree",
            importance="primary",
            layer=1,
            position=Position(x=820, y=80, width=720, height=880),
        )
    )
    sg.add_entity(
        VisualEntity(
            id="entity_monkey",
            name="monkey",
            label="monkey",
            importance="primary",
            layer=2,
            action="climbing",
            position=Position(x=720, y=400, width=440, height=440),
        )
    )
    sg.add_entity(
        VisualEntity(
            id="entity_banana",
            name="banana",
            label="banana",
            importance="primary",
            layer=3,
            position=Position(x=1120, y=180, width=240, height=240),
        )
    )
    sg.add_relationship(
        VisualRelationship(
            source_id="entity_monkey",
            target_id="entity_tree",
            relation_type="climbing",
            description="monkey climbing tree",
        )
    )
    sg.add_relationship(
        VisualRelationship(
            source_id="entity_monkey",
            target_id="entity_banana",
            relation_type="reaching",
            description="monkey reaching banana",
        )
    )
    return sg


@pytest.fixture
def mock_narration_timing() -> NarrationTiming:
    """Timing chuẩn từ narration TTS cho câu: 'Con khỉ đang trèo lên cây để lấy một quả chuối.' (4.5s)"""
    return NarrationTiming(
        text="Con khỉ đang trèo lên cây để lấy một quả chuối.",
        duration=4.5,
        words=[
            WordTiming(word="Con", start_time=0.10, end_time=0.35),
            WordTiming(word="khỉ", start_time=0.35, end_time=0.75),
            WordTiming(word="đang", start_time=0.80, end_time=1.05),
            WordTiming(word="trèo", start_time=1.10, end_time=1.45),
            WordTiming(word="lên", start_time=1.45, end_time=1.70),
            WordTiming(word="cây", start_time=1.70, end_time=2.15),
            WordTiming(word="để", start_time=2.20, end_time=2.40),
            WordTiming(word="lấy", start_time=2.45, end_time=2.75),
            WordTiming(word="một", start_time=2.80, end_time=3.05),
            WordTiming(word="quả", start_time=3.10, end_time=3.40),
            WordTiming(word="chuối.", start_time=3.45, end_time=4.10),
        ],
        provider_name="MockTTSProvider",
        is_word_level=True,
    )


def test_timeline_generation_monkey_banana_demo(monkey_banana_scene_graph, mock_narration_timing):
    """Kiểm tra tạo DrawingTimeline chuẩn với đầy đủ các thuộc tính bắt buộc của Phase 08."""
    synchronizer = DrawingTimelineSynchronizer()
    timeline = synchronizer.build_timeline(
        narration_timing=mock_narration_timing,
        scene_graph=monkey_banana_scene_graph,
    )

    assert isinstance(timeline, DrawingTimeline)
    assert len(timeline.events) > 0
    assert timeline.total_duration >= mock_narration_timing.duration

    draw_events = [e for e in timeline.events if e.action == "draw"]
    travel_events = [e for e in timeline.events if e.action == "hand_travel"]

    assert len(draw_events) > 30, "Phải có đủ nét vẽ chi tiết cho monkey, tree và banana"
    assert len(travel_events) > 0, "Phải có các bước nhấc bút di chuyển tay (hand travel)"

    # Kiểm tra tính toàn vẹn của từng event
    for ev in timeline.events:
        assert ev.start_time <= ev.end_time
        assert ev.asset_id in ["monkey", "tree", "banana"]
        assert ev.stroke_id is not None
        assert ev.action in ["draw", "hand_travel"]
        assert len(ev.hand_path) >= 2, "hand_path phải có ít nhất 2 điểm tọa độ"
        assert ev.semantic_purpose is not None

        # Tọa độ trên canvas 1920x1080
        for pt in ev.hand_path:
            assert -50 <= pt[0] <= 1970
            assert -50 <= pt[1] <= 1130


def test_dynamic_timing_adaptation(monkey_banana_scene_graph):
    """Kiểm tra timing co giãn linh hoạt theo tốc độ TTS (Không hardcode thời lượng cố định)."""
    synchronizer = DrawingTimelineSynchronizer()

    # Audio ngắn (2.5 giây)
    fast_timing = NarrationTiming(
        text="Con khỉ trèo cây lấy chuối.",
        duration=2.5,
        words=[
            WordTiming(word="Con", start_time=0.05, end_time=0.25),
            WordTiming(word="khỉ", start_time=0.25, end_time=0.55),
            WordTiming(word="trèo", start_time=0.60, end_time=0.90),
            WordTiming(word="cây", start_time=0.90, end_time=1.25),
            WordTiming(word="lấy", start_time=1.30, end_time=1.60),
            WordTiming(word="chuối.", start_time=1.65, end_time=2.30),
        ],
        provider_name="MockTTSProvider",
        is_word_level=True,
    )
    timeline_fast = synchronizer.build_timeline(fast_timing, monkey_banana_scene_graph)

    # Audio dài (7.0 giây)
    slow_timing = NarrationTiming(
        text="Con khỉ đang trèo lên cây để lấy một quả chuối chín mọng.",
        duration=7.0,
        words=[
            WordTiming(word="Con", start_time=0.2, end_time=0.6),
            WordTiming(word="khỉ", start_time=0.6, end_time=1.2),
            WordTiming(word="đang", start_time=1.3, end_time=1.7),
            WordTiming(word="trèo", start_time=1.8, end_time=2.4),
            WordTiming(word="lên", start_time=2.4, end_time=2.8),
            WordTiming(word="cây", start_time=2.8, end_time=3.5),
            WordTiming(word="chuối", start_time=4.5, end_time=5.8),
        ],
        provider_name="MockTTSProvider",
        is_word_level=True,
    )
    timeline_slow = synchronizer.build_timeline(slow_timing, monkey_banana_scene_graph)

    assert timeline_fast.total_duration < timeline_slow.total_duration
    assert abs(timeline_fast.total_duration - 3.0) < 1.0
    assert abs(timeline_slow.total_duration - 7.5) < 1.0


def test_semantic_synchronization_sequence(monkey_banana_scene_graph, mock_narration_timing):
    """
    Kiểm tra thứ tự đồng bộ ngữ nghĩa:
    'Con khỉ...' -> monkey vẽ đầu tiên
    '...trèo lên cây...' -> tree được vẽ
    '...lấy quả chuối.' -> banana xuất hiện cuối cùng
    """
    synchronizer = DrawingTimelineSynchronizer()
    timeline = synchronizer.build_timeline(mock_narration_timing, monkey_banana_scene_graph)

    sched = timeline.entities_schedule
    monkey_win = sched["entity_monkey"]
    tree_win = sched["entity_tree"]
    banana_win = sched["entity_banana"]

    # Monkey bắt đầu từ 0.1s (ứng với từ 'Con khỉ')
    assert monkey_win[0] == pytest.approx(0.1, abs=0.05)
    # Tree bắt đầu khi xuất hiện 'trèo' (1.1s)
    assert tree_win[0] == pytest.approx(1.1, abs=0.1)
    # Banana bắt đầu khi có 'lấy / chuối' (2.45s)
    assert banana_win[0] == pytest.approx(2.45, abs=0.1)

    # Thứ tự thời gian bắt đầu của các entity
    assert monkey_win[0] < tree_win[0] < banana_win[0]


def test_first_frame_empty_assertion(monkey_banana_scene_graph, mock_narration_timing):
    """Visual Assertion 1: First frames không có toàn bộ object xuất hiện ngay."""
    synchronizer = DrawingTimelineSynchronizer()
    timeline = synchronizer.build_timeline(mock_narration_timing, monkey_banana_scene_graph)

    # Tại t = 0.0s (trước khi narration bắt đầu vẽ)
    drawn_at_start = timeline.get_drawn_strokes_at(0.0)
    assert len(drawn_at_start) == 0, "Tại t=0.0s không được có nét vẽ nào xuất hiện trước"

    # Tại t = 0.05s
    drawn_early = timeline.get_drawn_strokes_at(0.05)
    assert len(drawn_early) == 0, "Trước từ 'Con khỉ' chưa có nét vẽ nào xuất hiện"


def test_final_frame_complete_assertion(monkey_banana_scene_graph, mock_narration_timing):
    """Visual Assertion 2: Final frame scene hoàn chỉnh toàn bộ nét vẽ của monkey, tree, banana."""
    synchronizer = DrawingTimelineSynchronizer()
    timeline = synchronizer.build_timeline(mock_narration_timing, monkey_banana_scene_graph)

    all_draw_events = [e for e in timeline.events if e.action == "draw"]
    total_draw_strokes = len(all_draw_events)

    # Tại cuối timeline
    drawn_at_end = timeline.get_drawn_strokes_at(timeline.total_duration)
    assert len(drawn_at_end) == total_draw_strokes

    # Đảm bảo tất cả 3 thực thể đều có mặt đầy đủ ở frame cuối
    drawn_assets = {e.asset_id for e in drawn_at_end}
    assert "monkey" in drawn_assets
    assert "tree" in drawn_assets
    assert "banana" in drawn_assets


def test_hand_tracking_proximity_during_drawing(monkey_banana_scene_graph, mock_narration_timing):
    """
    Visual Assertion 3: Trong suốt quá trình vẽ, hand nib luôn nằm trên nét vẽ đang hoạt động.
    Bàn tay không được tự nhiên biến mất hoặc xuất hiện ngẫu nhiên.
    """
    synchronizer = DrawingTimelineSynchronizer()
    timeline = synchronizer.build_timeline(mock_narration_timing, monkey_banana_scene_graph)

    # Kiểm tra tại thời điểm giữa của 10 nét vẽ ngẫu nhiên
    draw_events = [e for e in timeline.events if e.action == "draw"]
    for ev in draw_events[::5]:
        mid_time = (ev.start_time + ev.end_time) / 2.0
        hand_pos = timeline.get_hand_position_at(mid_time)

        assert hand_pos is not None, f"Phải có vị trí bàn tay tại t={mid_time}"
        assert 0 <= hand_pos[0] <= 1920
        assert 0 <= hand_pos[1] <= 1080

        # Kiểm tra khoảng cách tới ít nhất một điểm trên hand_path của sự kiện
        min_dist = min(
            ((hand_pos[0] - pt[0]) ** 2 + (hand_pos[1] - pt[1]) ** 2) ** 0.5
            for pt in ev.hand_path
        )
        assert min_dist < 5.0, f"Bàn tay phải bám sát nét vẽ (khoảng cách {min_dist} >= 5px)"
