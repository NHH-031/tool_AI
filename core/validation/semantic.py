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
        # Characters & Animals
        "cat": ["con mèo", "chú mèo", "mèo con", "mèo", "con meo", "chu meo", "cat", "kitten", "feline"],
        "monkey": ["chú khỉ", "con khỉ", "khỉ", "con khi", "chu khi", "monkey", "ape"],
        "dog": ["con chó", "chú chó", "chó con", "chó", "con cho", "chu cho", "dog", "puppy", "canine"],
        "tiger": ["con hổ", "chú hổ", "hổ", "con cọp", "chú cọp", "cọp", "con ho", "tiger", "tigers"],
        "rabbit": ["con thỏ", "chú thỏ", "thỏ", "con tho", "rabbit", "hare", "bunny", "rabbits"],
        "bird": ["con chim", "chú chim", "chim", "chu chim", "bird", "avian"],
        "fish": ["con cá", "chú cá", "cá con", "cá", "con ca", "chu ca", "fish", "fishes"],
        "sea": ["đại dương", "biển cả", "dưới biển", "biển", "dai duong", "bien", "ocean", "sea", "underwater"],
        "teacher": ["giáo viên", "thầy giáo", "cô giáo", "giao vien", "thay giao", "co giao", "teacher", "instructor", "professor"],
        "farmer": ["người nông dân", "bác nông dân", "nông dân", "nong dan", "nguoi nong dan", "bac nong dan", "farmer", "grower", "planter"],
        "children": ["học sinh", "hoc sinh", "trẻ em", "em bé", "bọn trẻ", "khán giả", "tre em", "em be", "bon tre", "children", "kids", "crowd", "students"],
        "doctor": ["bác sĩ", "bac si", "y sĩ", "thầy thuốc", "doctor", "physician", "surgeon"],
        "patient": ["bệnh nhân", "người bệnh", "benh nhan", "patient"],
        "clinic": ["phòng khám", "bệnh viện", "phong kham", "clinic", "hospital"],
        "hiker": ["người leo núi", "vận động viên leo núi", "nguoi leo nui", "hiker", "climber", "mountaineer"],
        "engineer": ["kỹ sư", "lập trình viên", "ky su", "developer", "programmer", "engineer", "technician", "mechanic"],
        "laptop": ["máy tính xách tay", "máy tính", "may tinh", "laptop", "computer"],
        "chart": ["biểu đồ", "đồ thị", "bieu do", "chart", "analytics", "graph"],
        # Flora & Structures
        "forest": ["khu rừng", "rừng già", "rừng rậm", "rừng", "cánh rừng", "khu rung", "rung", "forest", "jungle", "woods"],
        "areca_palm": ["cây cau", "cau", "cay cau", "areca palm", "areca", "betel palm", "areca_palm"],
        "tree": ["cái cây", "thân cây", "cây cối", "cây", "cay", "cai cay", "than cay", "tree"],
        "nest": ["tổ chim", "tổ", "to chim", "nest", "bird nest"],
        "bridge": ["cây cầu", "chiếc cầu", "cầu", "cay cau", "chiec cau", "cau", "bridge"],
        "ground": ["mặt đất", "mảnh đất", "đồng ruộng", "cánh đồng", "đất", "mat dat", "manh dat", "dong ruong", "canh dong", "ground", "soil"],
        "mountain": ["núi giả", "hòn non bộ", "núi", "nui", "nui gia", "mountain", "rockery"],
        # Objects & Transport
        "banana": ["quả chuối", "trái chuối", "nải chuối", "chuối", "chuoi", "qua chuoi", "trai chuoi", "banana"],
        "ball": ["quả bóng", "trái bóng", "bóng", "bong", "qua bong", "trai bong", "ball"],
        "car": ["xe hơi", "ô tô", "chiếc xe", "xe", "xe hoi", "o to", "car", "automobile", "vehicle"],
        "machine": ["máy móc", "cỗ máy", "thiết bị", "may moc", "co may", "machine", "machinery", "equipment"],
        # Physical & Abstract Concepts
        "water": ["nước nóng", "nước sôi", "nước", "nuoc nong", "nuoc", "water", "hot water", "liquid"],
        "vapor": ["hơi nước", "bốc hơi", "hoi nuoc", "boc hoi", "vapor", "steam", "evaporation"],
        "temperature": ["nhiệt độ", "nguồn nhiệt", "lửa", "độ nóng", "nhiet do", "nguon nhiet", "lua", "do nong", "temperature", "heat", "heat_source", "burner"],
        "molecules": ["phân tử", "nguyên tử", "hạt", "phan tu", "nguyen tu", "hat", "molecules", "atoms", "particles"],
        "inflation": ["lạm phát", "mức giá", "giá cả", "lam phat", "muc gia", "gia ca", "inflation", "price", "price_tag", "prices"],
        "goods_basket": ["giỏ hàng", "hàng hóa", "gio hang", "hang hoa", "shopping cart", "goods", "basket"],
        "mathematics": ["toán học", "công thức", "bảng đen", "toán", "toan", "toan hoc", "cong thuc", "bang den", "mathematics", "math", "formula", "blackboard", "equations"],
        # Astronomy & Space Exploration
        "earth": ["trái đất", "quả đất", "địa cầu", "trai dat", "qua dat", "dia cau", "earth", "globe", "planet"],
        "sun": ["mặt trời", "thái dương", "mat troi", "thai duong", "sun", "sunlight"],
        "orbit": ["quỹ đạo", "vòng quay", "quy dao", "vong quay", "orbit", "orbiting", "ellipse"],
        "astronaut": ["phi hành gia", "nhà du hành", "người du hành vũ trụ", "astronaut", "cosmonaut", "spaceman"],
        "spacecraft": ["tàu vũ trụ", "con tàu", "phi thuyền", "tàu đổ bộ", "spacecraft", "spaceship", "lander", "rocket"],
        "mars": ["sao hỏa", "hỏa tinh", "sao hoa", "hoa tinh", "mars", "martian", "martian surface"],
      }

    # Từ điển ánh xạ hành động / quan hệ tổng quát: (action, sources, targets, keywords, relation_type)
    RELATIONSHIP_RULES: List[Dict] = [
        # Climbing interaction (cat/monkey/hiker on palm/tree/mountain)
        {
            "action": "climbing",
            "sources": ["cat", "monkey", "hiker", "animal", "character"],
            "targets": ["areca_palm", "tree", "mountain", "climbing_structure"],
            "keywords": ["trèo", "leo", "climb", "climbing", "bám", "treo"],
            "relation_type": "climbing_on",
        },
        # Chasing interaction (dog chasing ball/prey, tiger chasing rabbit)
        {
            "action": "chasing",
            "sources": ["dog", "cat", "tiger", "predator", "character"],
            "targets": ["ball", "rabbit", "prey", "target"],
            "keywords": [
                "đuổi theo", "chạy theo", "vồ", "đuổi", "rượt đuổi", "rượt", "săn",
                "chasing", "running after", "runs after", "pursuing"
            ],
            "relation_type": "chasing",
        },
        # Grabbing / Reaching
        {
            "action": "reaching",
            "sources": ["monkey", "cat", "character"],
            "targets": ["banana", "ball", "fruit"],
            "keywords": ["với", "với tới", "reach", "reaching"],
            "relation_type": "reaching",
        },
        {
            "action": "grabbing",
            "sources": ["monkey", "cat", "character"],
            "targets": ["banana", "ball", "fruit"],
            "keywords": ["cướp", "giật", "chộp", "grab", "snatch", "grabbing"],
            "relation_type": "grabbing",
        },
        {
            "action": "located_on",
            "sources": ["banana", "fruit"],
            "targets": ["tree", "areca_palm"],
            "keywords": ["trên cây", "ở trên cây", "located on", "located_on", "mọc trên cây"],
            "relation_type": "located_on",
        },
        # Education / Explanation
        {
            "action": "explaining",
            "sources": ["teacher", "character"],
            "targets": ["mathematics", "formula", "diagram"],
            "keywords": ["giảng", "giảng giải", "giải thích", "dạy", "chỉ vào", "explaining", "teaching", "pointing to"],
            "relation_type": "explaining",
        },
        # Physical phenomena
        {
            "action": "accelerating",
            "sources": ["temperature", "heat"],
            "targets": ["molecules", "particles"],
            "keywords": ["làm chuyển động nhanh hơn", "tăng tốc", "khiến chuyển động", "accelerating", "speeding up", "vibrating", "makes move faster", "heating"],
            "relation_type": "accelerating",
        },
        {
            "action": "eroding",
            "sources": ["inflation"],
            "targets": ["money", "currency"],
            "keywords": ["làm giảm sức mua", "bào mòn", "tăng cao", "eroding", "devaluing", "shrinking", "inflating"],
            "relation_type": "eroding",
        },
        # Astronomy: Orbiting
        {
            "action": "orbiting",
            "sources": ["earth", "planet"],
            "targets": ["sun", "star"],
            "keywords": ["quay quanh", "quay xung quanh", "orbit", "orbits", "orbiting", "revolve", "revolves"],
            "relation_type": "orbiting",
        },
        # Agriculture: Planting
        {
            "action": "planting",
            "sources": ["farmer", "character"],
            "targets": ["tree", "areca_palm", "seedling", "ground"],
            "keywords": ["trồng", "chăm sóc", "gieo", "plant", "planting", "tưới"],
            "relation_type": "planting",
        },
        # Movement: Flying
        {
            "action": "flying",
            "sources": ["bird"],
            "targets": ["nest", "tree", "sky"],
            "keywords": ["bay", "bay khỏi", "bay ra", "flying", "flies"],
            "relation_type": "flying_from",
        },
        # Transportation: Crossing bridge
        {
            "action": "crossing",
            "sources": ["car", "vehicle"],
            "targets": ["bridge", "road"],
            "keywords": ["chạy qua", "đi qua", "vượt qua", "crossing", "driving across"],
            "relation_type": "crossing",
        },
        # Engineering: Repairing machine
        {
            "action": "repairing",
            "sources": ["engineer", "mechanic"],
            "targets": ["machine", "equipment"],
            "keywords": ["sửa chữa", "sửa", "khắc phục", "repairing", "fixing"],
            "relation_type": "repairing",
        },
        # Physics: Evaporating
        {
            "action": "evaporating",
            "sources": ["water"],
            "targets": ["vapor"],
            "keywords": ["bốc hơi", "bay hơi", "evaporating", "evaporates"],
            "relation_type": "evaporating",
        },
        # Space exploration: Stepping / Landing on celestial body
        {
            "action": "stepping",
            "sources": ["astronaut", "character"],
            "targets": ["mars", "spacecraft", "ground"],
            "keywords": ["bước ra", "bước xuống", "đặt chân", "bước", "stepping", "steps out", "landing"],
            "relation_type": "stepping_on",
        },
    ]

    @classmethod
    def extract_required_entities(cls, text: str) -> Set[str]:
        """
        Trích xuất các thực thể bắt buộc phải xuất hiện từ văn bản thoại.
        Sử dụng thuật toán Longest-Match-First và Span-Exclusion để tránh việc
        từ ngữ ngắn hơn (vd: 'cây') nuốt mất thực thể chuyên biệt (vd: 'cây cau' hay 'cây cầu').
        """
        text_lower = text.lower()
        candidates: List[Tuple[int, int, str, str]] = []

        for entity_key, keywords in cls.ENTITY_KEYWORDS.items():
            for kw in keywords:
                pattern = r"(?:\b|^)" + re.escape(kw) + r"(?:\b|$)"
                for m in re.finditer(pattern, text_lower):
                    candidates.append((m.start(), m.end(), entity_key, kw))
                if " " in kw and kw in text_lower:
                    idx = 0
                    while True:
                        idx = text_lower.find(kw, idx)
                        if idx == -1:
                            break
                        candidates.append((idx, idx + len(kw), entity_key, kw))
                        idx += len(kw)

        # Sắp xếp ưu tiên chuỗi dài nhất trước
        candidates.sort(key=lambda c: (len(c[3]), c[1] - c[0]), reverse=True)

        occupied_spans: List[Tuple[int, int]] = []
        found: Set[str] = set()

        for start, end, entity_key, kw in candidates:
            # Kiểm tra xem span này có bị bao phủ bởi span dài hơn đã chấp nhận không
            is_subsumed = False
            for o_start, o_end in occupied_spans:
                # Nếu phần lớn span bị trùng lặp với span dài hơn
                overlap_len = max(0, min(end, o_end) - max(start, o_start))
                if overlap_len >= (end - start) * 0.7:
                    is_subsumed = True
                    break
            if not is_subsumed:
                occupied_spans.append((start, end))
                found.add(entity_key)

        return found

    @classmethod
    def extract_required_relationships(cls, text: str, present_entities: Set[str]) -> List[Tuple[str, str, str]]:
        """
        Trích xuất các mối quan hệ ngữ nghĩa bắt buộc từ câu thoại theo quy tắc tổng quát.
        Trả về danh sách (source_entity, action, target_entity).
        """
        text_lower = text.lower()
        required_rels: List[Tuple[str, str, str]] = []

        for rule in cls.RELATIONSHIP_RULES:
            sources = rule.get("sources", [rule.get("source")])
            targets = rule.get("targets", [rule.get("target")])
            act = rule["action"]

            # Tìm xem có cặp (src, tgt) nào trong present_entities khớp với rule không
            for src in sources:
                if src not in present_entities:
                    continue
                for tgt in targets:
                    if tgt not in present_entities:
                        continue
                    # Cả source và target đều xuất hiện trong câu thoại
                    matched_kw = any(kw in text_lower for kw in rule["keywords"])
                    if matched_kw:
                        rel_tuple = (src, act, tgt)
                        if rel_tuple not in required_rels:
                            required_rels.append(rel_tuple)
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
            # Kiểm tra khớp ID, nhãn, species hoặc từ đồng nghĩa
            if req_key in available_entity_ids or req_key in available_entity_labels:
                return True
            for ent in scene_graph.entities:
                if getattr(ent, "species", None) and ent.species and ent.species.lower() == req_key:
                    return True
            for kw in cls.ENTITY_KEYWORDS.get(req_key, []):
                if kw in available_entity_ids or kw in available_entity_labels:
                    return True
                # Kiểm tra substring trong nhãn (ví dụ: 'chú khỉ con' chứa 'khỉ')
                if any(kw in label for label in available_entity_labels):
                    return True
                for ent in scene_graph.entities:
                    if getattr(ent, "species", None) and ent.species and kw in ent.species.lower():
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
                        src_species = (getattr(src_ent, "species", None) or "").lower()
                        tgt_species = (getattr(tgt_ent, "species", None) or "").lower()
                        src_match = (
                            src_req in src_ent.id.lower() or src_req in src_ent.label.lower() or src_req == src_species
                            or any(kw in src_ent.label.lower() or kw in src_species for kw in cls.ENTITY_KEYWORDS.get(src_req, []))
                        )
                        tgt_match = (
                            tgt_req in tgt_ent.id.lower() or tgt_req in tgt_ent.label.lower() or tgt_req == tgt_species
                            or any(kw in tgt_ent.label.lower() or kw in tgt_species for kw in cls.ENTITY_KEYWORDS.get(tgt_req, []))
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
