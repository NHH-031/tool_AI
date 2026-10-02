import pytest
from pathlib import Path

from core.assets.resolver import GenericAssetResolver
from core.qa.media_probe import MediaProbe
from core.schemas.scene_graph import (
    Position,
    SceneGraph,
    VisualAction,
    VisualEntity,
    VisualRelationship,
)
from core.schemas.tts import NarrationTiming, WordTiming
from core.timeline.synchronizer import DrawingTimelineSynchronizer
from engines.whiteboard.adapter import WhiteboardEngineAdapter


@pytest.fixture
def asset_resolver() -> GenericAssetResolver:
    return GenericAssetResolver()


@pytest.fixture
def timeline_synchronizer() -> DrawingTimelineSynchronizer:
    return DrawingTimelineSynchronizer()


@pytest.fixture
def engine_adapter() -> WhiteboardEngineAdapter:
    return WhiteboardEngineAdapter()


def test_regression_case_1_dog_ball(timeline_synchronizer, engine_adapter, tmp_path):
    """CASE 1: 'Con chó đang chạy theo quả bóng.' -> dog, ball, running, chasing."""
    sg = SceneGraph(
        scene_id="regression_dog_ball",
        description="Con chó đang chạy theo quả bóng.",
    )
    sg.add_entity(
        VisualEntity(
            id="entity_dog",
            name="dog",
            label="dog",
            visual_role="character",
            action="running",
            priority=1,
            position=Position(x=200, y=500, width=400, height=350),
        )
    )
    sg.add_entity(
        VisualEntity(
            id="entity_ball",
            name="ball",
            label="ball",
            visual_role="target",
            priority=2,
            position=Position(x=1200, y=600, width=200, height=200),
        )
    )
    sg.add_action(
        VisualAction(
            entity_id="entity_dog",
            action_type="running",
            required=True,
        )
    )
    sg.add_relationship(
        VisualRelationship(
            source_id="entity_dog",
            target_id="entity_ball",
            relation_type="chasing",
            description="dog chasing ball",
            required=True,
        )
    )

    timing = NarrationTiming(
        text="Con chó đang chạy theo quả bóng.",
        duration=4.0,
        words=[
            WordTiming(word="Con", start_time=0.1, end_time=0.4),
            WordTiming(word="chó", start_time=0.4, end_time=0.8),
            WordTiming(word="đang", start_time=0.8, end_time=1.1),
            WordTiming(word="chạy", start_time=1.1, end_time=1.5),
            WordTiming(word="theo", start_time=1.5, end_time=1.9),
            WordTiming(word="quả", start_time=1.9, end_time=2.3),
            WordTiming(word="bóng.", start_time=2.3, end_time=3.0),
        ],
    )

    timeline = timeline_synchronizer.build_timeline(timing, sg)
    assert len(timeline.events) >= 2

    # Verify generic asset resolution and completeness
    for entity in sg.entities:
        assert entity.asset_resolved is True
        assert entity.stroke_count > 0
        assert entity.completed_stroke_count == entity.stroke_count
        assert entity.completion_ratio == 1.0

    # Test artifact preparation
    img_path, ann_path = engine_adapter.prepare_scene_artifacts(sg, timeline, tmp_path)
    assert Path(img_path).exists()
    assert Path(ann_path).exists()

    # QA Verification
    report = MediaProbe.inspect_media(
        output_path="test_mock.mp4",
        expected_duration_sec=timing.duration,
        scene_graph=sg,
        timeline=timeline,
        run_ffprobe=False,
    )
    assert report.drawing_qa.pass_drawing is True
    assert report.drawing_qa.completion_ratio == 1.0
    assert report.semantic_qa.pass_semantic is True
    assert report.semantic_qa.required_entities == 2
    assert report.semantic_qa.completed_entities == 2


