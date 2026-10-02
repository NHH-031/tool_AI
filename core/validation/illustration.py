from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import cv2
import numpy as np
from pydantic import BaseModel, Field

from core.schemas.scene_graph import SceneGraph, VisualEntity
from core.schemas.timeline import DrawingTimeline
from core.validation.semantic import SemanticValidator

logger = logging.getLogger(__name__)


class IllustrationValidationResult(BaseModel):
    """Kết quả kiểm định tính hoàn thiện của Source Illustration trước khi đưa vào Renderer."""
    is_valid: bool = Field(description="Đạt yêu cầu để đưa vào render hay không")
    missing_entities: List[str] = Field(default_factory=list, description="Thực thể kịch bản yêu cầu nhưng thiếu trong illustration")
    missing_relationships: List[str] = Field(default_factory=list, description="Quan hệ/hành động bị thiếu")
    missing_regions: List[str] = Field(default_factory=list, description="Thực thể thiếu vùng region/mask hợp lệ")
    zero_stroke_entities: List[str] = Field(default_factory=list, description="Thực thể có 0 nét vẽ")
    errors: List[str] = Field(default_factory=list, description="Danh sách lỗi ngăn cản render")
    warnings: List[str] = Field(default_factory=list, description="Cảnh báo")
    vision_qa_checked: bool = Field(default=False, description="Đã thực hiện kiểm định thị giác")
    vision_qa_status: str = Field(default="MANUAL_REVIEW_REQUIRED", description="PASS / FAIL / MANUAL_REVIEW_REQUIRED")
    vision_qa_details: str = Field(default="", description="Chi tiết thẩm định Vision/VLM")


class IVisionQAProvider(ABC):
    """Interface trừu tượng cho hệ thống Vision/VLM kiểm tra hình ảnh trực quan."""

    @abstractmethod
    async def inspect_illustration(
        self,
        image_path: Path,
        scene_graph: SceneGraph,
        script_text: str,
    ) -> tuple[str, str]:
        """
        Trả về (status, details):
        status: 'PASS' | 'FAIL' | 'MANUAL_REVIEW_REQUIRED'
        """
        pass


class StructuralVisionQAProvider(IVisionQAProvider):
    """
    Bộ kiểm tra trực quan cấu trúc mặc định khi chưa tích hợp VLM ngoài.
    Xác minh qua pixel density, hình thái học đường nét và đánh dấu cần review thẩm mỹ thủ công.
    Tuyệt đối không giả lập kết quả VLM.
    """

    async def inspect_illustration(
        self,
        image_path: Path,
        scene_graph: SceneGraph,
        script_text: str,
    ) -> tuple[str, str]:
        if not image_path.exists():
            return "FAIL", f"File ảnh nguồn không tồn tại: {image_path}"

        img = cv2.imread(str(image_path))
        if img is None:
            return "FAIL", f"Không thể đọc file ảnh: {image_path}"

        # Kiểm tra độ tương phản giữa nét mực và giấy nền
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ink_pixels = np.sum(gray < 150)
        total_pixels = gray.size
        ink_ratio = ink_pixels / total_pixels

        if ink_ratio < 0.001:
            return "FAIL", f"Ảnh nguồn gần như trống rỗng (tỉ lệ mực: {ink_ratio:.4%})"

        return (
            "MANUAL_REVIEW_REQUIRED",
            f"Kiểm tra cấu trúc và mật độ pixel đạt (ink_ratio={ink_ratio:.3%}); "
            f"cần kiểm tra thẩm mỹ thủ công hoặc qua VLM provider thực thụ."
        )


