import pytest

from core.qa.media_probe import MediaProbe
from core.schemas.scene_graph import (
    Position,
    SceneGraph,
    VisualAction,
    VisualEntity,
    VisualRelationship,
)
from core.schemas.timeline import DrawingTimeline, DrawingTimelineEvent


@pytest.fixture
def base_scene_graph() -> SceneGraph:
    sg = SceneGraph(
        scene_id="test_injection_scene",
        description="Scene for failure injection tests",
    )
    sg.add_entity(
        VisualEntity(
            id="entity_tree",
            name="tree",
            label="tree",
            required=True,
            stroke_count=41,
            completed_stroke_count=41,
            completion_ratio=1.0,
            required_stroke_ids=[f"tree_{i}" for i in range(41)],
            completed_stroke_ids=[f"tree_{i}" for i in range(41)],
            position=Position(x=820, y=80, width=720, height=880),
        )
    )
    sg.add_entity(
        VisualEntity(
            id="entity_monkey",
            name="monkey",
            label="monkey",
            required=True,
            action="climbing",
            stroke_count=20,
            completed_stroke_count=20,
            completion_ratio=1.0,
            required_stroke_ids=[f"monkey_{i}" for i in range(20)],
            completed_stroke_ids=[f"monkey_{i}" for i in range(20)],
            position=Position(x=720, y=400, width=440, height=440),
        )
    )
    sg.add_entity(
        VisualEntity(
            id="entity_banana",
            name="banana",
            label="banana",
            required=True,
            stroke_count=6,
            completed_stroke_count=6,
            completion_ratio=1.0,
            required_stroke_ids=[f"banana_{i}" for i in range(6)],
            completed_stroke_ids=[f"banana_{i}" for i in range(6)],
            position=Position(x=1120, y=180, width=240, height=240),
        )
    )
    sg.add_action(
        VisualAction(
            entity_id="entity_monkey",
            action_type="climbing",
            required=True,
        )
    )
    sg.add_action(
        VisualAction(
            entity_id="entity_monkey",
            action_type="reaching_for",
            required=True,
        )
    )
    sg.add_relationship(
        VisualRelationship(
            source_id="entity_monkey",
            target_id="entity_tree",
            relation_type="climbing",
            required=True,
        )
    )
    sg.add_relationship(
        VisualRelationship(
            source_id="entity_monkey",
            target_id="entity_banana",
            relation_type="reaching_for",
            required=True,
        )
    )
    return sg


@pytest.fixture
def base_timeline() -> DrawingTimeline:
    return DrawingTimeline(
        total_duration=5.0,
        events=[
            DrawingTimelineEvent(
                stroke_id="tree_0",
                asset_id="asset_tree",
                entity_id="entity_tree",
                action="draw",
                start_time=0.1,
                end_time=1.8,
                hand_path=[(820.0, 80.0), (900.0, 500.0)],
                semantic_purpose="trunk",
            ),
            DrawingTimelineEvent(
                stroke_id="monkey_0",
                asset_id="asset_monkey",
                entity_id="entity_monkey",
                action="draw",
                start_time=1.8,
                end_time=3.5,
                hand_path=[(720.0, 400.0), (800.0, 600.0)],
                semantic_purpose="body",
            ),
            DrawingTimelineEvent(
                stroke_id="banana_0",
                asset_id="asset_banana",
                entity_id="entity_banana",
                action="draw",
                start_time=3.5,
                end_time=4.5,
                hand_path=[(1120.0, 180.0), (1200.0, 240.0)],
                semantic_purpose="banana_body",
            ),
        ],
    )


def test_failure_injection_missing_entity(base_scene_graph, base_timeline):
    """Failure Injection: Banana entity is missing from timeline events -> Semantic QA FAIL."""
    # Remove banana event from timeline
    base_timeline.events = [
        e for e in base_timeline.events
        if "banana" not in e.stroke_id and "banana" not in e.asset_id and e.entity_id != "entity_banana"
    ]
    # Mark banana as uncompleted
    banana = next(e for e in base_scene_graph.entities if e.id == "entity_banana")
    banana.completed_stroke_count = 0
    banana.completion_ratio = 0.0

    report = MediaProbe.inspect_media(
        output_path="test_mock.mp4",
        expected_duration_sec=5.0,
        scene_graph=base_scene_graph,
        timeline=base_timeline,
        run_ffprobe=False,
    )

    assert report.semantic_qa.pass_semantic is False
    assert report.semantic_qa.completed_entities < report.semantic_qa.required_entities
    assert report.overall_pass is False
    assert any("banana" in err.lower() for err in report.semantic_qa.errors)


def test_failure_injection_incomplete_stroke(base_scene_graph, base_timeline):
    """Failure Injection: Monkey entity only has 10/20 strokes completed -> Drawing QA FAIL."""
    monkey = next(e for e in base_scene_graph.entities if e.id == "entity_monkey")
    monkey.completed_stroke_count = 10
    monkey.completion_ratio = 0.5
    monkey.completed_stroke_ids = monkey.required_stroke_ids[:10]

    report = MediaProbe.inspect_media(
        output_path="test_mock.mp4",
        expected_duration_sec=5.0,
        scene_graph=base_scene_graph,
        timeline=base_timeline,
        run_ffprobe=False,
    )

    assert report.drawing_qa.pass_drawing is False
    assert report.drawing_qa.completion_ratio < 1.0
    assert report.overall_pass is False
    assert any("monkey" in err.lower() or "ratio" in err.lower() for err in report.drawing_qa.errors)


def test_failure_injection_wrong_hand_path(base_scene_graph, base_timeline):
    """Failure Injection: Hand path is empty or degenerate -> Drawing QA FAIL."""
    # Empty hand path for tree event
    base_timeline.events[0].hand_path = []

    report = MediaProbe.inspect_media(
        output_path="test_mock.mp4",
        expected_duration_sec=5.0,
        scene_graph=base_scene_graph,
        timeline=base_timeline,
        run_ffprobe=False,
    )

    assert report.drawing_qa.pass_drawing is False
    assert report.drawing_qa.hand_path_valid is False
    assert report.overall_pass is False
    assert any("hand_path" in err.lower() for err in report.drawing_qa.errors)


def test_failure_injection_technically_valid_but_banana_missing(base_scene_graph, base_timeline):
    """Failure Injection: MP4 is technically 100% valid, but banana is missing -> Overall MUST BE FAIL."""
    # Remove banana from events
    base_timeline.events = [
        e for e in base_timeline.events
        if "banana" not in e.stroke_id and "banana" not in e.asset_id and e.entity_id != "entity_banana"
    ]
    banana = next(e for e in base_scene_graph.entities if e.id == "entity_banana")
    banana.completion_ratio = 0.0

    report = MediaProbe.inspect_media(
        output_path="test_mock.mp4",
        expected_duration_sec=5.0,
        scene_graph=base_scene_graph,
        timeline=base_timeline,
        run_ffprobe=False,
    )

    # Technical QA passes
    assert report.technical_qa.pass_technical is True
    # But Drawing & Semantic QA FAIL
    assert report.drawing_qa.pass_drawing is False or report.semantic_qa.pass_semantic is False
    # Overall MUST be FAIL
    assert report.overall_pass is False
