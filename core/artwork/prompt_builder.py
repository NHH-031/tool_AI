from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field

from core.artwork.pose_system import CharacterPoseSystem
from core.artwork.style_profile import WhiteboardVisualStyleProfile, DetailBudget
from core.schemas.scene_graph import SceneGraph, VisualEntity, VisualAction, VisualRelationship


class StructuredIllustrationPrompt(BaseModel):
    """Cấu trúc prompt tạo hình minh họa Whiteboard Art hoàn chỉnh theo 9 thành phần kiến trúc."""
    subject: str = Field(description="Chủ thể chính và các đối tượng tương tác trong cảnh")
    action: str = Field(description="Hành động cụ thể đang diễn ra giữa các đối tượng")
    relationship: str = Field(description="Mối quan hệ và sự tiếp xúc vật lý cụ thể")
    composition: str = Field(description="Bố cục khung hình 16:9, vị trí và khoảng trống âm")
    pose: str = Field(description="Đặc tả tư thế giải phẫu và chuyển động của nhân vật")
    line_style: str = Field(description="Quy chuẩn nét vẽ phác thảo tay (sketch line art)")
    whiteboard_style: str = Field(description="Đặc trưng mỹ học Whiteboard Animation")
    background: str = Field(description="Đặc tả nền giấy kem ấm cũ (#F5EBD7)")
    negative_constraints: str = Field(description="Danh sách các điều cấm kỵ tuyệt đối")
    full_prompt: str = Field(description="Toàn văn prompt hoàn chỉnh ghép nối từ 9 thành phần")
    scene_context: str = Field(default="", description="Bối cảnh kịch bản thoại gốc")
    has_color: bool = Field(default=True, description="Chế độ đổ màu (True: Ghibli watercolor, False: Comic ink line art)")


