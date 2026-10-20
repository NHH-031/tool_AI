"""
Text Handwriter Engine (Phase 9 - Task 9.3).
Chuyển đổi chuỗi văn bản (tiêu đề, công thức, tóm tắt) thành chuỗi nét vẽ vector tuần tự (DrawingStroke)
và file đặc tả phân cảnh (AnnotationSchema) để bàn tay cầm bút viết từng ký tự từ trái sang phải trên bảng trắng.
"""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from core.schemas.annotation import (
    AnnotationSchema,
    CanvasSchema,
    ElementSchema,
    HandPathSchema,
    RegionSchema,
    RevealSchema,
)
from core.schemas.drawing import DrawingStroke
from core.drawing.vectorizer import (
    chaikin_smooth,
    compute_polyline_length,
    ramer_douglas_peucker,
)

logger = logging.getLogger(__name__)


def morphological_skeleton(binary_mask: np.ndarray) -> np.ndarray:
    """Trích xuất xương nét (skeleton) bằng phép toán hình thái học OpenCV chuẩn."""
    skel = np.zeros(binary_mask.shape, np.uint8)
    element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    temp = binary_mask.copy()
    while True:
        eroded = cv2.erode(temp, element)
        opened = cv2.morphologyEx(eroded, cv2.MORPH_OPEN, element)
        sub = cv2.subtract(eroded, opened)
        skel = cv2.bitwise_or(skel, sub)
        temp = eroded.copy()
        if cv2.countNonZero(temp) == 0:
            break
    return skel