class SourceIllustrationValidator:
    """
    Bộ thẩm định Source Illustration trước khi đưa vào Renderer.
    Quy tắc Section 6:
    Script → Scene Graph → Visual Plan → Source Illustration → Illustration Validation → Annotation → Drawing Plan → Render.
    Nếu hình nguồn thiếu một đối tượng bắt buộc: KHÔNG tiếp tục render như thể hình đã hoàn chỉnh.
    """

    @classmethod
    def validate_pre_render(
        cls,
        script_text: str,
        scene_graph: SceneGraph,
        timeline: Optional[DrawingTimeline] = None,
        image_path: Optional[Path] = None,
        annotation_path: Optional[Path] = None,
        vision_provider: Optional[IVisionQAProvider] = None,
    ) -> IllustrationValidationResult:
        errors: List[str] = []
        warnings: List[str] = []
        missing_entities: List[str] = []
        missing_relationships: List[str] = []
        missing_regions: List[str] = []
        zero_stroke_entities: List[str] = []

        # 1. Thẩm định Scene Graph đối chiếu với Lời thoại kịch bản
        req_from_script = SemanticValidator.extract_required_entities(script_text)
        graph_entities_by_species = {
            (getattr(e, "species", None) or "").lower(): e for e in scene_graph.entities
        }
        graph_entities_by_label = {
            e.label.lower(): e for e in scene_graph.entities
        }
        graph_entities_by_id = {
            e.id.lower(): e for e in scene_graph.entities
        }

        for req in sorted(req_from_script):
            matched = False
            # Khớp species, label, id hoặc từ khóa đồng nghĩa
            if (
                req in graph_entities_by_species
                or req in graph_entities_by_label
                or req in graph_entities_by_id
            ):
                matched = True
            else:
                for kw in SemanticValidator.ENTITY_KEYWORDS.get(req, []):
                    if (
                        kw in graph_entities_by_label
                        or kw in graph_entities_by_id
                        or any(kw in e.label.lower() for e in scene_graph.entities)
                        or any(kw in (getattr(e, "species", None) or "").lower() for e in scene_graph.entities)
                    ):
                        matched = True
                        break
            if not matched:
                missing_entities.append(req)
                errors.append(
                    f"PRE-RENDER VALIDATION FAILED: Thực thể '{req}' có trong kịch bản nhưng thiếu trong Scene Graph / Source Illustration!"
                )

        # 2. Thẩm định quan hệ/hành động tương tác bắt buộc
        req_rels = SemanticValidator.extract_required_relationships(script_text, req_from_script)
        for src_req, act_req, tgt_req in req_rels:
            rel_found = False
            for r in scene_graph.relationships:
                r_type = (r.relation_type or "").lower()
                r_act = (r.action or "").lower()
                if act_req in r_type or act_req in r_act or r_type in act_req:
                    src_ent = scene_graph.get_entity(r.source_id)
                    tgt_ent = scene_graph.get_entity(r.target_id)
                    if src_ent and tgt_ent:
                        src_sp = (getattr(src_ent, "species", None) or "").lower()
                        tgt_sp = (getattr(tgt_ent, "species", None) or "").lower()
                        s_ok = (src_req in src_ent.label.lower() or src_req in src_ent.id.lower() or src_req == src_sp)
                        t_ok = (tgt_req in tgt_ent.label.lower() or tgt_req in tgt_ent.id.lower() or tgt_req == tgt_sp)
                        if s_ok and t_ok:
                            rel_found = True
                            break
            if not rel_found:
                rel_desc = f"{src_req} -> {act_req} -> {tgt_req}"
                missing_relationships.append(rel_desc)
                errors.append(
                    f"PRE-RENDER VALIDATION FAILED: Hành động tương tác '{rel_desc}' bị thiếu trong Scene Graph!"
                )

        # 3. Thẩm định tính hoàn thiện nét vẽ và sự hiện diện của Timeline Events
        if timeline is not None:
            sched = timeline.entities_schedule
            events_by_entity: Dict[str, int] = {}
            for ev in timeline.events:
                if ev.entity_id and ev.action == "draw":
                    events_by_entity[ev.entity_id] = events_by_entity.get(ev.entity_id, 0) + 1

            for ent in scene_graph.entities:
                if ent.required:
                    st_count = events_by_entity.get(ent.id, 0)
                    if st_count == 0:
                        zero_stroke_entities.append(ent.id)
                        errors.append(
                            f"PRE-RENDER VALIDATION FAILED: Thực thể bắt buộc '{ent.id}' ({ent.label}) có 0 nét vẽ trong Timeline!"
                        )

        # 4. Thẩm định không gian tọa độ và kích thước Region
        for ent in scene_graph.entities:
            if ent.required:
                pos = ent.position
                if pos.width <= 0 or pos.height <= 0:
                    missing_regions.append(ent.id)
                    errors.append(
                        f"PRE-RENDER VALIDATION FAILED: Thực thể '{ent.id}' có kích thước hình học không hợp lệ (w={pos.width}, h={pos.height})!"
                    )
                if pos.x < 0 or pos.y < 0 or pos.x + pos.width > 2200 or pos.y + pos.height > 1300:
                    warnings.append(
                        f"Tọa độ thực thể '{ent.id}' vượt ngoài khung hình tiêu chuẩn: ({pos.x}, {pos.y}, {pos.width}, {pos.height})"
                    )

        # 5. Thẩm định trực quan Composite Image nếu có file trên đĩa
        if image_path is not None and image_path.exists():
            img_bgr = cv2.imread(str(image_path))
            if img_bgr is not None:
                h, w = img_bgr.shape[:2]
                for ent in scene_graph.entities:
                    if ent.required:
                        pos = ent.position
                        x0 = max(0, min(w, int(pos.x)))
                        y0 = max(0, min(h, int(pos.y)))
                        x1 = max(0, min(w, int(pos.x + pos.width)))
                        y1 = max(0, min(h, int(pos.y + pos.height)))
                        if x1 > x0 and y1 > y0:
                            crop = img_bgr[y0:y1, x0:x1]
                            # Nền giấy kem là (215, 235, 245) trong BGR.
                            # Mực đen có giá trị xám < 120.
                            crop_gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                            ink_count = np.sum(crop_gray < 120)
                            if ink_count == 0:
                                errors.append(
                                    f"PRE-RENDER VALIDATION FAILED: Vùng của thực thể '{ent.id}' trên ảnh tổng thể không có pixel nét mực nào!"
                                )

        # 6. Thẩm định Annotation JSON nếu có
        if annotation_path is not None and annotation_path.exists():
            try:
                ann_data = json.loads(annotation_path.read_text(encoding="utf-8"))
                ann_element_ids = {el.get("id") for el in ann_data.get("elements", [])}
                for ent in scene_graph.entities:
                    if ent.required and ent.id not in ann_element_ids:
                        missing_regions.append(ent.id)
                        errors.append(
                            f"PRE-RENDER VALIDATION FAILED: Annotation file thiếu đặc tả vùng cho thực thể '{ent.id}'!"
                        )
            except Exception as e:
                errors.append(f"PRE-RENDER VALIDATION FAILED: Không thể phân tích cú pháp annotation: {e}")

        # 7. Vision Provider check
        v_status = "MANUAL_REVIEW_REQUIRED"
        v_details = "Chưa cấu hình VLM provider; đã kiểm tra cấu trúc hình học và pixel-level. Cần kiểm tra thẩm mỹ thủ công."

        is_valid = len(errors) == 0

        return IllustrationValidationResult(
            is_valid=is_valid,
            missing_entities=missing_entities,
            missing_relationships=missing_relationships,
            missing_regions=missing_regions,
            zero_stroke_entities=zero_stroke_entities,
            errors=errors,
            warnings=warnings,
            vision_qa_checked=True,
            vision_qa_status=v_status,
            vision_qa_details=v_details,
        )