def test_regression_case_2_earth_sun(timeline_synchronizer, engine_adapter, tmp_path):
    """CASE 2: 'Trái Đất quay quanh Mặt Trời.' -> earth, sun, orbit."""
    sg = SceneGraph(
        scene_id="regression_earth_sun",
        description="Trái Đất quay quanh Mặt Trời.",
    )
    sg.add_entity(
        VisualEntity(
            id="entity_sun",
            name="sun",
            label="sun",
            visual_role="background",
            priority=1,
            position=Position(x=800, y=340, width=400, height=400),
        )
    )
    sg.add_entity(
        VisualEntity(
            id="entity_orbit",
            name="orbit",
            label="orbit",
            visual_role="relation_link",
            priority=2,
            position=Position(x=400, y=200, width=1100, height=680),
        )
    )
    sg.add_entity(
        VisualEntity(
            id="entity_earth",
            name="earth",
            label="earth",
            visual_role="character",
            action="orbiting",
            priority=3,
            position=Position(x=450, y=450, width=240, height=240),
        )
    )
    sg.add_action(
        VisualAction(
            entity_id="entity_earth",
            action_type="orbiting",
            required=True,
        )
    )
    sg.add_relationship(
        VisualRelationship(
            source_id="entity_earth",
            target_id="entity_sun",
            relation_type="orbiting",
            description="earth orbiting sun",
            required=True,
        )
    )

    timing = NarrationTiming(
        text="Trái Đất quay quanh Mặt Trời.",
        duration=4.0,
        words=[
            WordTiming(word="Trái", start_time=0.1, end_time=0.4),
            WordTiming(word="Đất", start_time=0.4, end_time=0.8),
            WordTiming(word="quay", start_time=0.8, end_time=1.3),
            WordTiming(word="quanh", start_time=1.3, end_time=1.8),
            WordTiming(word="Mặt", start_time=1.8, end_time=2.2),
            WordTiming(word="Trời.", start_time=2.2, end_time=2.8),
        ],
    )

    timeline = timeline_synchronizer.build_timeline(timing, sg)
    for entity in sg.entities:
        assert entity.asset_resolved is True
        assert entity.completion_ratio == 1.0

    img_path, ann_path = engine_adapter.prepare_scene_artifacts(sg, timeline, tmp_path)
    assert Path(img_path).exists()

    report = MediaProbe.inspect_media(
        output_path="test_mock.mp4",
        expected_duration_sec=timing.duration,
        scene_graph=sg,
        timeline=timeline,
        run_ffprobe=False,
    )
    assert report.drawing_qa.pass_drawing is True
    assert report.semantic_qa.pass_semantic is True


def test_regression_case_3_water_evaporation(timeline_synchronizer, engine_adapter, tmp_path):
    """CASE 3: 'Nước nóng bốc hơi.' -> water, heat, vapor, upward movement."""
    sg = SceneGraph(
        scene_id="regression_water_evaporation",
        description="Nước nóng bốc hơi.",
    )
    sg.add_entity(
        VisualEntity(
            id="entity_water",
            name="water",
            label="water",
            visual_role="subject",
            priority=1,
            position=Position(x=600, y=600, width=700, height=350),
        )
    )
    sg.add_entity(
        VisualEntity(
            id="entity_vapor",
            name="vapor",
            label="vapor",
            visual_role="action_indicator",
            action="upward_motion",
            priority=2,
            position=Position(x=700, y=200, width=500, height=400),
        )
    )
    sg.add_action(
        VisualAction(
            entity_id="entity_vapor",
            action_type="upward_motion",
            required=True,
        )
    )
    sg.add_relationship(
        VisualRelationship(
            source_id="entity_water",
            target_id="entity_vapor",
            relation_type="evaporating",
            description="water turns into rising vapor",
            required=True,
        )
    )

    timing = NarrationTiming(
        text="Nước nóng bốc hơi.",
        duration=3.5,
        words=[
            WordTiming(word="Nước", start_time=0.1, end_time=0.5),
            WordTiming(word="nóng", start_time=0.5, end_time=1.0),
            WordTiming(word="bốc", start_time=1.0, end_time=1.6),
            WordTiming(word="hơi.", start_time=1.6, end_time=2.3),
        ],
    )

    timeline = timeline_synchronizer.build_timeline(timing, sg)
    for entity in sg.entities:
        assert entity.asset_resolved is True
        assert entity.completion_ratio == 1.0

    img_path, ann_path = engine_adapter.prepare_scene_artifacts(sg, timeline, tmp_path)
    assert Path(img_path).exists()

    report = MediaProbe.inspect_media(
        output_path="test_mock.mp4",
        expected_duration_sec=timing.duration,
        scene_graph=sg,
        timeline=timeline,
        run_ffprobe=False,
    )
    assert report.drawing_qa.pass_drawing is True
    assert report.semantic_qa.pass_semantic is True


