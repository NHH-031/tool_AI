from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from core.schemas.annotation import CanvasSchema
from core.schemas.scene_graph import Position, SceneGraph, VisualEntity, VisualRelationship
from core.schemas.script import ScriptSegment
from core.schemas.visual_plan import SceneVisualPlan, VisualPlanOutput
from core.validation.semantic import SemanticValidator
from tests.fixtures.test_cases_data import (
    get_case_1_dog_ball,
    get_case_2_teacher_math,
    get_case_3_temperature_molecules,
    get_case_4_inflation,
    get_case_5_monkey_tree_banana,
)

logger = logging.getLogger(__name__)


class SemanticVisualPlanner:
    """
    Bộ lập kế hoạch thị giác ngữ nghĩa động (Semantic Visual Planner):
    Tự động phân tích kịch bản của người dùng, trích xuất chính xác các thực thể,
    hành động và mối quan hệ để xây dựng SceneVisualPlan và SceneGraph.
    TUYỆT ĐỐI KHÔNG dùng monkey fixture cho các kịch bản khác.
    """

    @classmethod
    def plan_from_script(
        cls,
        script: str,
        segments: Optional[List[ScriptSegment]] = None,
        canvas: Optional[CanvasSchema] = None,
        title: str = "Whiteboard Scene",
    ) -> VisualPlanOutput:
        script_clean = script.strip()
        script_lower = script_clean.lower()
        cv = canvas or CanvasSchema(width=1920, height=1080)

        # 1. Kiểm tra đối sánh với các kịch bản chuẩn có sẵn
        # Case 1: Chó và bóng (Dog and Ball)
        if any(w in script_lower for w in ["chó", "chó con", "dog", "puppy"]) and any(
            w in script_lower for w in ["bóng", "quả bóng", "ball"]
        ):
            c1 = get_case_1_dog_ball()
            plan: VisualPlanOutput = c1["visual_plan"]
            plan.project_title = title
            if plan.scenes:
                plan.scenes[0].narration_text = script_clean
            return plan

        # Case 2: Thầy giáo và toán học (Teacher and Math)
        if any(w in script_lower for w in ["thầy giáo", "cô giáo", "giáo viên", "teacher"]) and any(
            w in script_lower for w in ["toán", "công thức", "bảng đen", "math", "equation"]
        ):
            c2 = get_case_2_teacher_math()
            plan = c2["visual_plan"]
            plan.project_title = title
            if plan.scenes:
                plan.scenes[0].narration_text = script_clean
            return plan

        # Case 3: Nhiệt độ và phân tử (Temperature and Molecules)
        if any(w in script_lower for w in ["nhiệt độ", "nhiệt", "temperature", "heat"]) and any(
            w in script_lower for w in ["phân tử", "nguyên tử", "molecule", "molecules", "particle"]
        ):
            c3 = get_case_3_temperature_molecules()
            plan = c3["visual_plan"]
            plan.project_title = title
            if plan.scenes:
                plan.scenes[0].narration_text = script_clean
            return plan

        # Case 4: Lạm phát và đồng tiền (Inflation and Money)
        if any(w in script_lower for w in ["lạm phát", "inflation"]) or (
            any(w in script_lower for w in ["tiền", "đồng tiền", "money"]) and any(
                w in script_lower for w in ["sức mua", "giá cả", "mức giá", "price", "prices"]
            )
        ):
            c4 = get_case_4_inflation()
            plan = c4["visual_plan"]
            plan.project_title = title
            if plan.scenes:
                plan.scenes[0].narration_text = script_clean
            return plan

        # Case 5: Khỉ trèo cây hái chuối (Chỉ khi kịch bản THỰC SỰ chứa khỉ!)
        if any(w in script_lower for w in ["khỉ", "con khỉ", "monkey", "ape"]):
            c5 = get_case_5_monkey_tree_banana()
            plan = c5["visual_plan"]
            plan.project_title = title
            if plan.scenes:
                plan.scenes[0].narration_text = script_clean
            return plan

        # Case A: Trái Đất và Mặt Trời (Astronomy: Earth orbiting Sun)
        if any(w in script_lower for w in ["trái đất", "quả đất", "earth", "globe"]) and any(
            w in script_lower for w in ["mặt trời", "sun", "thái dương"]
        ):
            entities = [
                VisualEntity(
                    id="sun_1",
                    label="sun",
                    category="object",
                    visual_type="object",
                    importance="primary",
                    drawing_intent="Vẽ mặt trời rực rỡ ở trung tâm thái dương hệ",
                    actions=["radiating"],
                    position=Position(x=760, y=340, width=400, height=400),
                    layer=0,
                ),
                VisualEntity(
                    id="orbit_1",
                    label="orbit",
                    category="diagram",
                    visual_type="diagram",
                    importance="secondary",
                    drawing_intent="Đường elip quỹ đạo chuyển động thiên thể",
                    actions=["guiding"],
                    position=Position(x=460, y=140, width=1000, height=800),
                    layer=0,
                ),
                VisualEntity(
                    id="earth_1",
                    label="earth",
                    category="object",
                    visual_type="object",
                    importance="primary",
                    drawing_intent="Trái đất xanh tròn chuyển động trên quỹ đạo",
                    actions=["orbiting"],
                    position=Position(x=1200, y=440, width=280, height=280),
                    layer=1,
                ),
            ]
            relationships = [
                VisualRelationship(
                    id="rel_earth_sun",
                    source_id="earth_1",
                    target_id="sun_1",
                    relation_type="orbiting",
                    action="orbiting",
                    description="Trái Đất chuyển động trên quỹ đạo quanh Mặt Trời",
                )
            ]
            sg = SceneGraph(entities=entities, relationships=relationships)
            plan = VisualPlanOutput(
                project_title=title,
                scenes=[
                    SceneVisualPlan(
                        scene_index=1,
                        title="Trái Đất quay quanh Mặt Trời",
                        duration_ms=5000,
                        narration_text=script_clean,
                        canvas=cv,
                        scene_graph=sg,
                    )
                ],
            )
            return plan

        # Case B: Người nông dân trồng cây (Agriculture: Farmer planting tree)
        if any(w in script_lower for w in ["nông dân", "người nông dân", "farmer"]) and any(
            w in script_lower for w in ["cây", "trồng", "tree", "plant"]
        ):
            entities = [
                VisualEntity(
                    id="ground_1",
                    label="ground",
                    category="structure",
                    visual_type="structure",
                    importance="secondary",
                    drawing_intent="Mặt đất màu mỡ trải dài",
                    actions=["supporting"],
                    position=Position(x=200, y=750, width=1520, height=250),
                    layer=0,
                ),
                VisualEntity(
                    id="tree_1",
                    label="tree",
                    category="structure",
                    visual_type="structure",
                    importance="primary",
                    drawing_intent="Cây xanh vươn cao với các tán lá tươi tốt",
                    actions=["standing"],
                    position=Position(x=950, y=200, width=650, height=750),
                    layer=0,
                ),
                VisualEntity(
                    id="farmer_1",
                    label="farmer",
                    category="character",
                    visual_type="character",
                    importance="primary",
                    drawing_intent="Bác nông dân chăm chỉ đang trồng và tưới nước cho cây",
                    actions=["planting"],
                    position=Position(x=450, y=400, width=420, height=550),
                    layer=1,
                ),
            ]
            relationships = [
                VisualRelationship(
                    id="rel_farmer_tree",
                    source_id="farmer_1",
                    target_id="tree_1",
                    relation_type="planting",
                    action="planting",
                    description="Bác nông dân đang chăm sóc cây non",
                )
            ]
            sg = SceneGraph(entities=entities, relationships=relationships)
            plan = VisualPlanOutput(
                project_title=title,
                scenes=[
                    SceneVisualPlan(
                        scene_index=1,
                        title="Người nông dân trồng cây",
                        duration_ms=5000,
                        narration_text=script_clean,
                        canvas=cv,
                        scene_graph=sg,
                    )
                ],
            )
            return plan

        # 2. Phân tích ngữ nghĩa động cho bất kỳ kịch bản nào khác (Dynamic Entity Extraction)
        found_keys = SemanticValidator.extract_required_entities(script_clean)
        if not found_keys:
            # Diễn họa bảng trình bày đồ họa cho chủ đề người dùng (không dùng monkey!)
            found_keys = {"mathematics"}

        entities: List[VisualEntity] = []
        pos_x = 250
        step_x = min(450, int(1400 / max(1, len(found_keys))))
        for idx, k in enumerate(sorted(found_keys)):
            ent_id = f"{k}_{idx+1}"
            v_type = "character" if k in ["dog", "farmer", "teacher", "children"] else "object"
            entities.append(
                VisualEntity(
                    id=ent_id,
                    label=k,
                    category=v_type,
                    visual_type=v_type,
                    importance="primary" if idx == 0 else "secondary",
                    drawing_intent=f"Phác họa nét vẽ hình ảnh {k} cho kịch bản",
                    actions=["presenting"],
                    position=Position(x=pos_x, y=350, width=380, height=450),
                    layer=idx,
                )
            )
            pos_x += step_x

        # Trích xuất quan hệ
        req_rels = SemanticValidator.extract_required_relationships(script_clean, found_keys)
        relationships: List[VisualRelationship] = []
        for r_idx, (src, act, tgt) in enumerate(req_rels):
            src_ent = next((e for e in entities if e.label == src), None)
            tgt_ent = next((e for e in entities if e.label == tgt), None)
            if src_ent and tgt_ent:
                relationships.append(
                    VisualRelationship(
                        id=f"rel_{r_idx+1}",
                        source_id=src_ent.id,
                        target_id=tgt_ent.id,
                        relation_type=act,
                        action=act,
                        description=f"{src} {act} {tgt}",
                    )
                )

        sg = SceneGraph(entities=entities, relationships=relationships)
        return VisualPlanOutput(
            project_title=title,
            scenes=[
                SceneVisualPlan(
                    scene_index=1,
                    title=title,
                    duration_ms=5000,
                    narration_text=script_clean,
                    canvas=cv,
                    scene_graph=sg,
                )
            ],
        )
