from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from core.schemas.project import Scene
from core.schemas.scene_graph import SceneGraph


class SemanticValidationResult(BaseModel):
    """Kết quả kiểm tra tính nhất quán ngữ nghĩa giữa lời thoại và hình ảnh."""
    is_valid: bool = Field(description="Đạt yêu cầu logic ngữ nghĩa hay không")
    missing_entities: List[str] = Field(default_factory=list, description="Các thực thể có trong lời thoại nhưng thiếu trong Scene Graph")
    missing_relationships: List[str] = Field(
        default_factory=list, description="Các quan hệ/hành động kịch bản yêu cầu nhưng thiếu trong Scene Graph"
    )
    errors: List[str] = Field(default_factory=list, description="Chi tiết thông báo lỗi ngữ nghĩa")
    warnings: List[str] = Field(default_factory=list, description="Các cảnh báo lệch nhẹ")


class SemanticValidator:
    """
    Bộ thẩm định ngữ nghĩa: Đối chiếu nội dung lời thuyết minh (Narration) với Scene Graph
    để phát hiện đối tượng bị bỏ sót (missing entity) hoặc hành động bị thiếu (missing relationship).
    """

    # Từ điển ánh xạ từ vựng tiếng Việt và tiếng Anh sang entity canonical key
    ENTITY_KEYWORDS: Dict[str, List[str]] = {
        "monkey": ["khỉ", "con khỉ", "chú khỉ", "monkey", "ape"],
        "tree": ["cây", "cái cây", "thân cây", "tree"],
        "banana": ["chuối", "quả chuối", "trái chuối", "banana"],
        "mountain": ["núi", "núi giả", "hòn non bộ", "mountain", "rockery"],
        "children": ["trẻ em", "em bé", "bọn trẻ", "khán giả", "children", "kids", "crowd"],
        "car": ["xe", "ô tô", "xe hơi", "car"],
    }

    # Từ điển ánh xạ hành động / quan hệ: (action_key, source, target, keywords)
    RELATIONSHIP_RULES: List[Dict] = [
        {
            "action": "climbing",
            "source": "monkey",
            "target": "tree",
            "keywords": ["trèo", "leo", "climb", "climbing"],
        },
        {
            "action": "reaching",
            "source": "monkey",
            "target": "banana",
            "keywords": ["với", "với tới", "reach", "reaching"],
        },
        {
            "action": "located_on",
            "source": "banana",
            "target": "tree",
            "keywords": ["trên cây", "ở trên cây", "located on", "located_on", "mọc trên cây"],
        },
        {
            "action": "grabbing",
            "source": "monkey",
            "target": "banana",
            "keywords": ["cướp", "giật", "chộp", "grab", "snatch", "grabbing"],
        },
    ]

    @classmethod
    def extract_required_entities(cls, text: str) -> Set[str]:
        """Trích xuất các thực thể bắt buộc phải xuất hiện từ văn bản thoại."""
        text_lower = text.lower()
        found: Set[str] = set()
        for entity_key, keywords in cls.ENTITY_KEYWORDS.items():
            for kw in keywords:
                # Tìm từ nguyên vẹn với regex word boundary hoặc substring cho tiếng Việt
                pattern = r"(?:\b|^)" + re.escape(kw) + r"(?:\b|$)"
                if re.search(pattern, text_lower) or kw in text_lower:
                    found.add(entity_key)
                    break
        return found

    @classmethod
    def extract_required_relationships(cls, text: str, present_entities: Set[str]) -> List[Tuple[str, str, str]]:
        """
        Trích xuất các mối quan hệ ngữ nghĩa bắt buộc từ câu thoại.
        Trả về danh sách (source_entity, action, target_entity).
        """
        text_lower = text.lower()
        required_rels: List[Tuple[str, str, str]] = []
        for rule in cls.RELATIONSHIP_RULES:
            src, tgt, act = rule["source"], rule["target"], rule["action"]
            # Chỉ yêu cầu quan hệ nếu cả 2 đối tượng đều xuất hiện trong câu
            if src in present_entities and tgt in present_entities:
                for kw in rule["keywords"]:
                    if kw in text_lower:
                        required_rels.append((src, act, tgt))
                        break
        return required_rels

    @classmethod
    def validate_scene(cls, scene: Scene) -> SemanticValidationResult:
        """
        Thẩm định ngữ nghĩa cho toàn bộ phân cảnh bằng cách đối chiếu
        tổng hợp các câu thuyết minh với Scene Graph hiện tại.
        """
        full_narration = " ".join([seg.text for seg in scene.narration]).strip()
        return cls.validate_narration_against_graph(full_narration, scene.scene_graph)

    @classmethod
    def validate_narration_against_graph(
        cls, narration_text: str, scene_graph: SceneGraph
    ) -> SemanticValidationResult:
        """Kiểm tra đối chiếu văn bản thuyết minh với SceneGraph."""
        errors: List[str] = []
        warnings: List[str] = []
        missing_entities: List[str] = []
        missing_relationships: List[str] = []

        if not narration_text:
            return SemanticValidationResult(is_valid=True)

        # 1. Trích xuất thực thể kịch bản yêu cầu
        required_entities = cls.extract_required_entities(narration_text)

        # 2. Tập hợp các thực thể có sẵn trong SceneGraph (chuẩn hóa về lowercase key)
        available_entity_labels = {
            e.label.lower(): e.id for e in scene_graph.entities
        }
        available_entity_ids = {
            e.id.lower(): e.label.lower() for e in scene_graph.entities
        }

        def has_entity(req_key: str) -> bool:
            # Kiểm tra khớp ID hoặc nhãn hoặc từ đồng nghĩa
            if req_key in available_entity_ids or req_key in available_entity_labels:
                return True
            for kw in cls.ENTITY_KEYWORDS.get(req_key, []):
                if kw in available_entity_ids or kw in available_entity_labels:
                    return True
                # Kiểm tra substring trong nhãn (ví dụ: 'chú khỉ con' chứa 'khỉ')
                if any(kw in label for label in available_entity_labels):
                    return True
            return False

        # Kiểm tra missing entities
        for req in sorted(required_entities):
            if not has_entity(req):
                missing_entities.append(req)
                errors.append(
                    f"Missing entity: '{req}' được nhắc đến trong lời thoại nhưng không có trong Visual Scene Graph"
                )

        # 3. Trích xuất quan hệ/hành động kịch bản yêu cầu
        required_rels = cls.extract_required_relationships(narration_text, required_entities)

        # 4. Kiểm tra missing relationships
        for src_req, act_req, tgt_req in required_rels:
            # Tìm xem trong graph có quan hệ tương ứng không
            matched = False
            for rel in scene_graph.relationships:
                rel_type = (rel.relation_type or "").lower()
                rel_act = (rel.action or "").lower()
                # Kiểm tra khớp loại quan hệ
                if act_req in rel_type or act_req in rel_act or rel_type in act_req:
                    # Kiểm tra xem source và target của relation có tương ứng src_req và tgt_req không
                    src_ent = scene_graph.get_entity(rel.source_id)
                    tgt_ent = scene_graph.get_entity(rel.target_id)
                    if src_ent and tgt_ent:
                        src_match = (
                            src_req in src_ent.id.lower() or src_req in src_ent.label.lower()
                            or any(kw in src_ent.label.lower() for kw in cls.ENTITY_KEYWORDS.get(src_req, []))
                        )
                        tgt_match = (
                            tgt_req in tgt_ent.id.lower() or tgt_req in tgt_ent.label.lower()
                            or any(kw in tgt_ent.label.lower() for kw in cls.ENTITY_KEYWORDS.get(tgt_req, []))
                        )
                        if src_match and tgt_match:
                            matched = True
                            break

            if not matched:
                rel_desc = f"{src_req} -> {act_req} -> {tgt_req}"
                missing_relationships.append(rel_desc)
                errors.append(
                    f"Missing relationship: Lời thoại yêu cầu hành động '{rel_desc}' nhưng Scene Graph không khai báo"
                )

        return SemanticValidationResult(
            is_valid=len(errors) == 0,
            missing_entities=missing_entities,
            missing_relationships=missing_relationships,
            errors=errors,
            warnings=warnings,
        )
