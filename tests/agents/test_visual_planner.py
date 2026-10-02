import copy
import pytest
from core.providers.mock import MockLLMProvider
from core.schemas.scene_graph import Position, SceneGraph, VisualEntity, VisualRelationship
from core.schemas.script import ScriptSegment
from core.schemas.visual_plan import SceneVisualPlan, VisualPlanOutput
from agents.visual_planner.agent import VisualPlannerAgent
from tests.fixtures.test_cases_data import (
    get_case_1_dog_ball,
    get_case_2_teacher_math,
    get_case_3_temperature_molecules,
    get_case_4_inflation,
    get_case_5_monkey_tree_banana,
)


@pytest.mark.asyncio
async def test_case_1_dog_running_after_ball():
    """Case 1: Dog running after ball."""
    data = get_case_1_dog_ball()
    llm = MockLLMProvider(structured_responses=[data["visual_plan"]])
    agent = VisualPlannerAgent(llm=llm)

    result = await agent.plan_visuals(
        script=data["script_text"],
        segments=data["segments"],
    )

    assert result.success is True
    plan_dict = result.data["visual_plan"]
    entities = plan_dict["scenes"][0]["scene_graph"]["entities"]
    relationships = plan_dict["scenes"][0]["scene_graph"]["relationships"]

    # Kiểm tra entity và relationship
    entity_labels = [e["label"] for e in entities]
    assert "dog" in entity_labels
    assert "ball" in entity_labels
    assert any(r["relation_type"] == "chasing" for r in relationships)

    # Show Don't Write: Visual type không được là text
    for e in entities:
        assert e["visual_type"] != "text"
        assert e["category"] != "text"


@pytest.mark.asyncio
async def test_case_2_teacher_explaining_mathematics():
    """Case 2: Teacher explaining mathematics."""
    data = get_case_2_teacher_math()
    llm = MockLLMProvider(structured_responses=[data["visual_plan"]])
    agent = VisualPlannerAgent(llm=llm)

    result = await agent.plan_visuals(
        script=data["script_text"],
        segments=data["segments"],
    )

    assert result.success is True
    plan_dict = result.data["visual_plan"]
    entities = plan_dict["scenes"][0]["scene_graph"]["entities"]
    relationships = plan_dict["scenes"][0]["scene_graph"]["relationships"]

    entity_labels = [e["label"] for e in entities]
    assert "teacher" in entity_labels
    assert "mathematics" in entity_labels
    assert any(r["relation_type"] == "explaining" for r in relationships)


@pytest.mark.asyncio
async def test_case_3_temperature_molecules():
    """Case 3: Temperature makes molecules move faster (Diagram / Metaphor)."""
    data = get_case_3_temperature_molecules()
    llm = MockLLMProvider(structured_responses=[data["visual_plan"]])
    agent = VisualPlannerAgent(llm=llm)

    result = await agent.plan_visuals(
        script=data["script_text"],
        segments=data["segments"],
    )

    assert result.success is True
    plan_dict = result.data["visual_plan"]
    entities = plan_dict["scenes"][0]["scene_graph"]["entities"]
    relationships = plan_dict["scenes"][0]["scene_graph"]["relationships"]

    entity_labels = [e["label"] for e in entities]
    assert "temperature" in entity_labels
    assert "molecules" in entity_labels
    assert any(r["relation_type"] == "accelerating" for r in relationships)


@pytest.mark.asyncio
async def test_case_4_inflation_metaphor():
    """Case 4: Inflation (Abstract Metaphor / Diagram)."""
    data = get_case_4_inflation()
    llm = MockLLMProvider(structured_responses=[data["visual_plan"]])
    agent = VisualPlannerAgent(llm=llm)

    result = await agent.plan_visuals(
        script=data["script_text"],
        segments=data["segments"],
    )

    assert result.success is True
    plan_dict = result.data["visual_plan"]
    entities = plan_dict["scenes"][0]["scene_graph"]["entities"]
    relationships = plan_dict["scenes"][0]["scene_graph"]["relationships"]

    entity_labels = [e["label"] for e in entities]
    assert "inflation" in entity_labels
    assert "money" in entity_labels
    assert any(r["relation_type"] == "eroding" for r in relationships)


@pytest.mark.asyncio
async def test_case_5_monkey_climbing_tree_for_banana():
    """Case 5: Monkey climbing tree for banana (Show Don't Write standard test)."""
    data = get_case_5_monkey_tree_banana()
    llm = MockLLMProvider(structured_responses=[data["visual_plan"]])
    agent = VisualPlannerAgent(llm=llm)

    result = await agent.plan_visuals(
        script=data["script_text"],
        segments=data["segments"],
    )

    assert result.success is True
    plan_dict = result.data["visual_plan"]
    entities = plan_dict["scenes"][0]["scene_graph"]["entities"]
    relationships = plan_dict["scenes"][0]["scene_graph"]["relationships"]

    labels = {e["label"]: e for e in entities}
    assert "monkey" in labels
    assert "tree" in labels
    assert "banana" in labels

    # Xác minh cả 3 quan hệ mấu chốt
    rel_types = {r["relation_type"] for r in relationships}
    assert "climbing" in rel_types
    assert "reaching" in rel_types
    assert "located_on" in rel_types

    # Xác minh không được dùng text cho bất kỳ phần tử chính nào
    for e in entities:
        assert e["visual_type"] != "text"
        assert e["category"] != "text"


