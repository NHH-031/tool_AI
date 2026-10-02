"""Dữ liệu chuẩn hóa cho 5 Test Cases của Phase 04."""
from __future__ import annotations

from typing import Dict, Any
from core.schemas.annotation import CanvasSchema
from core.schemas.scene_graph import Position, SceneGraph, VisualEntity, VisualRelationship
from core.schemas.script import ScriptOutput, ScriptSegment
from core.schemas.visual_plan import SceneVisualPlan, VisualPlanOutput

CANVAS_1080P = CanvasSchema(width=1920, height=1080)


def get_case_1_dog_ball() -> Dict[str, Any]:
    """Case 1: Dog running after ball."""
    script_text = "Chú chó vui vẻ chạy đuổi theo quả bóng tròn trên bãi cỏ xanh."
    segment = ScriptSegment(
        cue_index=1,
        text=script_text,
        estimated_duration_sec=4.0,
        semantic_meaning="Chó đuổi theo quả bóng (hành động năng động)",
        key_entities=["dog", "ball"],
        suggested_actions=["chasing", "running"],
    )
    entities = [
        VisualEntity(
            id="dog_1",
            label="dog",
            category="character",
            visual_type="character",
            importance="primary",
            drawing_intent="Line art sketch of an energetic golden retriever running",
            actions=["running", "chasing"],
            position=Position(x=200, y=500, width=450, height=350),
            layer=1,
        ),
        VisualEntity(
            id="ball_1",
            label="ball",
            category="object",
            visual_type="object",
            importance="primary",
            drawing_intent="Sketch of a bouncing tennis ball with motion trails",
            actions=["bouncing"],
            position=Position(x=1200, y=600, width=150, height=150),
            layer=1,
        ),
    ]
    relationships = [
        VisualRelationship(
            id="rel_dog_ball",
            source_id="dog_1",
            target_id="ball_1",
            relation_type="chasing",
            action="chasing",
            description="Chú chó đang chạy hết tốc lực đuổi theo quả bóng",
        )
    ]
    scene_graph = SceneGraph(entities=entities, relationships=relationships)
    plan = VisualPlanOutput(
        project_title="Dog and Ball",
        scenes=[
            SceneVisualPlan(
                scene_index=1,
                title="Dog chasing ball",
                duration_ms=4000,
                narration_text=script_text,
                canvas=CANVAS_1080P,
                scene_graph=scene_graph,
            )
        ],
    )
    return {
        "idea": "Dog running after ball",
        "script_text": script_text,
        "segments": [segment],
        "visual_plan": plan,
    }


def get_case_2_teacher_math() -> Dict[str, Any]:
    """Case 2: Teacher explaining mathematics."""
    script_text = "Thầy giáo đang đứng cạnh bảng đen và nhiệt tình giảng giải công thức toán học."
    segment = ScriptSegment(
        cue_index=1,
        text=script_text,
        estimated_duration_sec=5.0,
        semantic_meaning="Thầy giáo giảng dạy công thức toán học",
        key_entities=["teacher", "mathematics"],
        suggested_actions=["explaining", "pointing"],
    )
    entities = [
        VisualEntity(
            id="teacher_1",
            label="teacher",
            category="character",
            visual_type="character",
            importance="primary",
            drawing_intent="Clear whiteboard illustration of a smiling professor holding a pointer",
            actions=["explaining", "pointing"],
            position=Position(x=250, y=250, width=400, height=700),
            layer=1,
        ),
        VisualEntity(
            id="math_board_1",
            label="mathematics",
            category="diagram",
            visual_type="diagram",
            importance="primary",
            drawing_intent="Diagram of a large blackboard containing quadratic equations and geometry charts",
            actions=["displaying"],
            position=Position(x=750, y=200, width=950, height=650),
            layer=0,
        ),
    ]
    relationships = [
        VisualRelationship(
            id="rel_teacher_math",
            source_id="teacher_1",
            target_id="math_board_1",
            relation_type="explaining",
            action="explaining",
            description="Thầy giáo chỉ thước và giảng giải công thức trên bảng",
        )
    ]
    scene_graph = SceneGraph(entities=entities, relationships=relationships)
    plan = VisualPlanOutput(
        project_title="Teacher explaining mathematics",
        scenes=[
            SceneVisualPlan(
                scene_index=1,
                title="Teacher explaining math",
                duration_ms=5000,
                narration_text=script_text,
                canvas=CANVAS_1080P,
                scene_graph=scene_graph,
            )
        ],
    )
    return {
        "idea": "Teacher explaining mathematics",
        "script_text": script_text,
        "segments": [segment],
        "visual_plan": plan,
    }


