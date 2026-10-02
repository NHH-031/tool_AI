from core.validation.semantic import SemanticValidator
from core.validation.structural import StructuralValidator
from tests.fixtures.monkey_banana_loader import (
    load_monkey_banana_project,
    load_monkey_banana_scene,
)


def test_monkey_banana_regression_fixture():
    # 1. Tải fixture
    scene = load_monkey_banana_scene()
    project = load_monkey_banana_project()

    # 2. Kiểm tra template text_required = false
    assert project.template.text_required is False

    # 3. Kiểm tra các thực thể mong đợi
    entity_ids = {e.id for e in scene.scene_graph.entities}
    assert "monkey" in entity_ids
    assert "tree" in entity_ids
    assert "banana" in entity_ids

    # 4. Kiểm tra các mối quan hệ mong đợi
    relationships = {
        (r.source_id, r.relation_type, r.target_id)
        for r in scene.scene_graph.relationships
    }
    assert ("monkey", "climbing", "tree") in relationships
    assert ("monkey", "reaching", "banana") in relationships
    assert ("banana", "located_on", "tree") in relationships

    # 5. Kiểm tra tính hợp lệ về cấu trúc (Structural Validation)
    struct_res = StructuralValidator.validate_scene(scene)
    assert struct_res.is_valid is True, f"Lỗi cấu trúc: {struct_res.errors}"
    assert len(struct_res.errors) == 0

    # 6. Kiểm tra tính hợp lệ về ngữ nghĩa (Semantic Validation)
    semantic_res = SemanticValidator.validate_scene(scene)
    assert semantic_res.is_valid is True, f"Lỗi ngữ nghĩa: {semantic_res.errors}"
    assert len(semantic_res.missing_entities) == 0
    assert len(semantic_res.missing_relationships) == 0
    assert len(semantic_res.errors) == 0
