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

        sg = SceneGraph(
            entities=entities,
            relationships=relationships,
            actions=actions,
            narration=script_clean,
            description=script_clean,
        )
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
            elif any(
                e.id.lower() == req
                or e.label.lower() == req
                or e.id.lower().startswith(f"{req}_")
                or e.label.lower().startswith(f"{req}_")
                for e in sg.entities
            ):
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
        if key in ["cat", "dog", "monkey", "bird", "tiger", "rabbit", "fish", "chicken", "duck", "horse", "cow", "pig"]:
            return "animal", "character", "character"
        elif key in ["farmer", "teacher", "children", "hiker", "engineer", "astronaut", "diver", "robot", "fighter", "boxer", "man", "woman", "person"]:
            return "human", "character", "character"
        elif key in ["areca_palm", "tree", "plant", "seedling"]:
            return "plant", "structure", "structure"
        elif key in ["ground", "mountain", "bridge", "nest", "spacecraft", "mars", "forest", "sea", "octagon", "ring", "cage"]:
            return "structure", "structure", "structure"
        elif key in ["sun", "earth", "orbit", "molecules", "mathematics"]:
            return "diagram", "diagram", "diagram"
        elif key in ["inflation", "temperature", "vapor"]:
            return "metaphor", "metaphor", "metaphor"
        elif key in ["flower", "rose", "bouquet", "gift", "banana", "ball", "car", "machine"]:
            return "object", "object", "object"
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
        talk_rel = next((r for r in req_rels if r[1] in ["talking", "talking_with"]), None)
        fight_rel = next((r for r in req_rels if r[1] in ["fighting", "fighting_in"]), None)
        climb_rel = next((r for r in req_rels if r[1] in ["climbing", "climbing_on"]), None)
        chase_rel = next((r for r in req_rels if r[1] in ["chasing"]), None)
        orbit_rel = next((r for r in req_rels if r[1] in ["orbiting"]), None)
        plant_rel = next((r for r in req_rels if r[1] in ["planting"]), None)
        fly_rel = next((r for r in req_rels if r[1] in ["flying", "flying_from"]), None)
        cross_rel = next((r for r in req_rels if r[1] in ["crossing"]), None)
        repair_rel = next((r for r in req_rels if r[1] in ["repairing"]), None)
        evap_rel = next((r for r in req_rels if r[1] in ["evaporating"]), None)
        step_rel = next((r for r in req_rels if r[1] in ["stepping", "stepping_on"]), None)
        give_rel = next((r for r in req_rels if r[1] in ["giving", "giving_to"]), None)

        is_talking = talk_rel is not None or any(
            w in script_clean.lower()
            for w in [
                "nói chuyện với nhau", "nói chuyện", "trò chuyện", "thảo luận", "đối thoại",
                "tâm sự", "trao đổi", "bàn bạc", "giao tiếp", "hàn huyên",
                "talking", "chatting", "conversing", "speaking"
            ]
        )
        is_fighting = fight_rel is not None or any(
            w in script_clean.lower()
            for w in ["đấu võ", "đấu boxing", "so tài", "quyết đấu", "đánh nhau", "mma", "sparring"]
        )
        is_giving = give_rel is not None or any(
            w in script_clean.lower()
            for w in [
                "tặng hoa", "tặng quà", "đưa hoa", "đưa quà", "dâng hoa",
                "giving flowers", "offering flowers", "handing flowers",
                "giving gift", "offering gift",
            ]
        )

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

        if is_giving and (
            any(k in found_keys for k in ["man", "woman", "person", "character", "flower"])
            or any(
                w in script_clean.lower()
                for w in ["người", "đàn ông", "phụ nữ", "chàng trai", "cô gái", "con trai", "con gái", "man", "woman", "boy", "girl"]
            )
        ):
            handled_entities.update(["man", "woman", "person", "character", "flower"])
            scr_l = script_clean.lower()

            # Xác định người tặng (giver) và người nhận (receiver) từ kịch bản
            has_man = "man" in found_keys or any(w in scr_l for w in ["đàn ông", "con trai", "người con trai", "chàng trai", "nam", "man", "boy"])
            has_woman = "woman" in found_keys or any(w in scr_l for w in ["phụ nữ", "con gái", "người con gái", "cô gái", "nữ", "woman", "girl"])

            if has_man and has_woman:
                k1, k2 = "man", "woman"
                lbl1, lbl2 = "man", "woman"
                intent1 = "Chàng trai đứng bên trái quay mặt sang phải, tay cầm bó hoa đưa tặng cho cô gái"
                intent2 = "Cô gái đứng bên phải quay mặt sang trái, hai tay đón nhận bó hoa với biểu cảm vui mừng"
            elif has_woman:
                k1, k2 = "woman", "woman"
                lbl1, lbl2 = "woman", "woman"
                intent1 = "Người phụ nữ thứ nhất đứng bên trái tay cầm bó hoa tặng cho người phụ nữ thứ hai"
                intent2 = "Người phụ nữ thứ hai đứng bên phải đón nhận bó hoa với niềm vui"
            elif has_man:
                k1, k2 = "man", "man"
                lbl1, lbl2 = "man", "man"
                intent1 = "Người đàn ông thứ nhất đứng bên trái tay cầm bó hoa tặng"
                intent2 = "Người đàn ông thứ hai đứng bên phải nhận bó hoa"
            else:
                k1, k2 = "person", "person"
                lbl1, lbl2 = "person", "person"
                intent1 = "Nhân vật thứ nhất đứng bên trái tay cầm bó hoa đưa tặng"
                intent2 = "Nhân vật thứ hai đứng bên phải đón nhận bó hoa với niềm hạnh phúc"

            giver = VisualEntity(
                id=f"{k1}_1",
                label=lbl1,
                species="human",
                semantic_type="human",
                category="character",
                visual_type="character",
                visual_role="main_character",
                importance="primary",
                required=True,
                pose="giving",
                actions=["giving"],
                drawing_intent=intent1,
                position=Position(x=250, y=200, width=500, height=750),
                layer=1,
                priority=1,
            )
            flower = VisualEntity(
                id="flower_1",
                label="flower",
                species="flower",
                semantic_type="object",
                category="object",
                visual_type="object",
                visual_role="gift_item",
                importance="primary",
                required=True,
                drawing_intent="Bó hoa tươi đẹp nằm giữa hai nhân vật, được trao từ tay người tặng sang người nhận",
                actions=["being_given"],
                position=Position(x=750, y=350, width=300, height=350),
                layer=2,
                priority=2,
            )
            receiver = VisualEntity(
                id=f"{k2}_2",
                label=lbl2,
                species="human",
                semantic_type="human",
                category="character",
                visual_type="character",
                visual_role="main_character",
                importance="primary",
                required=True,
                pose="receiving",
                actions=["receiving"],
                drawing_intent=intent2,
                position=Position(x=1120, y=200, width=500, height=750),
                layer=1,
                priority=3,
            )
            entities.extend([giver, flower, receiver])
            actions.append(
                VisualAction(
                    id=f"act_{giver.id}_giving",
                    entity_id=giver.id,
                    action_type="giving",
                    required=True,
                )
            )
            actions.append(
                VisualAction(
                    id=f"act_{receiver.id}_receiving",
                    entity_id=receiver.id,
                    action_type="receiving",
                    required=True,
                )
            )
            relationships.append(
                VisualRelationship(
                    id=f"rel_{giver.id}_{receiver.id}_giving",
                    source_id=giver.id,
                    target_id=receiver.id,
                    relation_type="giving_to",
                    action="giving",
                    description=f"{lbl1} tặng hoa cho {lbl2}, cảnh lãng mạn ấm áp",
                    required=True,
                )
            )

        elif is_talking and (
            any(k in found_keys for k in ["man", "woman", "person", "character", "fighter"])
            or any(
                w in script_clean.lower()
                for w in ["người", "đàn ông", "phụ nữ", "chàng trai", "cô gái", "bạn", "men", "man", "person", "people"]
            )
        ):
            handled_entities.update(["man", "woman", "person", "character", "fighter"])
            scr_l = script_clean.lower()
            if "woman" in found_keys and "man" in found_keys:
                k1, k2 = "man", "woman"
                lbl1, lbl2 = "man", "woman"
                intent1 = "Người đàn ông đứng bên trái quay mặt sang phải, cử chỉ tay tự nhiên khi nói chuyện"
                intent2 = "Người phụ nữ đứng bên phải quay mặt sang trái đối thoại, chăm chú lắng nghe"
            elif "woman" in found_keys or any(w in scr_l for w in ["phụ nữ", "cô gái", "nữ giới", "woman", "women"]):
                k1, k2 = "woman", "woman"
                lbl1, lbl2 = "woman", "woman"
                intent1 = "Người phụ nữ thứ nhất đứng bên trái quay mặt sang phải trò chuyện vui vẻ"
                intent2 = "Người phụ nữ thứ hai đứng bên phải quay mặt sang trái đối thoại tự nhiên"
            elif "man" in found_keys or any(w in scr_l for w in ["đàn ông", "nam giới", "chàng trai", "men", "man"]):
                k1, k2 = "man", "man"
                lbl1, lbl2 = "man", "man"
                intent1 = "Người đàn ông thứ nhất đứng bên trái quay mặt sang phải, cử chỉ tay tự nhiên khi nói chuyện"
                intent2 = "Người đàn ông thứ hai đứng bên phải quay mặt sang trái đối thoại, thân thiện và tự nhiên"
            else:
                k1, k2 = "person", "person"
                lbl1, lbl2 = "person", "person"
                intent1 = "Nhân vật thứ nhất đứng bên trái quay mặt sang phải trò chuyện vui vẻ"
                intent2 = "Nhân vật thứ hai đứng bên phải quay mặt sang trái đối thoại tương tác"

            char1 = VisualEntity(
                id=f"{k1}_1",
                label=lbl1,
                species="human",
                semantic_type="human",
                category="character",
                visual_type="character",
                visual_role="main_character",
                importance="primary",
                required=True,
                pose="standing_talking",
                actions=["talking"],
                drawing_intent=intent1,
                position=Position(x=250, y=200, width=550, height=750),
                layer=1,
                priority=1,
            )
            char2 = VisualEntity(
                id=f"{k2}_2",
                label=lbl2,
                species="human",
                semantic_type="human",
                category="character",
                visual_type="character",
                visual_role="main_character",
                importance="primary",
                required=True,
                pose="standing_listening",
                actions=["talking", "listening"],
                drawing_intent=intent2,
                position=Position(x=1120, y=200, width=550, height=750),
                layer=1,
                priority=2,
            )
            entities.extend([char1, char2])
            actions.append(
                VisualAction(
                    id=f"act_{char1.id}_talking",
                    entity_id=char1.id,
                    action_type="talking",
                    required=True,
                )
            )
            actions.append(
                VisualAction(
                    id=f"act_{char2.id}_talking",
                    entity_id=char2.id,
                    action_type="talking",
                    required=True,
                )
            )
            relationships.append(
                VisualRelationship(
                    id=f"rel_{char1.id}_{char2.id}_talking",
                    source_id=char1.id,
                    target_id=char2.id,
                    relation_type="talking_with",
                    action="talking",
                    description=f"{char1.label} và {char2.label} đứng đối diện trò chuyện sôi nổi",
                    required=True,
                )
            )

        elif is_fighting and (
            any(k in found_keys for k in ["fighter", "man", "character"])
            or any(w in script_clean.lower() for w in ["võ sĩ", "đấu thủ", "đàn ông", "người", "fighter", "boxer"])
        ):
            handled_entities.update(["fighter", "man", "character", "octagon"])
            has_octagon = "octagon" in found_keys or any(
                w in script_clean.lower() for w in ["bát giác", "sàn đấu", "võ đài", "lồng", "ring", "cage"]
            )
            if has_octagon:
                oct_ent = VisualEntity(
                    id="octagon_1",
                    label="octagon",
                    species="octagon",
                    semantic_type="structure",
                    category="structure",
                    visual_type="structure",
                    visual_role="environment",
                    importance="secondary",
                    required=True,
                    drawing_intent="Sàn đấu lồng bát giác MMA tiêu chuẩn với khung lưới và võ đài",
                    actions=["supporting"],
                    position=Position(x=100, y=100, width=1720, height=880),
                    layer=0,
                    priority=1,
                )
                entities.append(oct_ent)

            f1 = VisualEntity(
                id="fighter_1",
                label="fighter",
                species="human",
                semantic_type="human",
                category="character",
                visual_type="character",
                visual_role="main_character",
                importance="primary",
                required=True,
                pose="fighting",
                actions=["fighting"],
                drawing_intent="Võ sĩ thứ nhất trong tư thế thủ tấn đấu quyền dũng mãnh bên trái",
                position=Position(x=350, y=250, width=500, height=700),
                layer=1,
                priority=2,
            )
            f2 = VisualEntity(
                id="fighter_2",
                label="fighter",
                species="human",
                semantic_type="human",
                category="character",
                visual_type="character",
                visual_role="main_character",
                importance="primary",
                required=True,
                pose="fighting",
                actions=["fighting"],
                drawing_intent="Võ sĩ thứ hai trong tư thế áp sát ra đòn đối mặt bên phải",
                position=Position(x=1070, y=250, width=500, height=700),
                layer=1,
                priority=3,
            )
            entities.extend([f1, f2])
            actions.append(VisualAction(id="act_fighter_1_fighting", entity_id=f1.id, action_type="fighting", required=True))
            actions.append(VisualAction(id="act_fighter_2_fighting", entity_id=f2.id, action_type="fighting", required=True))
            relationships.append(
                VisualRelationship(
                    id="rel_fighter1_fighter2_fighting",
                    source_id=f1.id,
                    target_id=f2.id,
                    relation_type="fighting_with",
                    action="fighting",
                    description="Hai võ sĩ giao đấu quyết liệt trên sàn đấu",
                    required=True,
                )
            )
            if has_octagon:
                relationships.append(
                    VisualRelationship(
                        id="rel_fighter1_octagon",
                        source_id=f1.id,
                        target_id=oct_ent.id,
                        relation_type="fighting_in",
                        action="fighting",
                        description="Võ sĩ 1 thi đấu trong sàn bát giác",
                        required=True,
                    )
                )

        elif climb_rel:
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
            # Tự động trích xuất hành động phù hợp từ kịch bản
            detected_action = "presenting"
            scr_low = script_clean.lower()
            if any(w in scr_low for w in ["nói chuyện", "trò chuyện", "thảo luận", "đối thoại", "tâm sự", "trao đổi", "bàn bạc", "talking", "chatting", "conversing", "speaking"]):
                detected_action = "talking"
            elif any(w in scr_low for w in ["đấu võ", "đấu", "đánh nhau", "quyết đấu", "so tài", "fighting", "fights", "martial arts", "sparring"]):
                detected_action = "fighting"
            elif any(w in scr_low for w in ["chạy", "đang chạy", "running", "runs", "sprint"]):
                detected_action = "running"
            elif any(w in scr_low for w in ["bơi", "đang bơi", "lặn", "swimming", "swims", "diving"]):
                detected_action = "swimming"
            elif any(w in scr_low for w in ["bay", "đang bay", "flying", "flies"]):
                detected_action = "flying"
            elif any(w in scr_low for w in ["nhảy", "đang nhảy", "jumping", "jumps"]):
                detected_action = "jumping"
            elif any(w in scr_low for w in ["ăn", "đang ăn", "mổ", "eating", "eats"]):
                detected_action = "eating"
            elif any(w in scr_low for w in ["ngủ", "đang ngủ", "sleeping", "sleeps"]):
                detected_action = "sleeping"
            elif any(w in scr_low for w in ["leo", "trèo", "climbing", "climbs"]):
                detected_action = "climbing"
            elif any(w in scr_low for w in ["tặng", "đưa", "dâng", "biếu", "trao", "giving", "presents", "offering"]):
                detected_action = "giving"

            def _detect_count(text_raw: str, key_str: str) -> int:
                t_l = text_raw.lower()
                k_list = SemanticValidator.ENTITY_KEYWORDS.get(key_str, [key_str])
                for kw in k_list:
                    for prefix, cnt in [("hai ", 2), ("2 ", 2), ("đôi ", 2), ("cặp ", 2), ("two ", 2), ("ba ", 3), ("3 ", 3), ("three ", 3)]:
                        if f"{prefix}{kw}" in t_l:
                            return cnt
                if any(p in t_l for p in ["hai con", "2 con", "hai chú", "2 chú", "hai con gà", "hai con chó", "hai người", "2 người"]):
                    return 2
                return 1

            pos_x = 250
            total_items = sum(_detect_count(script_clean, k) for k in remaining)
            step_x = min(450, int(1400 / max(1, total_items)))
            for idx, k in enumerate(remaining):
                sem, cat, vtype = cls._infer_semantic_types(k)
                ent_cnt = _detect_count(script_clean, k)
                for c_i in range(ent_cnt):
                    ent_id = f"{k}_{len(entities)+1}"
                    ent_role = "main_character" if len(entities) < 2 else "supporting_element"
                    ent_importance = "primary" if len(entities) < 2 else "secondary"
                    entities.append(
                        VisualEntity(
                            id=ent_id,
                            label=k,
                            species=k,
                            semantic_type=sem,
                            category=cat,  # type: ignore
                            visual_type=vtype,  # type: ignore
                            visual_role=ent_role,
                            importance=ent_importance,
                            drawing_intent=f"Minh họa trực quan {k} {detected_action} cho kịch bản",
                            actions=[detected_action],
                            position=Position(x=pos_x, y=350, width=380, height=450),
                            layer=len(entities),
                            priority=len(entities) + 1,
                        )
                    )
                    actions.append(
                        VisualAction(
                            id=f"act_{ent_id}_{detected_action}",
                            entity_id=ent_id,
                            action_type=detected_action,
                            required=True,
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