def get_case_3_temperature_molecules() -> Dict[str, Any]:
    """Case 3: Temperature makes molecules move faster."""
    script_text = "Khi nguồn nhiệt độ tăng cao, các phân tử bắt đầu chuyển động nhanh hơn và va chạm hỗn loạn."
    segment = ScriptSegment(
        cue_index=1,
        text=script_text,
        estimated_duration_sec=5.0,
        semantic_meaning="Nhiệt độ kích thích phân tử tăng tốc độ chuyển động",
        key_entities=["temperature", "molecules"],
        suggested_actions=["accelerating", "heating"],
    )
    entities = [
        VisualEntity(
            id="temp_heat_1",
            label="temperature",
            category="diagram",
            visual_type="diagram",
            importance="primary",
            drawing_intent="Visual diagram of a Bunsen burner flame beneath a thermal beaker with a rising red thermometer",
            actions=["heating"],
            position=Position(x=150, y=350, width=400, height=600),
            layer=0,
        ),
        VisualEntity(
            id="molecules_1",
            label="molecules",
            category="object",
            visual_type="diagram",
            importance="primary",
            drawing_intent="Set of molecular spheres with high-speed motion streak arrows indicating fast vibration",
            actions=["accelerating", "vibrating"],
            position=Position(x=650, y=250, width=1100, height=700),
            layer=1,
        ),
    ]
    relationships = [
        VisualRelationship(
            id="rel_temp_molecules",
            source_id="temp_heat_1",
            target_id="molecules_1",
            relation_type="accelerating",
            action="accelerating",
            description="Nguồn nhiệt kích hoạt gia tốc làm các phân tử tăng tốc",
        )
    ]
    scene_graph = SceneGraph(entities=entities, relationships=relationships)
    plan = VisualPlanOutput(
        project_title="Kinetic Molecular Theory",
        scenes=[
            SceneVisualPlan(
                scene_index=1,
                title="Thermal energy and molecular velocity",
                duration_ms=5000,
                narration_text=script_text,
                canvas=CANVAS_1080P,
                scene_graph=scene_graph,
            )
        ],
    )
    return {
        "idea": "Temperature makes molecules move faster",
        "script_text": script_text,
        "segments": [segment],
        "visual_plan": plan,
    }


