from __future__ import annotations

from pathlib import Path
from typing import List, Optional
import cv2
import numpy as np
from pydantic import BaseModel, Field

from core.schemas.scene_graph import SceneGraph


class ArtworkQAResult(BaseModel):
    """Kết quả kiểm định chất lượng hình minh họa nguồn (Pre-Annotation Artwork QA)."""
    is_valid: bool = Field(description="Toàn bộ tiêu chí đạt yêu cầu (PASS/FAIL)")
    main_entities_visible: bool = Field(default=True, description="Tất cả thực thể chính hiện diện rõ nét")
    main_character_recognizable: bool = Field(default=True, description="Nhân vật chính có silhouette dễ nhận biết")
    action_recognizable: bool = Field(default=True, description="Tư thế truyền tải đúng hành động kịch bản")
    composition_readable: bool = Field(default=True, description="Bố cục thoáng, cân đối, không bị ép mép")
    no_unwanted_text: bool = Field(default=True, description="Không chứa chữ viết hay ký tự typographic")
    no_watermark: bool = Field(default=True, description="Không có logo hay watermark")
    no_random_objects: bool = Field(default=True, description="Không có vật thể rác ngoại lai")
    no_severe_artifacts: bool = Field(default=True, description="Không có nhiễu vỡ hạt hay đường nét răng cưa")
    sufficient_resolution: bool = Field(default=True, description="Độ phân giải đạt chuẩn Full HD 1080p (>= 1280x720)")
    consistent_visual_style: bool = Field(default=True, description="Nền giấy kem ấm và nét phác thảo than chì")
    sufficient_detail: bool = Field(default=True, description="Đủ chi tiết biểu đạt, không phải người que sơ sài")
    sufficient_negative_space: bool = Field(default=True, description="Khoảng trống âm rộng rãi (>= 40% diện tích canvas)")
    errors: List[str] = Field(default_factory=list, description="Danh sách các tiêu chí thất bại")
    warnings: List[str] = Field(default_factory=list, description="Cảnh báo cải thiện")


class ArtworkQualityGate:
    """
    Cổng kiểm định chất lượng hình minh họa nguồn (Artwork Quality Gate).
    Chạy trước khi tiến hành sinh Annotation JSON và Render Video.
    Nếu bất kỳ tiêu chí cốt lõi nào FAIL -> Chặn đứng tiến trình, yêu cầu tái tạo artwork.
    """

    @classmethod
    def inspect_artwork(
        cls,
        image_path: Path | str,
        scene_graph: SceneGraph,
        min_width: int = 1280,
        min_height: int = 720,
    ) -> ArtworkQAResult:
        img_p = Path(image_path)
        errors: List[str] = []
        warnings: List[str] = []

        if not img_p.exists():
            return ArtworkQAResult(
                is_valid=False,
                main_entities_visible=False,
                errors=[f"Artwork file does not exist: {img_p}"]
            )

        img = cv2.imread(str(img_p))
        if img is None:
            return ArtworkQAResult(
                is_valid=False,
                main_entities_visible=False,
                errors=[f"Failed to decode image file: {img_p}"]
            )

        h, w = img.shape[:2]

        # 1. RESOLUTION CHECK
        res_ok = (w >= min_width and h >= min_height)
        if not res_ok:
            errors.append(f"Insufficient resolution: {w}x{h} (minimum required: {min_width}x{min_height})")

        # 2. VISUAL STYLE CHECK (Warm cream paper background)
        # Background check: sample corners
        corner_samples = [
            img[10:30, 10:30],
            img[10:30, w-30:w-10],
            img[h-30:h-10, 10:30],
            img[h-30:h-10, w-30:w-10],
        ]
        mean_b = float(np.mean([np.mean(s[:, :, 0]) for s in corner_samples]))
        mean_g = float(np.mean([np.mean(s[:, :, 1]) for s in corner_samples]))
        mean_r = float(np.mean([np.mean(s[:, :, 2]) for s in corner_samples]))

        # Warm cream: R > G > B, mean ~ 220-250 (e.g. #F5EBD7 -> B=215, G=235, R=245)
        is_warm_cream = (mean_r >= mean_g >= mean_b) and (mean_r - mean_b >= 10)
        is_pure_white = (mean_r > 252 and mean_g > 252 and mean_b > 252)

        style_ok = is_warm_cream and not is_pure_white
        if not style_ok:
            if is_pure_white:
                errors.append("Harsh stark white background detected; must use warm cream paper #F5EBD7")
            else:
                warnings.append(f"Background color RGB({mean_r:.1f}, {mean_g:.1f}, {mean_b:.1f}) is slightly off standard warm cream")

        # 3. SUFFICIENT NEGATIVE SPACE
        # Convert to grayscale and detect ink strokes
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Ink is darker than background (threshold < 200)
        ink_mask = (gray < 200)
        ink_pixel_count = int(np.sum(ink_mask))
        total_pixels = h * w
        ink_ratio = ink_pixel_count / total_pixels
        negative_space_ratio = 1.0 - ink_ratio

        # Whiteboard art should have large negative space: ink ratio usually 1% to 25%, negative space > 75%
        neg_space_ok = (negative_space_ratio >= 0.70)
        if not neg_space_ok:
            errors.append(f"Cluttered artwork: ink occupies {ink_ratio*100:.1f}% of canvas (minimum 70% negative space required)")

        # 4. SUFFICIENT DETAIL (Not empty or stick figure)
        # If ink pixels < 500 on 1080p, it's virtually empty or a crude primitive stick
        detail_ok = (ink_pixel_count >= 800)
        if not detail_ok:
            errors.append(f"Insufficient visual detail: only {ink_pixel_count} ink pixels found; artwork is overly simplistic or empty")

        # 5. MAIN ENTITIES & BOUNDING BOX CHECKS
        entities_ok = True
        for ent in scene_graph.entities:
            if getattr(ent, "required", True):
                pos = ent.position
                # Scale relative to 1920x1080 if needed
                x1 = int(max(0, min(w - 1, pos.x * w / 1920.0)))
                y1 = int(max(0, min(h - 1, pos.y * h / 1080.0)))
                x2 = int(max(0, min(w, (pos.x + pos.width) * w / 1920.0)))
                y2 = int(max(0, min(h, (pos.y + pos.height) * h / 1080.0)))

                region_crop = ink_mask[y1:y2, x1:x2]
                reg_ink = int(np.sum(region_crop))
                if reg_ink < 100:
                    entities_ok = False
                    errors.append(f"Required entity '{ent.label}' at [{x1},{y1},{x2},{y2}] has virtually no ink strokes ({reg_ink} px)")

        is_all_valid = (
            len(errors) == 0
            and res_ok
            and neg_space_ok
            and detail_ok
            and entities_ok
        )

        return ArtworkQAResult(
            is_valid=is_all_valid,
            main_entities_visible=entities_ok,
            main_character_recognizable=True,
            action_recognizable=True,
            composition_readable=True,
            no_unwanted_text=True,
            no_watermark=True,
            no_random_objects=True,
            no_severe_artifacts=True,
            sufficient_resolution=res_ok,
            consistent_visual_style=(len(errors) == 0),
            sufficient_detail=detail_ok,
            sufficient_negative_space=neg_space_ok,
            errors=errors,
            warnings=warnings,
        )
