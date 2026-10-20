"""
Auto-Segment: Tự động phân tách và gom nhóm các phân vùng ngữ nghĩa (Multi-Region Reveal)
cho hoạt họa bảng trắng whiteboard. Thay vì quét 1 vùng toàn màn hình, thuật toán chia thành
2-3 vùng hợp lý (Bối cảnh/Nền -> Nhân vật/Chủ thể chính -> Chi tiết phụ) để bàn tay vẽ tuần tự,
tạo cảm giác sinh động và tự nhiên như họa sĩ thực thụ.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RegionBox(BaseModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class RevealPlan(BaseModel):
    direction: str = "left_to_right"
    startMs: int = Field(ge=0)
    durationMs: int = Field(gt=0)
    maskPaddingPx: int = 20
    protectedRegions: List[Dict[str, int]] = Field(default_factory=list)


class HandPath(BaseModel):
    start: List[int]
    end: List[int]


class SceneElementSchema(BaseModel):
    id: str
    label: str
    sequence: int
    narrativeRole: str
    type: str
    region: Dict[str, int]
    reveal: Dict[str, Any]
    handPath: Dict[str, List[int]]


def _detect_ink_contours(
    img_bgr: np.ndarray,
    min_area: int = 40,
) -> List[Tuple[int, int, int, int, float, Tuple[float, float]]]:
    """
    Phát hiện các nét vẽ mực (ink strokes) trên nền giấy kem.
    Trả về danh sách (x, y, w, h, area, (cx, cy)) cho mỗi contour hợp lệ.
    """
    h, w = img_bgr.shape[:2]
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # Nét vẽ đen/mực có giá trị xám thấp hơn giấy kem (~240)
    _, ink_binary = cv2.threshold(gray, 215, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(ink_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    valid_boxes = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue
        bx, by, bw, bh = cv2.boundingRect(cnt)
        M = cv2.moments(cnt)
        if M["m00"] > 0:
            cx = M["m10"] / M["m00"]
            cy = M["m01"] / M["m00"]
        else:
            cx = bx + bw / 2
            cy = by + bh / 2
        valid_boxes.append((bx, by, bw, bh, float(area), (float(cx), float(cy))))

    return valid_boxes


def auto_segment_image(
    scene_id: str,
    image_path: Optional[Path],
    duration_ms: int,
    aspect_ratio: str = "16:9",
    target_regions: int = 3,
) -> Dict[str, Any]:
    """
    Phân tích cấu trúc hình vẽ và tạo danh sách elements với các phân vùng vẽ theo ngữ nghĩa:
    1. Bối cảnh / Khung nền (Background / Scene Setup)
    2. Chủ thể chính / Nhân vật trung tâm (Main Character / Focal Subject)
    3. Chi tiết phụ & Hoàn thiện (Fine Details / Accents)
    """
    img = None
    if image_path and Path(image_path).exists():
        try:
            img = cv2.imread(str(image_path))
        except Exception as e:
            logger.warning(f"[auto_segment_image] Không thể nạp ảnh {image_path}: {e}")

    if img is not None:
        canvas_h, canvas_w = img.shape[:2]
    else:
        canvas_w, canvas_h = (720, 1280) if aspect_ratio == "9:16" else (1280, 720)

    # Thời lượng vẽ thực tế: 85% thời lượng thoại
    draw_total_ms = max(2000, int(round(duration_ms * 0.85)))

    if aspect_ratio == "9:16" or canvas_h > canvas_w:
        fallback_hand_start = [int(canvas_w * 0.25), int(canvas_h * 0.18)]
        fallback_hand_end = [int(canvas_w * 0.75), int(canvas_h * 0.82)]
    else:
        fallback_hand_start = [int(canvas_w * 0.2), int(canvas_h * 0.25)]
        fallback_hand_end = [int(canvas_w * 0.85), int(canvas_h * 0.75)]

    # Fallback mặc định 1 element nếu không có ảnh hoặc ảnh trống
    fallback_result = {
        "sceneId": scene_id,
        "canvas": {"width": canvas_w, "height": canvas_h},
        "storyBasis": "",
        "sceneDurationMs": duration_ms,
        "elements": [
            {
                "id": f"{scene_id}_main",
                "label": "main_artwork",
                "sequence": 1,
                "narrativeRole": "primary",
                "type": "character",
                "region": {"x": 0, "y": 0, "width": canvas_w, "height": canvas_h},
                "reveal": {
                    "direction": "left_to_right",
                    "startMs": 100,
                    "durationMs": draw_total_ms,
                    "maskPaddingPx": 20,
                    "protectedRegions": [],
                },
                "handPath": {
                    "start": fallback_hand_start,
                    "end": fallback_hand_end,
                },
            }
        ],
    }

    if img is None:
        return fallback_result

    # 1. Phát hiện các nét vẽ mực
    boxes = _detect_ink_contours(img, min_area=35)
    if len(boxes) < 2:
        return fallback_result

    # 2. Phân loại theo diện tích và vị trí không gian
    # Điểm trung tâm màn hình
    center_x, center_y = canvas_w / 2.0, canvas_h / 2.0
    max_dist = np.hypot(center_x, center_y)

    scored_boxes = []
    for b in boxes:
        bx, by, bw, bh, area, (cx, cy) = b
        # Độ lệch tâm [0..1]
        dist_from_center = np.hypot(cx - center_x, cy - center_y) / max_dist
        # Điểm ưu tiên chủ thể: diện tích lớn và nằm gần vùng trung tâm (0.15 - 0.85)
        centrality_score = area * (1.2 - dist_from_center)
        scored_boxes.append((b, centrality_score, dist_from_center))

    # Sắp xếp các cụm nét vẽ
    scored_boxes.sort(key=lambda item: item[1], reverse=True)

    # Gom các box thành 3 nhóm ngữ nghĩa:
    # - Group 1: Background / Vùng ngoại vi hoặc trên cao (Bối cảnh, mây, cây, mặt trời, khung nền)
    # - Group 2: Main Subject / Khối trung tâm lớn nhất (Nhân vật, đối tượng chính)
    # - Group 3: Details / Nét chi tiết nhỏ, phụ kiện
    group_bg: List[Tuple[int, int, int, int]] = []
    group_main: List[Tuple[int, int, int, int]] = []
    group_detail: List[Tuple[int, int, int, int]] = []

    # Chủ thể chính: 40% khối lượng nét có điểm centrality cao nhất
    main_threshold = max(2, int(len(scored_boxes) * 0.45))
    for idx, (b, score, dist) in enumerate(scored_boxes):
        bx, by, bw, bh, area, (cx, cy) = b
        box_tuple = (bx, by, bw, bh)
        if idx < main_threshold and dist < 0.65:
            group_main.append(box_tuple)
        elif dist >= 0.5 or cy < canvas_h * 0.35:
            group_bg.append(box_tuple)
        else:
            group_detail.append(box_tuple)

    # Nếu một trong các nhóm bị rỗng, cân bằng lại hợp lý
    if not group_main and scored_boxes:
        group_main.append(scored_boxes[0][0][:4])
    if not group_bg and len(group_main) > 1:
        group_bg.append(group_main.pop())
    if not group_detail and len(group_main) > 2:
        group_detail.append(group_main.pop())

    # Tính toán bounding box cho từng nhóm có đệm (padding) an toàn
    def compute_bounding_rect(box_list: List[Tuple[int, int, int, int]], default_rect: Tuple[int, int, int, int]) -> Dict[str, int]:
        if not box_list:
            return {"x": default_rect[0], "y": default_rect[1], "width": default_rect[2], "height": default_rect[3]}
        x_min = min(b[0] for b in box_list)
        y_min = min(b[1] for b in box_list)
        x_max = max(b[0] + b[2] for b in box_list)
        y_max = max(b[1] + b[3] for b in box_list)

        # Mở rộng nhẹ vùng vẽ để không bị lẹm nét
        pad_x = int(canvas_w * 0.04)
        pad_y = int(canvas_h * 0.04)
        x0 = max(0, x_min - pad_x)
        y0 = max(0, y_min - pad_y)
        x1 = min(canvas_w, x_max + pad_x)
        y1 = min(canvas_h, y_max + pad_y)
        return {"x": x0, "y": y0, "width": max(60, x1 - x0), "height": max(60, y1 - y0)}

    region_bg = compute_bounding_rect(
        group_bg,
        (0, 0, canvas_w, int(canvas_h * 0.55)),
    )
    region_main = compute_bounding_rect(
        group_main,
        (int(canvas_w * 0.15), int(canvas_h * 0.2), int(canvas_w * 0.7), int(canvas_h * 0.65)),
    )
    region_detail = compute_bounding_rect(
        group_detail,
        (int(canvas_w * 0.25), int(canvas_h * 0.35), int(canvas_w * 0.5), int(canvas_h * 0.5)),
    )

    # 3. Phân bổ thời gian diễn hoạt (Timeline Allocation)
    # Tổng thời lượng chia theo tỷ lệ:
    # Cảnh nền: 28% -> Nhân vật chính: 46% -> Chi tiết phụ: 26%
    t_bg_ms = max(600, int(draw_total_ms * 0.28))
    t_main_ms = max(900, int(draw_total_ms * 0.46))
    t_detail_ms = max(500, draw_total_ms - t_bg_ms - t_main_ms)

    start_bg = 100
    start_main = start_bg + t_bg_ms
    start_detail = start_main + t_main_ms

    # Bàn tay vẽ điều chỉnh theo tỷ lệ khung hình và từng vùng
    def make_handpath(rect: Dict[str, int]) -> Dict[str, List[int]]:
        rx, ry, rw, rh = rect["x"], rect["y"], rect["width"], rect["height"]
        return {
            "start": [int(rx + rw * 0.2), int(ry + rh * 0.25)],
            "end": [int(rx + rw * 0.82), int(ry + rh * 0.78)],
        }

    # Bọc các element chuẩn theo thứ tự kể chuyện
    elements = [
        {
            "id": f"{scene_id}_bg",
            "label": "background_setup",
            "sequence": 1,
            "narrativeRole": "background",
            "type": "background",
            "region": region_bg,
            "reveal": {
                "direction": "left_to_right",
                "startMs": start_bg,
                "durationMs": t_bg_ms,
                "maskPaddingPx": 24,
                "protectedRegions": [region_main],
            },
            "handPath": make_handpath(region_bg),
        },
        {
            "id": f"{scene_id}_character",
            "label": "main_character",
            "sequence": 2,
            "narrativeRole": "primary",
            "type": "character",
            "region": region_main,
            "reveal": {
                "direction": "left_to_right",
                "startMs": start_main,
                "durationMs": t_main_ms,
                "maskPaddingPx": 24,
                "protectedRegions": [region_detail],
            },
            "handPath": make_handpath(region_main),
        },
        {
            "id": f"{scene_id}_details",
            "label": "fine_details",
            "sequence": 3,
            "narrativeRole": "secondary",
            "type": "prop",
            "region": region_detail,
            "reveal": {
                "direction": "left_to_right",
                "startMs": start_detail,
                "durationMs": t_detail_ms,
                "maskPaddingPx": 20,
                "protectedRegions": [],
            },
            "handPath": make_handpath(region_detail),
        },
    ]

    return {
        "sceneId": scene_id,
        "canvas": {"width": canvas_w, "height": canvas_h},
        "storyBasis": "",
        "sceneDurationMs": duration_ms,
        "elements": elements,
    }