def get_case_4_inflation() -> Dict[str, Any]:
    """Case 4: Inflation (Visual Metaphor)."""
    script_text = "Lạm phát tăng vọt làm giảm sức mua của đồng tiền một cách rõ rệt."
    segment = ScriptSegment(
        cue_index=1,
        text=script_text,
        estimated_duration_sec=4.5,
        semantic_meaning="Lạm phát tăng làm suy giảm giá trị thực tế của đồng tiền",
        key_entities=["inflation", "money"],
        suggested_actions=["eroding", "rising"],
    )
    entities = [
        VisualEntity(
            id="inflation_metaphor_1",
            label="inflation",
            category="metaphor",
            visual_type="metaphor",
            importance="primary",
            drawing_intent="Visual metaphor: an oversized price tag inflating like a giant hot air balloon floating upward",
            actions=["rising"],
            position=Position(x=1000, y=150, width=750, height=750),
            layer=1,
        ),
        VisualEntity(
            id="money_wallet_1",
            label="money",
            category="metaphor",
            visual_type="metaphor",
            importance="primary",
            drawing_intent="Visual metaphor: a shrinking paper banknote coin leaking air and losing size",
            actions=["shrinking"],
            position=Position(x=200, y=400, width=650, height=500),
            layer=0,
        ),
    ]
    relationships = [
        VisualRelationship(
            id="rel_inflation_money",
            source_id="inflation_metaphor_1",
            target_id="money_wallet_1",
            relation_type="eroding",
            action="eroding",
            description="Lạm phát leo thang bào mòn giá trị đồng tiền",
        )
    ]
    scene_graph = SceneGraph(entities=entities, relationships=relationships)
    plan = VisualPlanOutput(
        project_title="Understanding Inflation",
        scenes=[
            SceneVisualPlan(
                scene_index=1,
                title="Purchasing power erosion",
                duration_ms=4500,
                narration_text=script_text,
                canvas=CANVAS_1080P,
                scene_graph=scene_graph,
            )
        ],
    )
    return {
        "idea": "Inflation",
        "script_text": script_text,
        "segments": [segment],
        "visual_plan": plan,
    }


def get_case_5_monkey_tree_banana() -> Dict[str, Any]:
    """Case 5: Monkey climbing tree for banana."""
    script_text = "Con khỉ đang trèo lên cây để lấy một quả chuối chín vàng."
    segment = ScriptSegment(
        cue_index=1,
        text=script_text,
        estimated_duration_sec=4.0,
        semantic_meaning="Khỉ trèo lên cây với lấy quả chuối",
        key_entities=["monkey", "tree", "banana"],
        suggested_actions=["climbing", "reaching"],
    )
    entities = [
        VisualEntity(
            id="tree_1",
            label="tree",
            category="structure",
            visual_type="structure",
            importance="primary",
            drawing_intent="Illustration of a tall tropical palm tree with wide green fronds",
            actions=["standing"],
            position=Position(x=850, y=100, width=800, height=950),
            layer=0,
        ),
        VisualEntity(
            id="monkey_1",
            label="monkey",
            category="character",
            visual_type="character",
            importance="primary",
            drawing_intent="Playful monkey clinging to tree trunk with arm outstretched upwards",
            actions=["climbing", "reaching"],
            position=Position(x=950, y=400, width=320, height=450),
            layer=1,
        ),
        VisualEntity(
            id="banana_1",
            label="banana",
            category="object",
            visual_type="object",
            importance="primary",
            drawing_intent="Ripe yellow banana bunch hanging from palm branch",
            actions=["hanging"],
            position=Position(x=1200, y=200, width=220, height=200),
            layer=2,
        ),
    ]
    relationships = [
        VisualRelationship(
            id="rel_climbing",
            source_id="monkey_1",
            target_id="tree_1",
            relation_type="climbing",
            action="climbing",
            description="Con khỉ đang bám và trèo lên thân cây",
        ),
        VisualRelationship(
            id="rel_reaching",
            source_id="monkey_1",
            target_id="banana_1",
            relation_type="reaching",
            action="reaching",
            description="Con khỉ với tay lên nải chuối",
        ),
        VisualRelationship(
            id="rel_located_on",
            source_id="banana_1",
            target_id="tree_1",
            relation_type="located_on",
            action="located_on",
            description="Quả chuối mọc ở trên ngọn cây",
        ),
    ]
    scene_graph = SceneGraph(entities=entities, relationships=relationships)
    plan = VisualPlanOutput(
        project_title="Monkey and Banana",
        scenes=[
            SceneVisualPlan(
                scene_index=1,
                title="Monkey climbing tree",
                duration_ms=4000,
                narration_text=script_text,
                canvas=CANVAS_1080P,
                scene_graph=scene_graph,
            )
        ],
    )
    return {
        "idea": "Monkey climbing tree for banana",
        "script_text": script_text,
        "segments": [segment],
        "visual_plan": plan,
    }
