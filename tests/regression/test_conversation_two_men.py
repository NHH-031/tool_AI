from pathlib import Path
import pytest

from core.artwork.prompt_builder import IllustrationPromptBuilder
from core.pipeline.semantic_planner import SemanticVisualPlanner
from core.schemas.scene_graph import SceneGraph
from core.schemas.timeline import DrawingTimeline
from core.schemas.tts import NarrationTiming, WordTiming
from core.timeline.synchronizer import DrawingTimelineSynchronizer
from core.validation.semantic import SemanticValidator
from engines.whiteboard.adapter import WhiteboardEngineAdapter


def test_two_men_talking_semantic_understanding():
    """
    Kiểm tra AI hiểu chính xác kịch bản hai người đàn ông nói chuyện:
    1. Trích xuất đúng thực thể 'man', không bị nhầm lẫn thành 'fighter'.
    2. Nhận diện hành động và mối quan hệ hội thoại 'talking'.
    3. Tạo đủ 2 thực thể nhân vật nam đứng đối diện nhau trên SceneGraph.
    """
    script = "hai người đàn ông nói chuyện với nhau"

    # 1. Semantic Validator Entity & Relationship Extraction
    entities = SemanticValidator.extract_required_entities(script)
    assert "man" in entities, f"FAIL: Phải trích xuất 'man', nhưng lại nhận được: {entities}"
    assert "fighter" not in entities, f"FAIL: Không được nhầm hai người đàn ông nói chuyện thành võ sĩ fighter! {entities}"

    rels = SemanticValidator.extract_required_relationships(script, entities)
    assert any(r[1] in ["talking", "talking_with"] for r in rels), f"FAIL: Phải có quan hệ talking, nhưng nhận được: {rels}"

    # 2. Dynamic Semantic Planning
    plan = SemanticVisualPlanner.plan_from_script(script)
    assert len(plan.scenes) >= 1
    sg: SceneGraph = plan.scenes[0].scene_graph

    # Phải có đủ 2 thực thể đàn ông
    assert len(sg.entities) >= 2, f"FAIL: Phải có ít nhất 2 thực thể, nhưng chỉ có {len(sg.entities)}: {[e.id for e in sg.entities]}"
    man_ids = [e.id for e in sg.entities if "man" in e.id or e.label == "man"]
    assert len(man_ids) >= 2, f"FAIL: Phải có 2 thực thể man, nhận được: {man_ids}"

    man1 = next(e for e in sg.entities if e.id == "man_1")
    man2 = next(e for e in sg.entities if e.id == "man_2")

    # Kiểm tra vị trí đứng đối diện nhau
    assert man1.position.x < man2.position.x, "FAIL: Người đàn ông 1 phải đứng bên trái người đàn ông 2"
    assert man1.position.x <= 500, "FAIL: Người đàn ông 1 phải ở khu vực bên trái canvas"
    assert man2.position.x >= 1000, "FAIL: Người đàn ông 2 phải ở khu vực bên phải canvas"

    # Kiểm tra hành động nói chuyện
    assert "talking" in man1.actions, "FAIL: Người đàn ông 1 phải có hành động talking"
    assert "talking" in man2.actions, "FAIL: Người đàn ông 2 phải có hành động talking"

    # Kiểm tra mối quan hệ giao tiếp
    talk_rels = [
        r for r in sg.relationships
        if r.relation_type in ["talking", "talking_with"]
    ]
    assert len(talk_rels) >= 1, "FAIL: Phải có relationship talking_with giữa hai người đàn ông"

    # 3. Prompt Builder Structure
    prompt_obj = IllustrationPromptBuilder.build_from_scene_graph(sg)
    assert "Two adult men" in prompt_obj.subject or "Two" in prompt_obj.subject, (
        f"FAIL: Subject prompt phải thể hiện rõ 2 người đàn ông: '{prompt_obj.subject}'"
    )
    assert prompt_obj.scene_context == script, (
        f"FAIL: Scene context phải lưu giữ trọn vẹn kịch bản gốc của người dùng: '{prompt_obj.scene_context}'"
    )