class TextHandwriter:
    """
    Bộ hoạt họa chữ viết tay:
    Tự động biến đổi ký tự / dòng chữ thành quỹ đạo di chuyển của bàn tay và ngòi bút theo thời gian thực.
    """

    FONT_SEARCH_PATHS = [
        Path(__file__).resolve().parent.parent.parent / "assets" / "fonts",
        Path("C:/Windows/Fonts"),
    ]

    def __init__(
        self,
        default_font_family: str = "Patrick Hand",
        default_font_size: int = 56,
        canvas_size: Tuple[int, int] = (1280, 720),
        bg_color_hex: str = "#F5EBD7",
    ):
        self.default_font_family = default_font_family
        self.default_font_size = default_font_size
        self.canvas_size = canvas_size  # (width, height)
        self.bg_color_hex = bg_color_hex

    def resolve_font(
        self, font_family: Optional[str] = None, font_size: Optional[int] = None
    ) -> ImageFont.FreeTypeFont:
        """Tìm nạp font TrueType phù hợp (hỗ trợ font viết tay & font hiện đại)."""
        family = (font_family or self.default_font_family or "").strip().lower()
        size = font_size or self.default_font_size

        candidates: List[Path] = []
        for d in self.FONT_SEARCH_PATHS:
            if not d.exists():
                continue
            if "patrick" in family:
                candidates.append(d / "PatrickHand-Regular.ttf")
            elif "mali" in family:
                candidates.append(d / "Mali-Regular.ttf")
            elif "caveat" in family:
                candidates.append(d / "Caveat-Regular.ttf")

        # Windows handwritten fallbacks
        if any(k in family for k in ["patrick", "mali", "caveat", "itim", "comic", "hand", "print"]):
            candidates.extend([
                Path("C:/Windows/Fonts/comicbd.ttf"),
                Path("C:/Windows/Fonts/comic.ttf"),
                Path("C:/Windows/Fonts/segoepr.ttf"),
                Path("C:/Windows/Fonts/inkfree.ttf"),
            ])

        # Modern fallbacks
        candidates.extend([
            Path("C:/Windows/Fonts/segoeuib.ttf"),
            Path("C:/Windows/Fonts/segoeui.ttf"),
            Path("C:/Windows/Fonts/arialbd.ttf"),
            Path("C:/Windows/Fonts/arial.ttf"),
        ])

        for c in candidates:
            if c.exists():
                try:
                    return ImageFont.truetype(str(c), size)
                except Exception:
                    continue

        try:
            return ImageFont.load_default()
        except Exception:
            return None

    def _hex_to_bgr(self, h: str) -> Tuple[int, int, int]:
        clean = (h or "").lstrip("#")
        if len(clean) == 6:
            try:
                r, g, b = int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16)
                return (b, g, r)
            except ValueError:
                pass
        return (26, 26, 26)

    def _hex_to_rgb(self, h: str) -> Tuple[int, int, int]:
        b, g, r = self._hex_to_bgr(h)
        return (r, g, b)

    def generate_handwritten_strokes(
        self,
        text: str,
        font_family: Optional[str] = None,
        font_size: Optional[int] = None,
        color_hex: str = "#1A1A1A",
        stroke_width: float = 4.5,
        total_duration_sec: float = 3.5,
        origin: Optional[Tuple[int, int]] = None,
        align: str = "center",
    ) -> List[DrawingStroke]:
        """
        Trích xuất danh sách các DrawingStroke theo thứ tự viết tay từ trái sang phải,
        từ trên xuống dưới của từng ký tự.
        """
        font = self.resolve_font(font_family, font_size)
        canvas_w, canvas_h = self.canvas_size

        # Khởi tạo canvas ảo
        dummy_img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(dummy_img)

        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if not lines:
            lines = [text.strip()]

        # Tính toán kích thước các dòng
        line_metrics = []
        total_text_h = 0
        line_spacing = 14

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            lw = bbox[2] - bbox[0]
            lh = bbox[3] - bbox[1]
            line_metrics.append((line, lw, lh))
            total_text_h += lh

        total_text_h += line_spacing * (len(lines) - 1)

        # Xác định vị trí xuất phát
        if origin:
            start_x, start_y = origin
        else:
            start_y = max(40, (canvas_h - total_text_h) // 2)

        strokes: List[DrawingStroke] = []
        global_stroke_idx = 1
        current_y = start_y

        # Duyệt qua từng dòng và từng ký tự
        for line, lw, lh in line_metrics:
            if origin:
                line_x = start_x
            elif align == "center":
                line_x = max(30, (canvas_w - lw) // 2)
            else:
                line_x = 80

            curr_char_x = line_x

            # Duyệt từng từ hoặc từng ký tự
            words = line.split(" ")
            space_w = draw.textbbox((0, 0), " ", font=font)[2]

            for word_idx, word in enumerate(words):
                if not word:
                    curr_char_x += space_w
                    continue

                for char in word:
                    c_bbox = draw.textbbox((0, 0), char, font=font)
                    cw = max(10, c_bbox[2] - c_bbox[0])
                    ch = max(10, c_bbox[3] - c_bbox[1])

                    # Vẽ ký tự lên mask riêng biệt để trích xuất xương nét
                    char_pad = 12
                    c_img = Image.new("L", (cw + char_pad * 2, ch + char_pad * 2), 0)
                    c_draw = ImageDraw.Draw(c_img)
                    c_draw.text((char_pad - c_bbox[0], char_pad - c_bbox[1]), char, font=font, fill=255)

                    c_arr = np.array(c_img, dtype=np.uint8)
                    skel = morphological_skeleton(c_arr)

                    # Trích xuất các điểm trên xương nét
                    pts_y, pts_x = np.nonzero(skel)

                    if len(pts_x) >= 4:
                        # Gom nhóm các điểm theo chiều từ trái qua phải, từ trên xuống dưới
                        char_points: List[Tuple[float, float]] = []
                        # Sắp xếp điểm theo logic viết chữ: ưu tiên tọa độ x (trái sang phải) và y (trên xuống dưới)
                        sorted_indices = sorted(range(len(pts_x)), key=lambda i: (pts_x[i] // 4, pts_y[i]))
                        
                        # Lấy mẫu các điểm nối tiếp
                        sampled_idx = sorted_indices[:: max(1, len(sorted_indices) // 16)]
                        for idx in sampled_idx:
                            gx = float(curr_char_x + (pts_x[idx] - char_pad))
                            gy = float(current_y + (pts_y[idx] - char_pad))
                            char_points.append((gx, gy))

                        # Làm mịn đường cong nét viết
                        if len(char_points) >= 3:
                            char_points = ramer_douglas_peucker(char_points, epsilon=1.5)
                            char_points = chaikin_smooth(char_points, iterations=1)
                    else:
                        # Fallback nét vẽ tự nhiên theo khung bao ký tự nếu không tìm được điểm xương nét
                        p0 = (float(curr_char_x), float(current_y))
                        p1 = (float(curr_char_x + cw * 0.5), float(current_y + ch))
                        p2 = (float(curr_char_x + cw), float(current_y))
                        char_points = [p0, p1, p2]

                    poly_len = compute_polyline_length(char_points)
                    stroke = DrawingStroke(
                        id=f"handwrite_stroke_{global_stroke_idx:04d}",
                        asset_id="handwritten_text",
                        order=global_stroke_idx,
                        duration=0.1,  # Tạm thời
                        start_point=char_points[0],
                        end_point=char_points[-1],
                        semantic_purpose="handwritten_character",
                        points=char_points,
                        length=poly_len,
                        color_hex=color_hex,
                        stroke_width=stroke_width,
                        path_mode="vector",
                    )
                    strokes.append(stroke)
                    global_stroke_idx += 1
                    curr_char_x += cw + 2

                curr_char_x += space_w

            current_y += lh + line_spacing

        # Phân bổ thời lượng đều đặn theo chiều dài nét vẽ
        total_length = sum(s.length for s in strokes) or 1.0
        for s in strokes:
            s.duration = max(0.04, round((s.length / total_length) * total_duration_sec, 3))

        logger.info(
            f"[TextHandwriter] Đã sinh {len(strokes)} nét vẽ chữ viết tay cho văn bản: '{text[:30]}...'"
        )
        return strokes

    def create_handwritten_scene_artifacts(
        self,
        scene_id: str,
        text: str,
        output_dir: Path,
        font_family: Optional[str] = None,
        font_size: Optional[int] = None,
        color_hex: str = "#1A1A1A",
        duration_ms: int = 4000,
        align: str = "center",
    ) -> Tuple[Path, Path]:
        """
        Sinh trọn bộ artifacts phân cảnh cho Whiteboard Engine:
        1. {scene_id}.png: Ảnh chữ viết hoàn chỉnh trên nền giấy màu kem (#F5EBD7).
        2. {scene_id}.annotation.json: File đặc tả các vùng chữ theo thứ tự vẽ tuần tự từ trái sang phải.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        image_path = output_dir / f"{scene_id}.png"
        annotation_path = output_dir / f"{scene_id}.annotation.json"

        canvas_w, canvas_h = self.canvas_size
        font = self.resolve_font(font_family, font_size)

        # 1. Vẽ ảnh hoàn chỉnh lên canvas nền kem
        bg_rgb = self._hex_to_rgb(self.bg_color_hex)
        text_rgb = self._hex_to_rgb(color_hex)

        img = Image.new("RGB", (canvas_w, canvas_h), bg_rgb)
        draw = ImageDraw.Draw(img)

        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if not lines:
            lines = [text.strip()]

        line_metrics = []
        total_text_h = 0
        line_spacing = 16

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            lw = bbox[2] - bbox[0]
            lh = bbox[3] - bbox[1]
            line_metrics.append((line, lw, lh))
            total_text_h += lh

        total_text_h += line_spacing * (len(lines) - 1)
        start_y = max(50, (canvas_h - total_text_h) // 2)

        elements: List[ElementSchema] = []
        current_y = start_y
        word_sequence = 1

        # Đếm tổng số từ để phân bổ thời gian reveal
        all_words_count = sum(len(line.split(" ")) for line in lines) or 1
        per_word_ms = max(150, int((duration_ms * 0.85) / all_words_count))

        space_w = draw.textbbox((0, 0), " ", font=font)[2]

        for line, lw, lh in line_metrics:
            if align == "center":
                line_x = max(40, (canvas_w - lw) // 2)
            else:
                line_x = 80

            curr_x = line_x
            words = line.split(" ")

            for w in words:
                if not w:
                    curr_x += space_w
                    continue

                w_bbox = draw.textbbox((0, 0), w, font=font)
                w_w = max(12, w_bbox[2] - w_bbox[0])
                w_h = max(12, w_bbox[3] - w_bbox[1])

                # Vẽ từ lên canvas
                draw.text(
                    (curr_x, current_y - w_bbox[1]),
                    w,
                    font=font,
                    fill=text_rgb,
                )

                # Tạo ElementSchema tương ứng với từ này
                el_start_ms = (word_sequence - 1) * per_word_ms
                reg_pad = 8
                region = RegionSchema(
                    x=max(0, curr_x - reg_pad),
                    y=max(0, current_y - reg_pad),
                    width=w_w + reg_pad * 2,
                    height=w_h + reg_pad * 2,
                )

                elem = ElementSchema(
                    id=f"{scene_id}_word_{word_sequence}",
                    label=w,
                    sequence=word_sequence,
                    narrativeRole="title_text",
                    subtitle="",
                    type="text",
                    region=region,
                    reveal=RevealSchema(
                        direction="left_to_right",
                        startMs=el_start_ms,
                        durationMs=per_word_ms,
                        maskPaddingPx=10,
                    ),
                    handPath=HandPathSchema(
                        start=(curr_x, current_y + int(w_h * 0.5)),
                        end=(curr_x + w_w, current_y + int(w_h * 0.5)),
                        easing="easeInOut",
                    ),
                )
                elements.append(elem)

                curr_x += w_w + space_w
                word_sequence += 1

            current_y += lh + line_spacing

        # Lưu ảnh PNG
        img.save(str(image_path), format="PNG")

        # Tạo AnnotationSchema
        annotation = AnnotationSchema(
            sceneId=scene_id,
            canvas=CanvasSchema(width=canvas_w, height=canvas_h),
            storyBasis=text[:80],
            sceneDurationMs=duration_ms,
            elements=elements,
        )

        annotation_path.write_text(
            annotation.model_dump_json(indent=2, by_alias=True),
            encoding="utf-8",
        )

        logger.info(
            f"[TextHandwriter] Đã xuất {len(elements)} phần tử chữ viết tay vào: {annotation_path.name}"
        )
        return (image_path, annotation_path)
