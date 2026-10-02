import pytest
from core.schemas.annotation import CanvasSchema
from core.schemas.project import Asset, Scene
from core.schemas.scene_graph import (
    Position,
    SceneGraph,
    VisualEntity,
    VisualRelationship,
)
from core.schemas.timeline import TimelineEvent
from core.validation.structural import StructuralValidator


def test_invalid_coordinates_exceeding_canvas():
    canvas = CanvasSchema(width=1920, height=1080)
    # Tọa độ x(1800) + width(200) = 2000 > 1920
    entity = VisualEntity(
        id="e1",
        label="out_of_bounds",
        position=Position(x=1800, y=100, width=200, height=100),
    )
    errors = StructuralValidator.validate_entity_coordinates(entity, canvas)
    assert len(errors) > 0
    assert any("vượt quá chiều rộng canvas" in err for err in errors)


def test_negative_coordinates():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        Position(x=-10, y=50, width=100, height=100)


def test_duplicate_entity_id():
    canvas = CanvasSchema(width=1920, height=1080)
    graph = SceneGraph(
        entities=[
            VisualEntity(id="dup", label="e1", position=Position(x=10, y=10, width=50, height=50)),
            VisualEntity(id="dup", label="e2", position=Position(x=100, y=100, width=50, height=50)),
        ]
    )
    errors = StructuralValidator.validate_scene_graph(graph, canvas)
    assert len(errors) > 0
    assert any("Trùng lặp Entity ID 'dup'" in err for err in errors)


def test_broken_relationship_reference():
    canvas = CanvasSchema(width=1920, height=1080)
    graph = SceneGraph(
        entities=[
            VisualEntity(id="monkey", label="monkey", position=Position(x=10, y=10, width=50, height=50))
        ],
        relationships=[
            VisualRelationship(
                id="r1",
                source_id="monkey",
                target_id="non_existent_target",
                relation_type="climbing",
            )
        ],
    )
    errors = StructuralValidator.validate_scene_graph(graph, canvas)
    assert len(errors) > 0
    assert any("target_id không tồn tại" in err for err in errors)


def test_broken_asset_reference():
    scene = Scene(
        id="s1",
        scene_index=1,
        title="Scene 1",
        canvas=CanvasSchema(width=1920, height=1080),
        duration_ms=5000,
        scene_graph=SceneGraph(
            entities=[
                VisualEntity(
                    id="monkey",
                    label="monkey",
                    position=Position(x=10, y=10, width=50, height=50),
                    asset_id="missing_asset_123",
                )
            ]
        ),
    )
    # Dự án chỉ có asset "existing_asset"
    existing_assets = [
        Asset(id="existing_asset", name="test.png", asset_type="image", file_path_or_uri="/tmp/test.png")
    ]
    res = StructuralValidator.validate_scene(scene, project_assets=existing_assets)
    assert res.is_valid is False
    assert any("tham chiếu asset_id không tồn tại" in err for err in res.errors)


def test_inverted_timeline_events():
    scene = Scene(
        id="s1",
        scene_index=1,
        title="Scene 1",
        canvas=CanvasSchema(width=1920, height=1080),
        duration_ms=5000,
        timeline_events=[
            TimelineEvent(
                id="evt1",
                event_type="drawing",
                start_ms=3000,
                end_ms=1000,  # Lỗi: end < start
                duration_ms=0,
            )
        ],
    )
    res = StructuralValidator.validate_scene(scene)
    assert res.is_valid is False
    assert any("nhỏ hơn start_ms" in err for err in res.errors)
