from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np

from core.schemas.drawing import DrawingStroke


@dataclass
class VectorStrokeSegment:
    """Đặc tả một nét vẽ vector trích xuất từ hình ảnh raster."""
    id: str
    points: List[Tuple[float, float]]
    length: float
    category: str = "outline"  # "outline", "structure", "detail", "shading"
    stroke_width: float = 3.0
    color_hex: str = "#1A1A1A"
    is_closed: bool = False
    bbox: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)  # min_x, min_y, max_x, max_y


def ramer_douglas_peucker(points: List[Tuple[float, float]], epsilon: float) -> List[Tuple[float, float]]:
    """
    Thuật toán Ramer-Douglas-Peucker (RDP) rút gọn điểm polyline,
    loại bỏ các điểm đồng quy dư thừa mà vẫn giữ nguyên hình dạng đường cong.
    """
    if len(points) < 3:
        return points

    dmax = 0.0
    index = 0
    p1 = np.array(points[0], dtype=np.float32)
    p2 = np.array(points[-1], dtype=np.float32)
    line_vec = p2 - p1
    line_len = np.linalg.norm(line_vec)

    for i in range(1, len(points) - 1):
        p = np.array(points[i], dtype=np.float32)
        if line_len < 1e-6:
            dist = float(np.linalg.norm(p - p1))
        else:
            # Khoảng cách từ điểm p đến đoạn thẳng p1-p2
            cross_prod = float(line_vec[0] * (p1[1] - p[1]) - line_vec[1] * (p1[0] - p[0]))
            dist = float(abs(cross_prod) / line_len)

        if dist > dmax:
            index = i
            dmax = dist

    if dmax > epsilon:
        rec_results1 = ramer_douglas_peucker(points[: index + 1], epsilon)
        rec_results2 = ramer_douglas_peucker(points[index:], epsilon)
        return rec_results1[:-1] + rec_results2
    else:
        return [points[0], points[-1]]


def chaikin_smooth(points: List[Tuple[float, float]], iterations: int = 2) -> List[Tuple[float, float]]:
    """
    Thuật toán cắt góc Chaikin (Chaikin's corner-cutting algorithm) làm mềm mượt
    các góc gấp khúc thành đường cong Bezier tự nhiên.
    """
    if len(points) < 3:
        return points

    current = points
    for _ in range(iterations):
        smoothed: List[Tuple[float, float]] = [current[0]]
        for i in range(len(current) - 1):
            p0 = current[i]
            p1 = current[i + 1]
            q = (0.75 * p0[0] + 0.25 * p1[0], 0.75 * p0[1] + 0.25 * p1[1])
            r = (0.25 * p0[0] + 0.75 * p1[0], 0.25 * p0[1] + 0.75 * p1[1])
            smoothed.extend([q, r])
        smoothed.append(current[-1])
        current = smoothed
    return current


def compute_polyline_length(points: List[Tuple[float, float]]) -> float:
    """Tính tổng chiều dài đoạn polyline."""
    if len(points) < 2:
        return 0.0
    total = 0.0
    for i in range(len(points) - 1):
        dx = points[i + 1][0] - points[i][0]
        dy = points[i + 1][1] - points[i][1]
        total += math.hypot(dx, dy)
    return total


