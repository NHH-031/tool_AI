from __future__ import annotations

import io
from pathlib import Path
from typing import Optional, Tuple, Union

import cv2
import numpy as np


def hex_to_bgr(hex_color: str) -> np.ndarray:
    """Chuyển mã màu hex sang mảng NumPy BGR uint8."""
    digits = hex_color.lstrip("#")
    if len(digits) != 6:
        return np.array([215, 235, 245], dtype=np.uint8)  # #F5EBD7
    r = int(digits[0:2], 16)
    g = int(digits[2:4], 16)
    b = int(digits[4:6], 16)
    return np.array([b, g, r], dtype=np.uint8)


class SketchFilter:
    """
    Bộ lọc chuyển đổi hình ảnh thực tế / logo / sơ đồ sang tranh vẽ tay 2D (Comic Sketch Filter):
    - Khử hoàn toàn chất liệu 3D, CGI và ánh sáng nhân tạo.
    - Chuyển thành nét mực đen contour (#1A1A1A) và bóng bút chì graphite.
    - Hòa quyện nền giấy kem ấm cổ điển #F5EBD7 (BGR 215, 235, 245).
    - Hỗ trợ cả 2 phong cách: Đơn sắc mực đen (pure_ink) hoặc Truyện tranh màu nước cổ điển (watercolor_comic).
    """

    def __init__(self, canvas_hex: str = "#F5EBD7"):
        self.canvas_hex = canvas_hex
        self.canvas_bgr = hex_to_bgr(canvas_hex)

    def fit_and_pad_to_canvas(
        self,
        img: np.ndarray,
        target_size: Tuple[int, int] = (1920, 1080),
        has_alpha: bool = False,
    ) -> np.ndarray:
        """
        Căn giữa và đệm viền (letterbox/pillarbox) hình ảnh vào tỷ lệ mục tiêu
        với màu nền giấy kem ấm #F5EBD7, không làm biến dạng tỷ lệ gốc.
        """
        tw, th = target_size
        h, w = img.shape[:2]

        # Tính toán tỷ lệ co giãn giữ nguyên aspect ratio
        scale = min(tw / float(w), th / float(h))
        nw = max(1, int(round(w * scale)))
        nh = max(1, int(round(h * scale)))

        resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LANCZOS4 if scale > 1.0 else cv2.INTER_AREA)

        # Tạo canvas nền giấy kem ấm
        if has_alpha and img.shape[2] == 4:
            # Tách alpha channel và hòa sắc trước
            rgb = resized[:, :, :3].astype(np.float32)
            alpha = (resized[:, :, 3].astype(np.float32) / 255.0)[:, :, np.newaxis]
            bg_tile = np.full_like(rgb, self.canvas_bgr, dtype=np.float32)
            blended = (rgb * alpha + bg_tile * (1.0 - alpha)).astype(np.uint8)
            resized = blended

        canvas = np.full((th, tw, 3), self.canvas_bgr, dtype=np.uint8)
        off_x = (tw - nw) // 2
        off_y = (th - nh) // 2

        canvas[off_y : off_y + nh, off_x : off_x + nw] = resized[:, :, :3]
        return canvas

    def convert_to_pure_ink(
        self,
        img_bgr: np.ndarray,
        contrast: float = 1.25,
        line_strength: float = 1.3,
    ) -> np.ndarray:
        """
        Chuyển ảnh thành tranh vẽ phác thảo đơn sắc nét mực đen trên nền giấy kem ấm:
        Sử dụng kết hợp Color Dodge Pencil Sketch và Adaptive Edge Extraction.
        """
        # 1. Chuyển sang ảnh xám
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

        # 2. Làm mượt song phương để giảm nhiễu hạt nhưng giữ vững ranh giới chi tiết
        smooth = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)

        # 3. Kỹ thuật Color Dodge: Đảo nghịch -> Gaussian Blur -> Chia độ sáng
        inverted = 255 - smooth
        blurred = cv2.GaussianBlur(inverted, (21, 21), sigmaX=0, sigmaY=0)
        # Dodge division: (gray * 256) / (255 - blurred + 1)
        denom = 255 - blurred
        denom[denom == 0] = 1
        dodge = np.clip((gray.astype(np.float32) * 256.0) / denom.astype(np.float32), 0, 255).astype(np.uint8)

        # 4. Trích xuất nét viền mực đen bằng Adaptive Gaussian Thresholding
        adaptive_thresh = cv2.adaptiveThreshold(
            smooth,
            maxValue=255,
            adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            thresholdType=cv2.THRESH_BINARY,
            blockSize=9,
            C=3,
        )

        # 5. Kết hợp nét viền và bóng bút chì
        sketch_val = np.minimum(dodge, adaptive_thresh)

        # 6. Tinh chỉnh độ tương phản (contrast curve)
        if contrast != 1.0:
            sketch_norm = sketch_val.astype(np.float32) / 255.0
            sketch_norm = np.clip((sketch_norm - 0.5) * contrast + 0.5, 0.0, 1.0)
            sketch_val = (sketch_norm * 255.0).astype(np.uint8)

        # 7. Phối trộn lên nền giấy kem ấm #F5EBD7
        # Giá trị 255 là màu giấy kem, giá trị 0 là màu mực đen #1A1A1A (BGR: 26, 26, 26)
        ink_bgr = np.array([26, 26, 26], dtype=np.float32)
        paper_bgr = self.canvas_bgr.astype(np.float32)

        factor = (sketch_val.astype(np.float32) / 255.0)[:, :, np.newaxis]
        # factor = 1.0 -> paper; factor = 0.0 -> ink
        result = factor * paper_bgr + (1.0 - factor) * ink_bgr
        return np.clip(result, 0, 255).astype(np.uint8)

    def convert_to_watercolor_comic(
        self,
        img_bgr: np.ndarray,
        contrast: float = 1.15,
        line_strength: float = 1.4,
    ) -> np.ndarray:
        """
        Chuyển ảnh thành phong cách truyện tranh 2D màu nước cổ điển (Vintage Watercolor Comic):
        - Giữ các dải màu dạng flat cel-shade/màu nước mờ (matte wash).
        - Phủ nét mực đen contour dứt khoát lên trên ranh giới đối tượng.
        - Hòa trộn màu giấy kem ấm #F5EBD7.
        """
        # 1. Làm mượt phân vùng phẳng bằng bilateral nhiều lần (Watercolor posterization)
        color_smooth = img_bgr.copy()
        for _ in range(2):
            color_smooth = cv2.bilateralFilter(color_smooth, d=9, sigmaColor=50, sigmaSpace=50)

        # 2. Tạo viền mực đen
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        gray_smooth = cv2.medianBlur(gray, 5)
        edges = cv2.adaptiveThreshold(
            gray_smooth,
            maxValue=255,
            adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            thresholdType=cv2.THRESH_BINARY,
            blockSize=9,
            C=4,
        )

        # Làm nét viền mực đanh chắc hơn nếu line_strength > 1
        if line_strength > 1.0:
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            edges = cv2.erode(edges, kernel, iterations=1)

        edge_mask = (edges.astype(np.float32) / 255.0)[:, :, np.newaxis]

        # 3. Hòa trộn màu với chất nền kem ấm (Multiply blend với #F5EBD7)
        paper_norm = self.canvas_bgr.astype(np.float32) / 255.0
        color_norm = color_smooth.astype(np.float32) / 255.0
        tinted_color = color_norm * (0.65 * paper_norm + 0.35) * 255.0

        # 4. Phủ nét mực đen lên trên
        ink_bgr = np.array([26, 26, 26], dtype=np.float32)
        final_bgr = edge_mask * tinted_color + (1.0 - edge_mask) * ink_bgr

        if contrast != 1.0:
            final_norm = final_bgr / 255.0
            final_norm = np.clip((final_norm - 0.5) * contrast + 0.5, 0.0, 1.0)
            final_bgr = final_norm * 255.0

        return np.clip(final_bgr, 0, 255).astype(np.uint8)

    def extract_lineart_layer(
        self,
        img_bgr: np.ndarray,
        contrast: float = 1.2,
        line_strength: float = 1.4,
    ) -> np.ndarray:
        """
        Trích xuất riêng lớp nét vẽ mực đen (Line-art Layer) trên nền giấy kem ấm #F5EBD7.
        Dành riêng cho pha vẽ nét của cánh tay robot / hoạt họa whiteboard (vẽ nét TRƯỚC khi đổ màu).
        """
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        gray_smooth = cv2.medianBlur(gray, 5)
        edges = cv2.adaptiveThreshold(
            gray_smooth,
            maxValue=255,
            adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            thresholdType=cv2.THRESH_BINARY,
            blockSize=9,
            C=4,
        )

        if line_strength > 1.0:
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            edges = cv2.erode(edges, kernel, iterations=1)

        edge_mask = (edges.astype(np.float32) / 255.0)[:, :, np.newaxis]
        paper_bgr = self.canvas_bgr.astype(np.float32)
        ink_bgr = np.array([26, 26, 26], dtype=np.float32)

        lineart_bgr = edge_mask * paper_bgr + (1.0 - edge_mask) * ink_bgr

        if contrast != 1.0:
            lineart_norm = lineart_bgr / 255.0
            lineart_norm = np.clip((lineart_norm - 0.5) * contrast + 0.5, 0.0, 1.0)
            lineart_bgr = lineart_norm * 255.0

        return np.clip(lineart_bgr, 0, 255).astype(np.uint8)

    def extract_color_layer(
        self,
        img_bgr: np.ndarray,
    ) -> np.ndarray:
        """
        Trích xuất riêng lớp màu nước / flat cel-shade (Color Wash Layer) hòa trộn với nền kem ấm #F5EBD7.
        Được dùng để fade-in hoặc tô màu SAU KHI toàn bộ nét vẽ line-art đã hoàn thành 100%.
        """
        color_smooth = img_bgr.copy()
        for _ in range(2):
            color_smooth = cv2.bilateralFilter(color_smooth, d=9, sigmaColor=50, sigmaSpace=50)

        paper_norm = self.canvas_bgr.astype(np.float32) / 255.0
        color_norm = color_smooth.astype(np.float32) / 255.0
        tinted_color = color_norm * (0.65 * paper_norm + 0.35) * 255.0
        return np.clip(tinted_color, 0, 255).astype(np.uint8)

    def extract_dual_layers(
        self,
        img_bgr: np.ndarray,
        contrast: float = 1.15,
        line_strength: float = 1.4,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Tách ảnh hoàn chỉnh thành 2 lớp độc lập phục vụ Dual-Layer Rendering:
        - Layer 1 (Line-art): Nét mực contour đen trên nền giấy kem (vẽ trước hoàn toàn)
        - Layer 2 (Color wash): Lớp màu phẳng cel-shade (fade-in sau)
        """
        lineart = self.extract_lineart_layer(img_bgr, contrast=contrast, line_strength=line_strength)
        color = self.extract_color_layer(img_bgr)
        return lineart, color

    def process_image(
        self,
        image_input: Union[str, Path, bytes, np.ndarray],
        style: str = "watercolor_comic",  # "watercolor_comic" | "pure_ink" | "lineart" | "color"
        target_size: Tuple[int, int] = (1920, 1080),
        contrast: float = 1.2,
        line_strength: float = 1.3,
    ) -> np.ndarray:
        """
        Hàm chính nhận vào file ảnh / bytes / mảng NumPy,
        chuẩn hóa tỷ lệ canvas và áp dụng bộ lọc nghệ thuật vẽ tay.
        """
        # Đọc ảnh từ các nguồn định dạng khác nhau
        if isinstance(image_input, (str, Path)):
            raw = cv2.imread(str(image_input), cv2.IMREAD_UNCHANGED)
        elif isinstance(image_input, bytes):
            nparr = np.frombuffer(image_input, np.uint8)
            raw = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
        elif isinstance(image_input, np.ndarray):
            raw = image_input
        else:
            raise ValueError(f"Không hỗ trợ kiểu đầu vào: {type(image_input)}")

        if raw is None:
            raise ValueError("Không thể nạp hoặc giải mã hình ảnh cung cấp.")

        has_alpha = len(raw.shape) == 3 and raw.shape[2] == 4

        # Căn chỉnh kích thước và đệm viền canvas nền kem
        padded = self.fit_and_pad_to_canvas(raw, target_size=target_size, has_alpha=has_alpha)

        # Áp dụng bộ lọc tùy biến theo style
        if style == "pure_ink":
            return self.convert_to_pure_ink(padded, contrast=contrast, line_strength=line_strength)
        elif style == "lineart":
            return self.extract_lineart_layer(padded, contrast=contrast, line_strength=line_strength)
        elif style == "color":
            return self.extract_color_layer(padded)
        elif style == "dual_layer":
            return self.extract_dual_layers(padded, contrast=contrast, line_strength=line_strength)
        else:
            return self.convert_to_watercolor_comic(padded, contrast=contrast, line_strength=line_strength)
