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
    show_dont_write_violations: List[str] = Field(
        default_factory=list, description="Các vi phạm nguyên tắc Show Don't Write (dùng text thay vì minh họa trực quan)"
    )
    errors: List[str] = Field(default_factory=list, description="Chi tiết thông báo lỗi ngữ nghĩa")
    warnings: List[str] = Field(default_factory=list, description="Các cảnh báo lệch nhẹ")


class SemanticValidator:
    """
    Bộ thẩm định ngữ nghĩa: Đối chiếu nội dung lời thuyết minh (Narration) với Scene Graph
    để phát hiện đối tượng bị bỏ sót (missing entity), hành động bị thiếu (missing relationship),
    hoặc vi phạm nguyên tắc Show Don't Write (lạm dụng text thay cho hình vẽ).
    """

    # Từ điển ánh xạ từ vựng tiếng Việt và tiếng Anh sang entity canonical key
    ENTITY_KEYWORDS: Dict[str, List[str]] = {
        # Case 5 & General
        "monkey": ["khỉ", "con khỉ", "chú khỉ", "con khi", "chu khi", "monkey", "ape"],
        "tree": ["cây", "cái cây", "thân cây", "cay", "cai cay", "than cay", "tree"],
        "banana": ["chuối", "quả chuối", "trái chuối", "chuoi", "qua chuoi", "trai chuoi", "banana"],
        "mountain": ["núi", "núi giả", "hòn non bộ", "nui", "nui gia", "mountain", "rockery"],
        "children": ["trẻ em", "em bé", "bọn trẻ", "khán giả", "tre em", "em be", "bon tre", "children", "kids", "crowd"],
        "car": ["xe", "ô tô", "xe hơi", "xe hoi", "o to", "car"],
        # Case 1: Dog running after ball
        "dog": ["chó", "con chó", "chú chó", "cho", "con cho", "chu cho", "dog", "puppy", "canine"],
        "ball": ["bóng", "quả bóng", "trái bóng", "bong", "qua bong", "trai bong", "ball"],
        # Case 2: Teacher explaining mathematics
        "teacher": ["giáo viên", "thầy giáo", "cô giáo", "giao vien", "thay giao", "co giao", "teacher", "instructor", "professor"],
        "mathematics": ["toán", "toán học", "công thức", "bảng đen", "toan", "toan hoc", "cong thuc", "bang den", "mathematics", "math", "formula", "blackboard", "equations"],
        # Case 3: Temperature makes molecules move faster
        "temperature": ["nhiệt độ", "nguồn nhiệt", "lửa", "độ nóng", "nhiet do", "nguon nhiet", "lua", "do nong", "temperature", "heat", "heat_source", "burner"],
        "molecules": ["phân tử", "nguyên tử", "hạt", "phan tu", "nguyen tu", "hat", "molecules", "atoms", "particles"],
        # Case 4: Inflation
        "inflation": ["lạm phát", "mức giá", "giá cả", "lam phat", "muc gia", "gia ca", "inflation", "price", "price_tag", "prices"],
        "goods_basket": ["giỏ hàng", "hàng hóa", "gio hang", "hang hoa", "shopping cart", "goods", "basket"],
        # Astronomy: Earth around Sun
        "earth": ["trái đất", "quả đất", "địa cầu", "trai dat", "qua dat", "dia cau", "earth", "globe", "planet"],
        "sun": ["mặt trời", "thái dương", "mat troi", "thai duong", "sun", "sunlight"],
        "orbit": ["quỹ đạo", "vòng quay", "quy dao", "vong quay", "orbit", "orbiting", "ellipse"],
        # Agriculture: Farmer planting tree
        "farmer": ["nông dân", "người nông dân", "bác nông dân", "nong dan", "nguoi nong dan", "bac nong dan", "farmer", "grower"],
        "ground": ["mặt đất", "mảnh đất", "đồng ruộng", "cánh đồng", "mat dat", "manh dat", "dong ruong", "canh dong", "ground", "soil"],
    }

    # Từ điển ánh xạ hành động / quan hệ: (action_key, source, target, keywords)
    RELATIONSHIP_RULES: List[Dict] = [
        # Case 5
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
        # Case 1: Dog running after ball
        {
            "action": "chasing",
            "source": "dog",
            "target": "ball",
            "keywords": ["đuổi theo", "chạy theo", "vồ", "chasing", "running after", "runs after", "pursuing"],
        },
        # Case 2: Teacher explaining mathematics
        {
            "action": "explaining",
            "source": "teacher",
            "target": "mathematics",
            "keywords": ["giảng", "giảng giải", "giải thích", "dạy", "chỉ vào", "explaining", "teaching", "pointing to"],
        },
        # Case 3: Temperature makes molecules move faster
        {
            "action": "accelerating",
            "source": "temperature",
            "target": "molecules",
            "keywords": ["làm chuyển động nhanh hơn", "tăng tốc", "khiến chuyển động", "accelerating", "speeding up", "vibrating", "makes move faster", "heating"],
        },
        # Case 4: Inflation
        {
            "action": "eroding",
            "source": "inflation",
            "target": "money",
            "keywords": ["làm giảm sức mua", "bào mòn", "tăng cao", "eroding", "devaluing", "shrinking", "inflating"],
        },
        # Astronomy: Earth orbiting Sun
        {
            "action": "orbiting",
            "source": "earth",
            "target": "sun",
            "keywords": ["quay quanh", "quay xung quanh", "orbit", "orbits", "orbiting", "revolve", "revolves"],
        },
        # Agriculture: Farmer planting tree
        {
            "action": "planting",
            "source": "farmer",
            "target": "tree",
            "keywords": ["trồng", "chăm sóc", "gieo", "plant", "planting", "tưới"],
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

        # 5. Kiểm tra nguyên tắc Show Don't Write
        sdw_violations = cls.validate_show_dont_write(scene_graph)
        for viol in sdw_violations:
            errors.append(viol)

        return SemanticValidationResult(
            is_valid=len(errors) == 0,
            missing_entities=missing_entities,
            missing_relationships=missing_relationships,
            show_dont_write_violations=sdw_violations,
            errors=errors,
            warnings=warnings,
        )

    @classmethod
    def validate_show_dont_write(cls, scene_graph: SceneGraph) -> List[str]:
        """
        Kiểm tra nguyên tắc 'Show Don't Write':
        Bảng trắng vẽ tranh minh họa trực quan, không được dùng Text làm nhân vật/vật thể chính.
        Ví dụ: Không được tạo entity text="CON KHỈ" hay text="CÂY" thay vì vẽ hình con khỉ, cây cối.
        """
        violations: List[str] = []
        if not scene_graph.entities:
            return violations

        text_entities = [
            e for e in scene_graph.entities
            if getattr(e, "visual_type", e.category) == "text" or e.category == "text"
        ]

        for ent in text_entities:
            importance = getattr(ent, "importance", "primary")
            # Nếu một thực thể chính lại là Text
            if importance == "primary":
                violations.append(
                    f"Show Don't Write violation: Thực thể chính '{ent.label}' (id={ent.id}) có visual_type='text'. "
                    f"Video whiteboard yêu cầu vẽ hình minh họa (character, object, diagram, metaphor), không viết chữ thay thế."
                )

        # Nếu toàn bộ các thực thể trong scene đều là Text (hoặc > 60% là text)
        if len(scene_graph.entities) > 1 and len(text_entities) / len(scene_graph.entities) > 0.6:
            violations.append(
                f"Show Don't Write violation: Phân cảnh có quá nhiều phần tử dạng Text ({len(text_entities)}/{len(scene_graph.entities)}). "
                f"Whiteboard video phải tập trung vào hình vẽ minh họa nét tay."
            )

        return violations

    @classmethod
    def format_repair_feedback(cls, result: SemanticValidationResult) -> str:
        """Định dạng phản hồi lỗi logic thành chỉ dẫn sửa chữa để LLM tự động hiệu chỉnh (repair loop)."""
        lines = ["Phát hiện lỗi logic trong kế hoạch thị giác vừa sinh:"]
        if result.missing_entities:
            lines.append(f"- Thiếu thực thể bắt buộc: {', '.join(result.missing_entities)}")
        if result.missing_relationships:
            lines.append(f"- Thiếu quan hệ/hành động tương tác: {'; '.join(result.missing_relationships)}")
        if result.show_dont_write_violations:
            for v in result.show_dont_write_violations:
                lines.append(f"- Vi phạm Show Don't Write: {v}")
        lines.append(
            "Yêu cầu: Hãy bổ sung đầy đủ các thực thể và mối quan hệ hành động trên dưới dạng hình vẽ minh họa (character, object, diagram, metaphor), "
            "tuyệt đối KHÔNG dùng text làm phần tử chính, và gán tọa độ canvas hợp lệ."
        )
        return "\n".join(lines)
