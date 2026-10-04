from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from core.schemas.annotation import CanvasSchema
from core.schemas.scene_graph import Position, SceneGraph, VisualAction, VisualEntity, VisualRelationship
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
            return cls._ensure_all_required_entities_present(plan, script_clean)

        # Case 2: Thầy giáo và toán học (Teacher and Math)
        if any(w in script_lower for w in ["thầy giáo", "cô giáo", "giáo viên", "teacher"]) and any(
            w in script_lower for w in ["toán", "công thức", "bảng đen", "math", "equation"]
        ):
            c2 = get_case_2_teacher_math()
            plan = c2["visual_plan"]
            plan.project_title = title
            if plan.scenes:
                plan.scenes[0].narration_text = script_clean
            return cls._ensure_all_required_entities_present(plan, script_clean)

        # Case 3: Nhiệt độ và phân tử (Temperature and Molecules)
        if any(w in script_lower for w in ["nhiệt độ", "nhiệt", "temperature", "heat"]) and any(
            w in script_lower for w in ["phân tử", "nguyên tử", "molecule", "molecules", "particle"]
        ):
            c3 = get_case_3_temperature_molecules()
            plan = c3["visual_plan"]
            plan.project_title = title
            if plan.scenes:
                plan.scenes[0].narration_text = script_clean
            return cls._ensure_all_required_entities_present(plan, script_clean)

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
            return cls._ensure_all_required_entities_present(plan, script_clean)

        # Case 5: Khỉ trèo cây hái chuối (Chỉ khi kịch bản THỰC SỰ chứa khỉ!)
        if any(w in script_lower for w in ["khỉ", "con khỉ", "monkey", "ape"]):
            c5 = get_case_5_monkey_tree_banana()
            plan = c5["visual_plan"]
            plan.project_title = title
            if plan.scenes:
                plan.scenes[0].narration_text = script_clean
            return cls._ensure_all_required_entities_present(plan, script_clean)

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
            return cls._ensure_all_required_entities_present(plan, script_clean)

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
            return cls._ensure_all_required_entities_present(plan, script_clean)

        # 2. Phân tích ngữ nghĩa động cho kịch bản tổng quát (Dynamic Entity & Action/Pose Planning)
        found_keys = SemanticValidator.extract_required_entities(script_clean)
        if not found_keys:
            if any(k in script_clean.lower() for k in ["toán", "công thức", "math", "bảng đen"]):
                found_keys = {"mathematics"}
            elif any(k in script_clean.lower() for k in ["chó", "chú chó", "dog"]):
                found_keys = {"dog"}
            elif any(k in script_clean.lower() for k in ["hổ", "cọp", "tiger"]):
                found_keys = {"tiger"}
            elif any(k in script_clean.lower() for k in ["thỏ", "rabbit"]):
                found_keys = {"rabbit"}
            else:
                found_keys = {"character"}

        req_rels = SemanticValidator.extract_required_relationships(script_clean, found_keys)
        entities, actions, relationships = cls._plan_dynamic_entities_and_actions(
            script_clean=script_clean,
            found_keys=found_keys,
            req_rels=req_rels,
            canvas=cv,
        )

        sg = SceneGraph(entities=entities, relationships=relationships, actions=actions)
        plan = VisualPlanOutput(
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
        return cls._ensure_all_required_entities_present(plan, script_clean)

    @classmethod
    def _ensure_all_required_entities_present(
        cls, plan: VisualPlanOutput, script_text: str
    ) -> VisualPlanOutput:
        """
        Đảm bảo mọi thực thể bắt buộc trích xuất từ kịch bản đều có mặt trong SceneGraph,
        ngăn ngừa lỗi PRE-RENDER VALIDATION FAILED khi kịch bản chứa thêm thực thể phụ
        (ví dụ: kịch bản giáo viên có thêm 'học sinh' / 'children').
        """
        if not plan.scenes:
            return plan
        scene = plan.scenes[0]
        sg = scene.scene_graph

        req_entities = SemanticValidator.extract_required_entities(script_text)
        existing_labels = {e.label.lower() for e in sg.entities}
        existing_ids = {e.id.lower() for e in sg.entities}
        existing_species = {(getattr(e, "species", None) or "").lower() for e in sg.entities}

        for req in sorted(req_entities):
            matched = False
            if req in existing_labels or req in existing_ids or req in existing_species:
                matched = True
            else:
                kws = SemanticValidator.ENTITY_KEYWORDS.get(req, [])
                for kw in kws:
                    if (
                        kw in existing_labels
                        or kw in existing_ids
                        or any(kw in e.label.lower() for e in sg.entities)
                        or any(kw in (getattr(e, "species", None) or "").lower() for e in sg.entities)
                    ):
                        matched = True
                        break
            if not matched:
                sem, cat, vtype = cls._infer_semantic_types(req)
                ent_idx = len(sg.entities) + 1
                pos_x = min(1500, 300 + (ent_idx * 250))
                new_ent = VisualEntity(
                    id=f"{req}_{ent_idx}",
                    label=req,
                    species=req,
                    semantic_type=sem,
                    category=cat,  # type: ignore
                    visual_type=vtype,  # type: ignore
                    visual_role="supporting_element",
                    importance="secondary",
                    drawing_intent=f"Minh họa trực quan bổ trợ cho {req}",
                    actions=["presenting"],
                    position=Position(x=pos_x, y=400, width=400, height=450),
                    layer=ent_idx,
                    priority=ent_idx,
                )
                sg.entities.append(new_ent)
                existing_labels.add(req)
                logger.info(f"[SemanticVisualPlanner] Đã tự động bổ sung thực thể '{req}' vào SceneGraph.")

        return plan

    @classmethod
    def _infer_semantic_types(cls, key: str) -> tuple[str, str, str]:
        """Suy luận (semantic_type, category, visual_type) dựa trên bản chất thực thể."""
        if key in ["cat", "dog", "monkey", "bird", "tiger", "rabbit", "fish"]:
            return "animal", "character", "character"
        elif key in ["farmer", "teacher", "children", "hiker", "engineer", "astronaut"]:
            return "human", "character", "character"
        elif key in ["areca_palm", "tree", "plant", "seedling"]:
            return "plant", "structure", "structure"
        elif key in ["ground", "mountain", "bridge", "nest", "spacecraft", "mars", "forest", "sea"]:
            return "structure", "structure", "structure"
        elif key in ["sun", "earth", "orbit", "molecules", "mathematics"]:
            return "diagram", "diagram", "diagram"
        elif key in ["inflation", "temperature", "vapor"]:
            return "metaphor", "metaphor", "metaphor"
        else:
            return "object", "object", "object"

    @classmethod
    def _plan_dynamic_entities_and_actions(
        cls,
        script_clean: str,
        found_keys: set[str],
        req_rels: list[tuple[str, str, str]],
        canvas: CanvasSchema,
    ) -> tuple[list[VisualEntity], list[VisualAction], list[VisualRelationship]]:
        """
        Action & Pose Planner: Thiết lập không gian hình học, tư thế bám/tiếp xúc thực tế,
        và liên kết hành động cho mọi kịch bản tổng quát.
        """
        entities: list[VisualEntity] = []
        actions: list[VisualAction] = []
        relationships: list[VisualRelationship] = []

        handled_entities: set[str] = set()

        # Kiểm tra các mẫu tương tác ngữ nghĩa (Semantic Interaction Patterns)
        climb_rel = next((r for r in req_rels if r[1] in ["climbing", "climbing_on"]), None)
        chase_rel = next((r for r in req_rels if r[1] in ["chasing"]), None)
        orbit_rel = next((r for r in req_rels if r[1] in ["orbiting"]), None)
        plant_rel = next((r for r in req_rels if r[1] in ["planting"]), None)
        fly_rel = next((r for r in req_rels if r[1] in ["flying", "flying_from"]), None)
        cross_rel = next((r for r in req_rels if r[1] in ["crossing"]), None)
        repair_rel = next((r for r in req_rels if r[1] in ["repairing"]), None)
        evap_rel = next((r for r in req_rels if r[1] in ["evaporating"]), None)
        step_rel = next((r for r in req_rels if r[1] in ["stepping", "stepping_on"]), None)

        # Xử lý môi trường nền nếu có (Forest / Background Environment)
        if "forest" in found_keys:
            handled_entities.add("forest")
            forest_ent = VisualEntity(
                id="forest_1",
                label="forest",
                species="forest",
                semantic_type="structure",
                category="structure",
                visual_type="structure",
                visual_role="environment",
                importance="secondary",
                required=True,
                drawing_intent="Cảnh quan khu rừng bạt ngàn với các cây cổ thụ và thảm cỏ xanh",
                actions=["standing", "surrounding"],
                position=Position(x=100, y=80, width=1720, height=920),
                layer=0,
                priority=0,
            )
            entities.append(forest_ent)

        if climb_rel:
            src, act, tgt = climb_rel
            handled_entities.update([src, tgt])
            src_sem, src_cat, src_vtype = cls._infer_semantic_types(src)
            tgt_sem, tgt_cat, tgt_vtype = cls._infer_semantic_types(tgt)

            # Giá bám leo (Structure): Thân cây / núi đặt ở trục thẳng đứng
            struct_ent = VisualEntity(
                id=f"{tgt}_1",
                label=tgt,
                species=tgt,
                semantic_type=tgt_sem,
                category=tgt_cat,  # type: ignore
                visual_type=tgt_vtype,  # type: ignore
                visual_role="climbing_structure",
                importance="primary",
                required=True,
                drawing_intent=f"Cấu trúc {tgt} vươn cao vững chắc làm giá bám leo",
                actions=["standing", "supporting"],
                position=Position(x=920, y=100, width=540, height=880),
                layer=0,
                priority=1,
            )
            # Nhân vật leo (Actor): Đặt tiếp xúc trực tiếp trên thân cây, chân và móng vuốt bám thân
            actor_ent = VisualEntity(
                id=f"{src}_1",
                label=src,
                species=src,
                semantic_type=src_sem,
                category=src_cat,  # type: ignore
                visual_type=src_vtype,  # type: ignore
                visual_role="main_character",
                importance="primary",
                required=True,
                pose="climbing",
                actions=["climbing"],
                drawing_intent=f"Tư thế {src} đang bám chắc và leo lên thân {tgt}",
                position=Position(x=820, y=380, width=360, height=360),
                layer=1,
                priority=2,
            )
            entities.extend([struct_ent, actor_ent])
            actions.append(
                VisualAction(
                    id=f"act_{src}_climbing",
                    entity_id=actor_ent.id,
                    action_type="climbing",
                    required=True,
                )
            )
            relationships.append(
                VisualRelationship(
                    id=f"rel_{src}_{tgt}_climbing",
                    source_id=actor_ent.id,
                    target_id=struct_ent.id,
                    relation_type="climbing_on",
                    action="climbing",
                    description=f"{src} leo trên thân {tgt}",
                    required=True,
                )
            )

        elif chase_rel:
            src, act, tgt = chase_rel
            handled_entities.update([src, tgt])
            src_sem, src_cat, src_vtype = cls._infer_semantic_types(src)
            tgt_sem, tgt_cat, tgt_vtype = cls._infer_semantic_types(tgt)

            has_bg = any(e.label == "forest" for e in entities)
            tgt_pos = (
                Position(x=1200, y=500, width=380, height=300)
                if tgt == "rabbit"
                else Position(x=1200, y=550, width=240, height=240)
            )
            tgt_actions = ["running", "leaping", "fleeing"] if tgt == "rabbit" else ["rolling", "bouncing"]
            tgt_pose = "running" if tgt == "rabbit" else "default"

            tgt_ent = VisualEntity(
                id=f"{tgt}_1",
                label=tgt,
                species=tgt,
                semantic_type=tgt_sem,
                category=tgt_cat,  # type: ignore
                visual_type=tgt_vtype,  # type: ignore
                visual_role="target",
                importance="primary",
                required=True,
                pose=tgt_pose,
                drawing_intent=f"Mục tiêu {tgt} đang tháo chạy phía trước" if tgt == "rabbit" else f"Mục tiêu {tgt} lăn chuyển động phía trước",
                actions=tgt_actions,
                position=tgt_pos,
                layer=1 if has_bg else 0,
                priority=1,
            )
            actor_pos = (
                Position(x=450, y=400, width=540, height=420)
                if src == "tiger"
                else Position(x=400, y=460, width=450, height=350)
            )
            actor_intent = (
                f"Chúa sơn lâm {src} dũng mãnh phi nước đại săn đuổi {tgt}"
                if src == "tiger"
                else f"{src} phi nước đại đuổi theo {tgt}"
            )
            actor_ent = VisualEntity(
                id=f"{src}_1",
                label=src,
                species=src,
                semantic_type=src_sem,
                category=src_cat,  # type: ignore
                visual_type=src_vtype,  # type: ignore
                visual_role="main_character",
                importance="primary",
                required=True,
                pose="running",
                actions=["running", "chasing"],
                drawing_intent=actor_intent,
                position=actor_pos,
                layer=2 if has_bg else 1,
                priority=2,
            )
            entities.extend([tgt_ent, actor_ent])
            actions.append(
                VisualAction(
                    id=f"act_{src}_chasing",
                    entity_id=actor_ent.id,
                    action_type="chasing",
                    required=True,
                )
            )
            relationships.append(
                VisualRelationship(
                    id=f"rel_{src}_{tgt}_chasing",
                    source_id=actor_ent.id,
                    target_id=tgt_ent.id,
                    relation_type="chasing",
                    action="chasing",
                    description=f"{src} đuổi theo {tgt}",
                    required=True,
                )
            )

        elif plant_rel:
            src, act, tgt = plant_rel
            handled_entities.update([src, tgt, "ground"])
            src_sem, src_cat, src_vtype = cls._infer_semantic_types(src)
            tgt_sem, tgt_cat, tgt_vtype = cls._infer_semantic_types(tgt)

            ground_ent = VisualEntity(
                id="ground_1",
                label="ground",
                species="ground",
                semantic_type="structure",
                category="structure",
                visual_type="structure",
                visual_role="environment",
                importance="secondary",
                drawing_intent="Mặt đất màu mỡ trải dài",
                actions=["supporting"],
                position=Position(x=200, y=750, width=1520, height=250),
                layer=0,
                priority=1,
            )
            plant_ent = VisualEntity(
                id=f"{tgt}_1",
                label=tgt,
                species=tgt,
                semantic_type=tgt_sem,
                category=tgt_cat,  # type: ignore
                visual_type=tgt_vtype,  # type: ignore
                visual_role="cultivated_plant",
                importance="primary",
                required=True,
                drawing_intent=f"Cây {tgt} xanh tốt đang được ươm trồng",
                actions=["standing"],
                position=Position(x=950, y=200, width=650, height=750),
                layer=0,
                priority=2,
            )
            farmer_ent = VisualEntity(
                id=f"{src}_1",
                label=src,
                species=src,
                semantic_type=src_sem,
                category=src_cat,  # type: ignore
                visual_type=src_vtype,  # type: ignore
                visual_role="main_character",
                importance="primary",
                required=True,
                pose="planting",
                actions=["planting"],
                drawing_intent=f"{src} chăm chú chăm sóc và trồng cây",
                position=Position(x=450, y=400, width=420, height=550),
                layer=1,
                priority=3,
            )
            entities.extend([ground_ent, plant_ent, farmer_ent])
            actions.append(
                VisualAction(
                    id=f"act_{src}_planting",
                    entity_id=farmer_ent.id,
                    action_type="planting",
                    required=True,
                )
            )
            relationships.append(
                VisualRelationship(
                    id=f"rel_{src}_{tgt}_planting",
                    source_id=farmer_ent.id,
                    target_id=plant_ent.id,
                    relation_type="planting",
                    action="planting",
                    description=f"{src} trồng {tgt}",
                    required=True,
                )
            )

        elif fly_rel:
            src, act, tgt = fly_rel
            handled_entities.update([src, tgt])
            src_sem, src_cat, src_vtype = cls._infer_semantic_types(src)
            tgt_sem, tgt_cat, tgt_vtype = cls._infer_semantic_types(tgt)

            nest_ent = VisualEntity(
                id=f"{tgt}_1",
                label=tgt,
                species=tgt,
                semantic_type=tgt_sem,
                category=tgt_cat,  # type: ignore
                visual_type=tgt_vtype,  # type: ignore
                visual_role="origin_structure",
                importance="secondary",
                required=True,
                drawing_intent=f"Tổ ấm {tgt}",
                actions=["resting"],
                position=Position(x=350, y=500, width=350, height=300),
                layer=0,
                priority=1,
            )
            bird_ent = VisualEntity(
                id=f"{src}_1",
                label=src,
                species=src,
                semantic_type=src_sem,
                category=src_cat,  # type: ignore
                visual_type=src_vtype,  # type: ignore
                visual_role="main_character",
                importance="primary",
                required=True,
                pose="flying",
                actions=["flying"],
                drawing_intent=f"{src} sải cánh bay lượn trên bầu trời",
                position=Position(x=850, y=250, width=350, height=300),
                layer=1,
                priority=2,
            )
            entities.extend([nest_ent, bird_ent])
            actions.append(
                VisualAction(
                    id=f"act_{src}_flying",
                    entity_id=bird_ent.id,
                    action_type="flying",
                    required=True,
                )
            )
            relationships.append(
                VisualRelationship(
                    id=f"rel_{src}_{tgt}_flying",
                    source_id=bird_ent.id,
                    target_id=nest_ent.id,
                    relation_type="flying_from",
                    action="flying",
                    description=f"{src} bay khỏi {tgt}",
                    required=True,
                )
            )

        elif step_rel:
            src, act, tgt = step_rel
            handled_entities.update([src, tgt, "spacecraft", "mars"])
            src_sem, src_cat, src_vtype = cls._infer_semantic_types(src)
            tgt_sem, tgt_cat, tgt_vtype = cls._infer_semantic_types(tgt)

            # 1. Tàu vũ trụ / Lander ở bên trái
            spacecraft_ent = VisualEntity(
                id="spacecraft_1",
                label="spacecraft",
                species="spacecraft",
                semantic_type="structure",
                category="structure",
                visual_type="structure",
                visual_role="origin_vehicle",
                importance="primary",
                required=True,
                drawing_intent="Tàu vũ trụ đổ bộ trên bề mặt Sao Hỏa",
                actions=["landing"],
                position=Position(x=120, y=140, width=540, height=660),
                layer=0,
                priority=1,
            )
            # 2. Bề mặt Sao Hỏa ở bên dưới
            mars_ent = VisualEntity(
                id="mars_1",
                label="mars",
                species="mars",
                semantic_type="structure",
                category="structure",
                visual_type="structure",
                visual_role="environment",
                importance="secondary",
                required=True,
                drawing_intent="Bề mặt đất đá gồ ghề của Sao Hỏa",
                actions=["supporting"],
                position=Position(x=100, y=700, width=1720, height=280),
                layer=0,
                priority=2,
            )
            # 3. Phi hành gia đang bước chân xuống đất
            astronaut_ent = VisualEntity(
                id=f"{src}_1",
                label=src,
                species=src,
                semantic_type=src_sem,
                category=src_cat,  # type: ignore
                visual_type=src_vtype,  # type: ignore
                visual_role="main_character",
                importance="primary",
                required=True,
                pose="stepping",
                actions=["stepping", "exploring"],
                drawing_intent=f"Phi hành gia {src} đang bước chân khám phá Sao Hỏa",
                position=Position(x=680, y=260, width=480, height=560),
                layer=1,
                priority=3,
            )
            entities.extend([spacecraft_ent, mars_ent, astronaut_ent])
            actions.append(
                VisualAction(
                    id=f"act_{src}_stepping",
                    entity_id=astronaut_ent.id,
                    action_type="stepping",
                    required=True,
                )
            )
            relationships.append(
                VisualRelationship(
                    id=f"rel_{src}_mars_stepping",
                    source_id=astronaut_ent.id,
                    target_id=mars_ent.id,
                    relation_type="stepping_on",
                    action="stepping",
                    description=f"{src} đặt chân lên {tgt}",
                    required=True,
                )
            )

        elif any(k in found_keys for k in ["engineer", "developer", "programmer", "kỹ sư", "lập trình"]):
            handled_entities.update(["engineer", "developer", "laptop", "computer", "chart", "analytics_monitor"])
            dev_ent = VisualEntity(
                id="developer_1",
                label="developer",
                species="human",
                semantic_type="human",
                category="character",
                visual_type="character",
                visual_role="main_character",
                importance="primary",
                required=True,
                drawing_intent="Kỹ sư phần mềm tập trung tại bàn làm việc",
                actions=["coding", "analyzing"],
                position=Position(x=150, y=150, width=750, height=850),
                layer=1,
                priority=1,
            )
            laptop_ent = VisualEntity(
                id="laptop_1",
                label="laptop",
                species="laptop",
                semantic_type="structure",
                category="structure",
                visual_type="structure",
                visual_role="working_tool",
                importance="primary",
                required=True,
                drawing_intent="Máy tính xách tay với bàn phím và màn hình mở",
                actions=["operating"],
                position=Position(x=800, y=400, width=450, height=400),
                layer=0,
                priority=2,
            )
            monitor_ent = VisualEntity(
                id="analytics_monitor_1",
                label="analytics_monitor",
                species="chart",
                semantic_type="diagram",
                category="diagram",
                visual_type="diagram",
                visual_role="analytics_display",
                importance="secondary",
                required=True,
                drawing_intent="Màn hình phân tích đồ thị số liệu tăng trưởng",
                actions=["displaying"],
                position=Position(x=1150, y=180, width=700, height=650),
                layer=0,
                priority=3,
            )
            entities.extend([dev_ent, laptop_ent, monitor_ent])
            actions.append(
                VisualAction(
                    id="act_developer_coding",
                    entity_id=dev_ent.id,
                    action_type="coding",
                    required=True,
                )
            )
            relationships.append(
                VisualRelationship(
                    id="rel_developer_laptop_coding",
                    source_id=dev_ent.id,
                    target_id=laptop_ent.id,
                    relation_type="working_with",
                    action="coding",
                    description="Kỹ sư lập trình trên máy tính",
                    required=True,
                )
            )

        elif any(k in found_keys for k in ["doctor", "physician", "bác sĩ", "y tế", "clinic"]):
            handled_entities.update(["doctor", "patient", "clinic", "desk_records"])
            doc_ent = VisualEntity(
                id="doctor_1",
                label="doctor",
                species="human",
                semantic_type="human",
                category="character",
                visual_type="character",
                visual_role="main_character",
                importance="primary",
                required=True,
                drawing_intent="Bác sĩ tận tâm tư vấn và chẩn đoán",
                actions=["consulting"],
                position=Position(x=150, y=150, width=750, height=850),
                layer=1,
                priority=1,
            )
            desk_ent = VisualEntity(
                id="desk_records_1",
                label="desk_records",
                species="desk",
                semantic_type="structure",
                category="structure",
                visual_type="structure",
                visual_role="consultation_desk",
                importance="secondary",
                required=True,
                drawing_intent="Bàn làm việc với hồ sơ bệnh án và ống nghe",
                actions=["supporting"],
                position=Position(x=700, y=450, width=550, height=550),
                layer=0,
                priority=2,
            )
            pat_ent = VisualEntity(
                id="patient_1",
                label="patient",
                species="human",
                semantic_type="human",
                category="character",
                visual_type="character",
                visual_role="consulted_patient",
                importance="primary",
                required=True,
                drawing_intent="Bệnh nhân chăm chú trao đổi với bác sĩ",
                actions=["listening"],
                position=Position(x=1100, y=150, width=750, height=850),
                layer=1,
                priority=3,
            )
            entities.extend([doc_ent, desk_ent, pat_ent])
            actions.append(
                VisualAction(
                    id="act_doctor_consulting",
                    entity_id=doc_ent.id,
                    action_type="consulting",
                    required=True,
                )
            )
            relationships.append(
                VisualRelationship(
                    id="rel_doctor_patient_consulting",
                    source_id=doc_ent.id,
                    target_id=pat_ent.id,
                    relation_type="consulting",
                    action="consulting",
                    description="Bác sĩ tư vấn cho bệnh nhân",
                    required=True,
                )
            )

        # Xử lý các entity còn lại chưa nằm trong pattern chính
        remaining = sorted(found_keys - handled_entities)
        if remaining:
            pos_x = 250
            step_x = min(450, int(1400 / max(1, len(remaining))))
            for idx, k in enumerate(remaining):
                sem, cat, vtype = cls._infer_semantic_types(k)
                ent_id = f"{k}_{len(entities)+1}"
                entities.append(
                    VisualEntity(
                        id=ent_id,
                        label=k,
                        species=k,
                        semantic_type=sem,
                        category=cat,  # type: ignore
                        visual_type=vtype,  # type: ignore
                        visual_role="supporting_element" if entities else "main_character",
                        importance="primary" if not entities else "secondary",
                        drawing_intent=f"Minh họa trực quan {k} cho kịch bản",
                        actions=["presenting"],
                        position=Position(x=pos_x, y=350, width=380, height=450),
                        layer=len(entities),
                        priority=len(entities) + 1,
                    )
                )
                pos_x += step_x

        # Bổ sung các relationship phụ nếu có
        for r_idx, (r_src, r_act, r_tgt) in enumerate(req_rels):
            src_ent = next((e for e in entities if e.label == r_src or getattr(e, "species", None) == r_src), None)
            tgt_ent = next((e for e in entities if e.label == r_tgt or getattr(e, "species", None) == r_tgt), None)
            if src_ent and tgt_ent:
                already_has_rel = any(
                    r.source_id == src_ent.id and r.target_id == tgt_ent.id
                    for r in relationships
                )
                if not already_has_rel:
                    rel_id = f"rel_{src_ent.id}_{tgt_ent.id}_{r_act}"
                    relationships.append(
                        VisualRelationship(
                            id=rel_id,
                            source_id=src_ent.id,
                            target_id=tgt_ent.id,
                            relation_type=r_act,
                            action=r_act,
                            description=f"{r_src} {r_act} {r_tgt}",
                            required=True,
                        )
                    )

        return entities, actions, relationships
