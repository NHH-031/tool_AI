from core.schemas.annotation import CanvasSchema
from core.schemas.scene_graph import (
    Position,
    SceneGraph,
    VisualEntity,
    VisualRelationship,
)
from core.validation.semantic import SemanticValidator


def test_semantic_detects_missing_tree():
    """
    Kịch bản: Narration là 'Con khỉ trèo lên cây.'
    Visual plan chỉ có: monkey, car, banana.
    Bộ thẩm định BẮT BUỘC phải phát hiện: 'tree missing'.
    """
    narration = "Con khỉ trèo lên cây."
    graph = SceneGraph(
        entities=[
            VisualEntity(id="monkey", label="monkey", position=Position(x=10, y=10, width=50, height=50)),
            VisualEntity(id="car", label="car", position=Position(x=100, y=100, width=50, height=50)),
            VisualEntity(id="banana", label="banana", position=Position(x=200, y=200, width=50, height=50)),
        ],
        relationships=[],
    )

    res = SemanticValidator.validate_narration_against_graph(narration, graph)
    assert res.is_valid is False
    assert "tree" in res.missing_entities
    assert any("Missing entity: 'tree'" in err for err in res.errors)


def test_semantic_detects_missing_climbing_relationship():
    """
    Kịch bản: Narration là 'Con khỉ trèo lên cây.'
    Visual plan có cả monkey và tree, nhưng KHÔNG có relationship 'climbing'.
    Bộ thẩm định BẮT BUỘC phải phát hiện lỗi thiếu quan hệ.
    """
    narration = "Con khỉ trèo lên cây."
    graph = SceneGraph(
        entities=[
            VisualEntity(id="monkey", label="monkey", position=Position(x=10, y=10, width=50, height=50)),
            VisualEntity(id="tree", label="tree", position=Position(x=100, y=100, width=50, height=50)),
        ],
        relationships=[],  # Thiếu relationship climbing
    )

    res = SemanticValidator.validate_narration_against_graph(narration, graph)
    assert res.is_valid is False
    assert len(res.missing_relationships) > 0
    assert any("monkey -> climbing -> tree" in rel for rel in res.missing_relationships)


def test_semantic_passes_when_all_entities_and_actions_match():
    """
    Kịch bản: Đầy đủ monkey, tree, banana và quan hệ climbing, reaching, located_on.
    """
    narration = "Con khỉ trèo lên cây và với quả chuối trên cây."
    graph = SceneGraph(
        entities=[
            VisualEntity(id="monkey", label="monkey", position=Position(x=10, y=10, width=50, height=50)),
            VisualEntity(id="tree", label="tree", position=Position(x=100, y=100, width=50, height=50)),
            VisualEntity(id="banana", label="banana", position=Position(x=200, y=200, width=50, height=50)),
        ],
        relationships=[
            VisualRelationship(id="r1", source_id="monkey", target_id="tree", relation_type="climbing"),
            VisualRelationship(id="r2", source_id="monkey", target_id="banana", relation_type="reaching"),
            VisualRelationship(id="r3", source_id="banana", target_id="tree", relation_type="located_on"),
        ],
    )

    res = SemanticValidator.validate_narration_against_graph(narration, graph)
    assert res.is_valid is True
    assert len(res.missing_entities) == 0
    assert len(res.missing_relationships) == 0
    assert len(res.errors) == 0