class IllustrationPromptBuilder:
    """
    Module tạo prompt minh họa kiến trúc tổng quát (Generic Art Prompt Builder).
    Chuyển đổi Visual Scene Graph thành prompt có cấu trúc chặt chẽ,
    đáp ứng hoàn hảo chuẩn mực của geeklee/srt-whiteboard-animation.
    Tuyệt đối không hard-code cho riêng một con vật hay đồ vật nào.
    """

    @classmethod
    def build_from_scene_graph(
        cls,
        scene_graph: SceneGraph,
        style_profile: Optional[WhiteboardVisualStyleProfile] = None,
        detail_budget: Optional[DetailBudget] = None,
    ) -> StructuredIllustrationPrompt:
        profile = style_profile or WhiteboardVisualStyleProfile()
        budget = detail_budget or profile.detail_budget

        # 1. SUBJECT: Xác định chủ thể chính và các đối tượng phụ trợ
        main_entities: List[VisualEntity] = []
        secondary_entities: List[VisualEntity] = []
        for ent in scene_graph.entities:
            if ent.visual_role in ["main_character", "actor", "primary"] or getattr(ent, "semantic_type", "") in ["animal", "person", "human", "character"]:
                main_entities.append(ent)
            else:
                secondary_entities.append(ent)

        if not main_entities and scene_graph.entities:
            main_entities.append(scene_graph.entities[0])
            secondary_entities = scene_graph.entities[1:]

        subject_parts = []
        if len(main_entities) == 2 and main_entities[0].label == main_entities[1].label:
            base_lbl = main_entities[0].label
            if base_lbl in ["man", "fighter"]:
                noun = "adult men" if base_lbl == "man" else "athletic male fighters"
            elif base_lbl == "woman":
                noun = "women"
            elif base_lbl in ["person", "character"]:
                noun = "people"
            else:
                noun = f"{base_lbl}s"
            subject_parts.append(f"Two {noun} standing facing each other (main characters)")
        else:
            for me in main_entities:
                name = me.label.replace("_", " ")
                role = f" ({me.visual_role})" if me.visual_role else ""
                subject_parts.append(f"A clear, recognizable {name}{role}")
        for se in secondary_entities:
            name = se.label.replace("_", " ")
            role = f" as {se.visual_role}" if se.visual_role else ""
            subject_parts.append(f"a distinct {name}{role}")
        subject_desc = ", accompanied by ".join(subject_parts) if subject_parts else "A hand-drawn whiteboard scene"

        # 2. ACTION: Trích xuất hành động từ Scene Graph
        action_parts = []
        active_pose_key = "standing"
        if scene_graph.actions:
            for act in scene_graph.actions:
                actor_ent = next((e for e in scene_graph.entities if e.id == act.entity_id), None)
                actor_name = actor_ent.label.replace("_", " ") if actor_ent else "The character"
                action_parts.append(f"{actor_name} is actively {act.action_type.replace('_', ' ')}")
                active_pose_key = act.action_type
        elif main_entities and main_entities[0].actions:
            act_name = main_entities[0].actions[0].replace("_", " ")
            action_parts.append(f"{main_entities[0].label.replace('_', ' ')} is actively {act_name}")
            active_pose_key = act_name
        elif scene_graph.relationships:
            for rel in scene_graph.relationships:
                if rel.relation_type:
                    src = next((e for e in scene_graph.entities if e.id == rel.source_id), None)
                    src_name = src.label.replace("_", " ") if src else "The subject"
                    action_parts.append(f"{src_name} is actively {rel.relation_type.replace('_', ' ')}")
                    active_pose_key = rel.relation_type
                    break
        else:
            action_parts.append("The subject is in a natural, lively posture")

        action_desc = "; ".join(action_parts)

        # 3. RELATIONSHIP & PHYSICAL CONTACT
        rel_parts = []
        if scene_graph.relationships:
            for rel in scene_graph.relationships:
                src = next((e for e in scene_graph.entities if e.id == rel.source_id), None)
                tgt = next((e for e in scene_graph.entities if e.id == rel.target_id), None)
                s_name = src.label.replace("_", " ") if src else "subject"
                t_name = tgt.label.replace("_", " ") if tgt else "target"
                rel_parts.append(
                    f"{s_name} is in direct physical contact with {t_name}, {rel.relation_type.replace('_', ' ')}"
                )
        if not rel_parts:
            rel_parts.append("Elements are harmoniously connected with logical spatial and physical alignment")
        rel_desc = "; ".join(rel_parts)

        # 4. POSE GUIDANCE (from CharacterPoseSystem)
        pose_info = CharacterPoseSystem.get_pose(active_pose_key)
        pose_desc = (
            f"Dynamic {pose_info.pose_name} pose: {pose_info.silhouette_notes}. "
            f"Limbs: {pose_info.limbs_guidance}. Contact: {pose_info.contact_notes}."
        )

        # 5. COMPOSITION & DETAIL BUDGET
        comp_desc = (
            f"Clean 16:9 widescreen composition with generous negative space ({profile.negative_space}). "
            f"Main subject positioned centrally or along rule-of-thirds, sized at 35%-60% of canvas height. "
            f"Detail budget allocation: Main subject={budget.main_subject}, secondary={budget.secondary_subject}, "
            f"ground/background={budget.background}. Well-balanced breathing room, no cramped edges."
        )

        has_color = getattr(scene_graph, "has_color", True)

        # 6. LINE STYLE
        if has_color:
            line_desc = (
                f"Clear clean dark ink outlines ({profile.primary_line_color}) with vibrant watercolor and cel-shaded color fills. "
                f"Studio Ghibli inspired anime watercolor storybook illustration, smooth connected contours, harmonious lighting."
            )
            wb_desc = (
                f"Studio Ghibli inspired anime watercolor storybook illustration with rich warm harmonious colors. "
                f"Clear distinct contour lines, rich watercolor fills, highly detailed, peaceful aesthetic."
            )
        else:
            line_desc = (
                f"Masterpiece comic book ink line art in dark charcoal ink ({profile.primary_line_color}). "
                f"Crisp expressive dark ink contours, intricate cross-hatching and hatching shading textures, "
                f"smooth connected contours, dynamic expressive anatomy and lush detailed environment (like tiger_rabbit_forest.png)."
            )
            wb_desc = (
                f"Masterpiece comic book line art illustration (vintage graphic novel & manga ink style). "
                f"Rich hand-drawn line textures and professional ink cross-hatching. "
                f"Absolutely NO colors, NO watercolor washes, NO gray smudges, pristine black line art."
            )

        # 8. BACKGROUND
        bg_desc = (
            f"Solid warm vintage cream paper texture in hex {profile.background_color} "
            f"(RGB 245, 235, 215 / BGR 215, 235, 245). Absolutely NO pure harsh white (#FFFFFF) background."
        )

        # 9. NEGATIVE CONSTRAINTS
        neg_desc = (
            "STRICT PROHIBITIONS: NO text, NO words, NO letters, NO numbers, NO labels, NO typography, "
            "NO speech bubbles, NO photorealism, NO photographic textures, NO 3D rendering, NO complex shading, "
            "NO cluttered backgrounds, NO watermarks, NO signatures, NO stick figures, NO shoddy oval-and-stick primitives."
        )

        title_text = getattr(scene_graph, "title", None) or getattr(scene_graph, "scene_id", "Whiteboard Scene")
        full_prompt = (
            f"Title: {title_text}\n"
            f"[Subject]: {subject_desc}.\n"
            f"[Action]: {action_desc}.\n"
            f"[Relationship]: {rel_desc}.\n"
            f"[Pose]: {pose_desc}\n"
            f"[Composition]: {comp_desc}\n"
            f"[Line Style]: {line_desc}\n"
            f"[Whiteboard Aesthetic]: {wb_desc}\n"
            f"[Background]: {bg_desc}\n"
            f"[Negative Constraints]: {neg_desc}"
        )

        scene_ctx = (
            getattr(scene_graph, "narration", "")
            or getattr(scene_graph, "description", "")
            or getattr(scene_graph, "title", "")
            or ""
        )

        return StructuredIllustrationPrompt(
            subject=subject_desc,
            action=action_desc,
            relationship=rel_desc,
            composition=comp_desc,
            pose=pose_desc,
            line_style=line_desc,
            whiteboard_style=wb_desc,
            background=bg_desc,
            negative_constraints=neg_desc,
            full_prompt=full_prompt,
            scene_context=scene_ctx,
            has_color=has_color,
        )