@pytest.mark.asyncio
async def test_show_dont_write_rejection_and_repair():
    """
    Kiểm tra vi phạm Show Don't Write:
    Nếu AI xuất các thực thể chính dạng Text ('CON KHỈ', 'CÂY', 'QUẢ CHUỐI'),
    hệ thống phải phát hiện vi phạm, gửi thông báo lỗi và yêu cầu sửa lại.
    """
    data = get_case_5_monkey_tree_banana()
    valid_plan = data["visual_plan"]

    # Tạo một invalid plan vi phạm nguyên tắc Show Don't Write
    invalid_entities = [
        VisualEntity(
            id="text_monkey",
            label="CON KHỈ",
            category="text",
            visual_type="text",
            importance="primary",
            drawing_intent="Viết chữ 'CON KHỈ'",
            position=Position(x=200, y=200, width=300, height=100),
        ),
        VisualEntity(
            id="text_tree",
            label="CÂY",
            category="text",
            visual_type="text",
            importance="primary",
            drawing_intent="Viết chữ 'CÂY'",
            position=Position(x=600, y=200, width=200, height=100),
        ),
    ]
    invalid_plan = VisualPlanOutput(
        project_title="Invalid Text Scene",
        scenes=[
            SceneVisualPlan(
                scene_index=1,
                title="Invalid Text Only Scene",
                duration_ms=4000,
                narration_text=data["script_text"],
                scene_graph=SceneGraph(entities=invalid_entities, relationships=[]),
            )
        ],
    )

    # Đưa invalid_plan ở lần 1, valid_plan ở lần 2 (repair loop)
    llm = MockLLMProvider(structured_responses=[invalid_plan, valid_plan])
    agent = VisualPlannerAgent(llm=llm, max_retries=2)

    result = await agent.plan_visuals(
        script=data["script_text"],
        segments=data["segments"],
    )

    assert result.success is True
    assert result.data["retries"] == 1  # Đã sửa thành công ở lần thử thứ 2!
    final_entities = result.data["visual_plan"]["scenes"][0]["scene_graph"]["entities"]
    # Ở kết quả cuối cùng, không còn thực thể dạng text
    assert all(e["visual_type"] != "text" for e in final_entities)


@pytest.mark.asyncio
async def test_semantic_missing_entity_triggers_repair():
    """Kiểm tra khi kế hoạch thị giác ban đầu thiếu 'tree', hệ thống phát hiện và sửa lại thành công."""
    data = get_case_5_monkey_tree_banana()
    valid_plan = data["visual_plan"]

    # Tạo plan ban đầu thiếu cây (chỉ có monkey và banana)
    broken_plan = copy.deepcopy(valid_plan)
    broken_plan.scenes[0].scene_graph.entities = [
        e for e in broken_plan.scenes[0].scene_graph.entities if e.label != "tree"
    ]
    # Bỏ quan hệ liên quan đến tree
    broken_plan.scenes[0].scene_graph.relationships = []

    llm = MockLLMProvider(structured_responses=[broken_plan, valid_plan])
    agent = VisualPlannerAgent(llm=llm, max_retries=2)

    result = await agent.plan_visuals(
        script=data["script_text"],
        segments=data["segments"],
    )

    assert result.success is True
    assert result.data["retries"] == 1
    # Đồ thị cuối cùng đã có lại thực thể tree
    labels = [e["label"] for e in result.data["visual_plan"]["scenes"][0]["scene_graph"]["entities"]]
    assert "tree" in labels


@pytest.mark.asyncio
async def test_visual_planner_bounded_retries_failure():
    """Kiểm tra khi lỗi liên tục vượt quá max_retries, trả về structured failure không crash."""
    llm = MockLLMProvider(fail_first_n_structured=10)
    agent = VisualPlannerAgent(llm=llm, max_retries=2)

    result = await agent.plan_visuals(
        script="Con khỉ trèo cây lấy chuối",
        segments=[ScriptSegment(text="Con khỉ trèo cây lấy chuối", estimated_duration_sec=3.0, semantic_meaning="Khỉ lấy chuối")],
    )

    assert result.success is False
    assert result.data["error_type"] == "visual_planning_validation_exhausted"
    assert result.data["retries"] == 2
    assert "Không thể lập kế hoạch thị giác hợp lệ sau 3 lần thử" in result.error_message