class BitmapStrokeVectorizer:
    """
    Bộ chuyển đổi Vector nét vẽ (Vector Stroke Engine):
    Trích xuất từ hình ảnh raster / line-art thành các đường cong vector Bezier liên tục,
    phân loại ngữ nghĩa (outline, structure, detail, shading) và tối ưu hóa để vẽ tay chân thực.
    """

    def __init__(
        self,
        ink_threshold: int = 145,
        min_stroke_length: float = 6.0,
        rdp_epsilon: float = 1.2,
        smooth_iterations: int = 2,
    ):
        self.ink_threshold = ink_threshold
        self.min_stroke_length = min_stroke_length
        self.rdp_epsilon = rdp_epsilon
        self.smooth_iterations = smooth_iterations

    def vectorize_image(
        self,
        image_or_path: Union[str, Path, np.ndarray],
        mask: Optional[np.ndarray] = None,
        asset_id: str = "vector_artwork",
    ) -> List[VectorStrokeSegment]:
        """
        Trích xuất danh sách các nét vẽ vector từ ảnh.
        """
        if isinstance(image_or_path, (str, Path)):
            img = cv2.imread(str(image_or_path))
            if img is None:
                raise ValueError(f"Không thể đọc ảnh: {image_or_path}")
        else:
            img = image_or_path

        # 1. Tiền xử lý ảnh grayscale & thresholding
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()

        # Áp dụng mask nếu có
        if mask is not None:
            mask_bool = mask > 50
        else:
            mask_bool = np.ones_like(gray, dtype=bool)

        # Trích xuất các pixel mực đậm
        binary_ink = (gray < self.ink_threshold) & mask_bool

        if not np.any(binary_ink):
            return []

        # 2. Skeletonization (làm mảnh nét vẽ thành đường 1-pixel)
        skeleton = self._skeletonize(binary_ink)

        # 3. Trích xuất chuỗi nét vẽ 8-lân cận
        raw_strokes = self._trace_skeleton_paths(skeleton)

        # 4. Làm mượt và phân loại nét vẽ
        segments: List[VectorStrokeSegment] = []
        for idx, stroke_pts in enumerate(raw_strokes):
            if len(stroke_pts) < 2:
                continue

            # Rút gọn điểm dư thừa RDP
            simplified = ramer_douglas_peucker(stroke_pts, self.rdp_epsilon)
            if len(simplified) < 2:
                continue

            # Làm mượt đường cong Chaikin
            smooth_pts = chaikin_smooth(simplified, self.smooth_iterations)
            length = compute_polyline_length(smooth_pts)

            if length < self.min_stroke_length:
                continue

            # Tính Bounding Box
            xs = [p[0] for p in smooth_pts]
            ys = [p[1] for p in smooth_pts]
            bbox = (min(xs), min(ys), max(xs), max(ys))

            # Phân loại nét vẽ dựa trên độ dài và độ cong
            category = self._classify_stroke(length, bbox, smooth_pts)

            # Ước lượng độ dày nét vẽ ban đầu
            stroke_width = self._estimate_stroke_width(gray, smooth_pts)

            seg = VectorStrokeSegment(
                id=f"{asset_id}_stroke_{idx+1:04d}",
                points=[(round(x, 2), round(y, 2)) for x, y in smooth_pts],
                length=round(length, 2),
                category=category,
                stroke_width=round(stroke_width, 1),
                color_hex="#1A1A1A",
                is_closed=math.hypot(smooth_pts[0][0] - smooth_pts[-1][0], smooth_pts[0][1] - smooth_pts[-1][1]) < 6.0,
                bbox=bbox,
            )
            segments.append(seg)

        return segments

    def to_drawing_strokes(
        self,
        segments: List[VectorStrokeSegment],
        asset_id: str = "vector_art",
    ) -> List[DrawingStroke]:
        """Chuyển đổi VectorStrokeSegment sang mô hình DrawingStroke chuẩn của hệ thống."""
        strokes: List[DrawingStroke] = []
        for idx, seg in enumerate(segments, start=1):
            pts = seg.points
            strokes.append(
                DrawingStroke(
                    id=seg.id,
                    asset_id=asset_id,
                    path="",  # Sẽ được sinh tự động nếu cần
                    order=idx,
                    duration=max(0.04, round(seg.length / 450.0, 3)),
                    start_point=pts[0],
                    end_point=pts[-1],
                    semantic_purpose=seg.category,
                    points=pts,
                    length=seg.length,
                    color_hex=seg.color_hex,
                    stroke_width=seg.stroke_width,
                    path_mode="skeleton",
                )
            )
        return strokes

    def _skeletonize(self, binary_img: np.ndarray) -> np.ndarray:
        """
        Thực hiện skeletonization bằng kỹ thuật morphological thinning tối ưu hóa bằng NumPy/OpenCV.
        """
        u8_img = (binary_img.astype(np.uint8)) * 255
        # Sử dụng cv2.ximgproc nếu có, hoặc phương pháp morphological thinning nhanh
        try:
            if hasattr(cv2, "ximgproc") and hasattr(cv2.ximgproc, "thinning"):
                return cv2.ximgproc.thinning(u8_img, thinningType=cv2.ximgproc.THINNING_ZHANGSUEN) > 0
        except Exception:
            pass

        # Thuật toán Morphological Thinning tương thích cao
        skeleton = np.zeros_like(u8_img)
        element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
        temp = u8_img.copy()

        while True:
            eroded = cv2.erode(temp, element)
            opened = cv2.morphologyEx(eroded, cv2.MORPH_OPEN, element)
            subset = cv2.subtract(eroded, opened)
            skeleton = cv2.bitwise_or(skeleton, subset)
            temp = eroded.copy()
            if cv2.countNonZero(temp) == 0:
                break

        # Nếu morph thinning quá thưa, bổ sung đường biên Canny mảnh
        if cv2.countNonZero(skeleton) < 15:
            edges = cv2.Canny(u8_img, 50, 150)
            skeleton = cv2.bitwise_or(skeleton, edges)

        return skeleton > 0

    def _trace_skeleton_paths(self, skeleton: np.ndarray) -> List[List[Tuple[float, float]]]:
        """
        Duyệt và gom các pixel khung xương 8-lân cận thành danh sách các đường nét liên tục.
        """
        h, w = skeleton.shape
        visited = np.zeros((h, w), dtype=bool)
        ys, xs = np.where(skeleton)
        pixel_set = set(zip(xs, ys))

        # Tìm các điểm đầu mút (endpoints có đúng 1 láng giềng)
        endpoints = []
        for px, py in pixel_set:
            neighbors = 0
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    if (px + dx, py + dy) in pixel_set:
                        neighbors += 1
            if neighbors <= 1:
                endpoints.append((px, py))

        paths: List[List[Tuple[float, float]]] = []

        # 1. Bắt đầu từ các điểm đầu mút để đi trọn vẹn nét vẽ
        for start_pt in endpoints:
            if start_pt not in pixel_set or visited[start_pt[1], start_pt[0]]:
                continue

            current_path = [start_pt]
            visited[start_pt[1], start_pt[0]] = True
            curr = start_pt

            while True:
                next_pt = None
                # Tìm láng giềng chưa thăm gần nhất trong 8 hướng
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = curr[0] + dx, curr[1] + dy
                        if (nx, ny) in pixel_set and not visited[ny, nx]:
                            next_pt = (nx, ny)
                            break
                    if next_pt:
                        break

                if next_pt:
                    visited[next_pt[1], next_pt[0]] = True
                    current_path.append(next_pt)
                    curr = next_pt
                else:
                    break

            if len(current_path) >= 3:
                paths.append([(float(x), float(y)) for x, y in current_path])

        # 2. Xử lý các vòng khép kín (closed loops) không có endpoint
        remaining = [pt for pt in pixel_set if not visited[pt[1], pt[0]]]
        for start_pt in remaining:
            if visited[start_pt[1], start_pt[0]]:
                continue
            current_path = [start_pt]
            visited[start_pt[1], start_pt[0]] = True
            curr = start_pt

            while True:
                next_pt = None
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = curr[0] + dx, curr[1] + dy
                        if (nx, ny) in pixel_set and not visited[ny, nx]:
                            next_pt = (nx, ny)
                            break
                    if next_pt:
                        break

                if next_pt:
                    visited[next_pt[1], next_pt[0]] = True
                    current_path.append(next_pt)
                    curr = next_pt
                else:
                    break

            if len(current_path) >= 3:
                paths.append([(float(x), float(y)) for x, y in current_path])

        return paths

    def _classify_stroke(
        self,
        length: float,
        bbox: Tuple[float, float, float, float],
        points: List[Tuple[float, float]],
    ) -> str:
        """
        Phân loại nét vẽ dựa trên chiều dài hình học và diện tích bao phủ.
        """
        bw = bbox[2] - bbox[0]
        bh = bbox[3] - bbox[1]
        diag = math.hypot(bw, bh)

        # Nét khung chính: dài và trải rộng
        if length > 120.0 or diag > 90.0:
            return "outline"

        # Nét cấu trúc trung bình
        if length > 45.0 or diag > 35.0:
            return "structure"

        # Nét nở bóng, gạch sọc: rất ngắn và thẳng
        if length < 18.0 and diag < 15.0:
            return "shading"

        # Các nét chi tiết còn lại (mắt, mũi, hoa văn nhỏ)
        return "detail"

    def _estimate_stroke_width(
        self,
        gray: np.ndarray,
        points: List[Tuple[float, float]],
    ) -> float:
        """Ước lượng độ dày nét vẽ thực tế."""
        if len(points) < 2:
            return 3.0

        # Lấy mẫu tại 3 điểm
        sample_indices = [len(points) // 4, len(points) // 2, (3 * len(points)) // 4]
        h, w = gray.shape
        widths = []

        for idx in sample_indices:
            px, py = int(round(points[idx][0])), int(round(points[idx][1]))
            if 2 <= px < w - 2 and 2 <= py < h - 2:
                # Đếm số pixel tối xung quanh bán kính 5px
                patch = gray[max(0, py - 4): min(h, py + 5), max(0, px - 4): min(w, px + 5)]
                dark_count = np.sum(patch < self.ink_threshold)
                # Đường kính xấp xỉ = 2 * sqrt(dark_count / pi)
                est_w = 2.0 * math.sqrt(max(1.0, dark_count) / math.pi)
                widths.append(min(12.0, max(1.5, est_w)))

        return float(np.median(widths)) if widths else 3.0