def test_regression_case_4_farmer_tree(timeline_synchronizer, engine_adapter, tmp_path):
    """CASE 4: 'Người nông dân đang trồng một cái cây.' -> farmer, ground, tree, planting."""
    sg = SceneGraph(
        scene_id="regression_farmer_tree",
        description="Người nông dân đang trồng một cái cây.",
    )
    sg.add_entity(
        VisualEntity(
            id="entity_ground",
            name="ground",
            label="ground",
            visual_role="environment",
            priority=1,
            position=Position(x=200, y=750, width=1500, height=200),
        )
    )
    sg.add_entity(
        VisualEntity(
            id="entity_farmer",
            name="farmer",
            label="farmer",
            visual_role="character",
            action="planting",
            priority=2,
            position=Position(x=450, y=350, width=500, height=500),
        )
    )
    sg.add_entity(
        VisualEntity(
            id="entity_tree",
            name="tree",
            label="tree",
            visual_role="target",
            priority=3,
            position=Position(x=1050, y=250, width=600, height=650),
        )
    )
    sg.add_action(
        VisualAction(
            entity_id="entity_farmer",
            action_type="planting",
            required=True,
        )
    )
    sg.add_relationship(
        VisualRelationship(
            source_id="entity_farmer",
            target_id="entity_tree",
            relation_type="planting",
            description="farmer planting tree into ground",
            required=True,
        )
    )

    timing = NarrationTiming(
        text="Người nông dân đang trồng một cái cây.",
        duration=4.5,
        words=[
            WordTiming(word="Người", start_time=0.1, end_time=0.4),
            WordTiming(word="nông", start_time=0.4, end_time=0.7),
            WordTiming(word="dân", start_time=0.7, end_time=1.0),
            WordTiming(word="đang", start_time=1.0, end_time=1.4),
            WordTiming(word="trồng", start_time=1.4, end_time=1.9),
            WordTiming(word="một", start_time=1.9, end_time=2.2),
            WordTiming(word="cái", start_time=2.2, end_time=2.5),
            WordTiming(word="cây.", start_time=2.5, end_time=3.2),
        ],
    )

    timeline = timeline_synchronizer.build_timeline(timing, sg)
    for entity in sg.entities:
        assert entity.asset_resolved is True
        assert entity.completion_ratio == 1.0

    img_path, ann_path = engine_adapter.prepare_scene_artifacts(sg, timeline, tmp_path)
    assert Path(img_path).exists()

    report = MediaProbe.inspect_media(
        output_path="test_mock.mp4",
        expected_duration_sec=timing.duration,
        scene_graph=sg,
        timeline=timeline,
        run_ffprobe=False,
    )
    assert report.drawing_qa.pass_drawing is True
    assert report.semantic_qa.pass_semantic is True


def test_regression_case_5_inflation_price(timeline_synchronizer, engine_adapter, tmp_path):
    """CASE 5: 'Giá cả tăng khi lạm phát tăng.' -> price, inflation, upward trend, relationship."""
    sg = SceneGraph(
        scene_id="regression_inflation_price",
        description="Giá cả tăng khi lạm phát tăng.",
    )
    sg.add_entity(
        VisualEntity(
            id="entity_price_chart",
            name="price_chart",
            label="price",
            visual_role="subject",
            priority=1,
            position=Position(x=350, y=250, width=700, height=600),
        )
    )
    sg.add_entity(
        VisualEntity(
            id="entity_upward_trend",
            name="upward_trend",
            label="inflation",
            visual_role="action_indicator",
            action="rising",
            priority=2,
            position=Position(x=1050, y=200, width=500, height=650),
        )
    )
    sg.add_action(
        VisualAction(
            entity_id="entity_upward_trend",
            action_type="rising",
            required=True,
        )
    )
    sg.add_relationship(
        VisualRelationship(
            source_id="entity_upward_trend",
            target_id="entity_price_chart",
            relation_type="correlated_with",
            description="inflation drives price chart upward",
            required=True,
        )
    )

    timing = NarrationTiming(
        text="Giá cả tăng khi lạm phát tăng.",
        duration=4.0,
        words=[
            WordTiming(word="Giá", start_time=0.1, end_time=0.4),
            WordTiming(word="cả", start_time=0.4, end_time=0.7),
            WordTiming(word="tăng", start_time=0.7, end_time=1.2),
            WordTiming(word="khi", start_time=1.2, end_time=1.6),
            WordTiming(word="lạm", start_time=1.6, end_time=1.9),
            WordTiming(word="phát", start_time=1.9, end_time=2.3),
            WordTiming(word="tăng.", start_time=2.3, end_time=3.0),
        ],
    )

    timeline = timeline_synchronizer.build_timeline(timing, sg)
    for entity in sg.entities:
        assert entity.asset_resolved is True
        assert entity.completion_ratio == 1.0

    img_path, ann_path = engine_adapter.prepare_scene_artifacts(sg, timeline, tmp_path)
    assert Path(img_path).exists()

    report = MediaProbe.inspect_media(
        output_path="test_mock.mp4",
        expected_duration_sec=timing.duration,
        scene_graph=sg,
        timeline=timeline,
        run_ffprobe=False,
    )
    assert report.drawing_qa.pass_drawing is True
    assert report.semantic_qa.pass_semantic is True


def test_regression_case_6_monkey_tree_banana(timeline_synchronizer, engine_adapter, tmp_path):
    """CASE 6: 'Con khỉ đang trèo lên cây để lấy một quả chuối.' -> monkey, tree, banana, climbing, reaching, located_on."""
    sg = SceneGraph(
        scene_id="regression_monkey_tree_banana",
        description="Con khỉ đang trèo lên cây để lấy một quả chuối.",
    )
    sg.add_entity(
        VisualEntity(
            id="entity_tree",
            name="tree",
            label="tree",
            visual_role="environment",
            priority=1,
            position=Position(x=820, y=80, width=720, height=880),
        )
    )
    sg.add_entity(
        VisualEntity(
            id="entity_monkey",
            name="monkey",
            label="monkey",
            visual_role="character",
            action="climbing",
            priority=2,
            position=Position(x=720, y=400, width=440, height=440),
        )
    )
    sg.add_entity(
        VisualEntity(
            id="entity_banana",
            name="banana",
            label="banana",
            visual_role="target",
            action="reached",
            priority=3,
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
            description="monkey climbing tree",
            required=True,
        )
    )
    sg.add_relationship(
        VisualRelationship(
            source_id="entity_monkey",
            target_id="entity_banana",
            relation_type="reaching_for",
            description="monkey reaching banana",
            required=True,
        )
    )
    sg.add_relationship(
        VisualRelationship(
            source_id="entity_banana",
            target_id="entity_tree",
            relation_type="located_on",
            description="banana located on tree",
            required=True,
        )
    )

    timing = NarrationTiming(
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
    )

    timeline = timeline_synchronizer.build_timeline(timing, sg)
    assert len(timeline.events) >= 3

    for entity in sg.entities:
        assert entity.asset_resolved is True
        assert entity.stroke_count > 0
        assert entity.completed_stroke_count == entity.stroke_count
        assert entity.completion_ratio == 1.0

    img_path, ann_path = engine_adapter.prepare_scene_artifacts(sg, timeline, tmp_path)
    assert Path(img_path).exists()
    assert Path(ann_path).exists()

    report = MediaProbe.inspect_media(
        output_path="test_mock.mp4",
        expected_duration_sec=timing.duration,
        scene_graph=sg,
        timeline=timeline,
        run_ffprobe=False,
    )
    assert report.drawing_qa.pass_drawing is True
    assert report.drawing_qa.completion_ratio == 1.0
    assert report.semantic_qa.pass_semantic is True
    assert report.semantic_qa.required_entities == 3
    assert report.semantic_qa.completed_entities == 3
    assert report.semantic_qa.required_actions == 2
    assert report.semantic_qa.completed_actions == 2
    assert report.semantic_qa.required_relationships == 3
    assert report.semantic_qa.completed_relationships == 3
    assert report.semantic_qa.final_frame_complete is True
    assert report.overall_pass is True
