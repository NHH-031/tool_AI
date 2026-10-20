from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.artwork.generator import ArtworkGeneratorFactory
from core.artwork.prompt_builder import StructuredIllustrationPrompt

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/storyboard", tags=["Storyboard"])

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class GenerateImageRequest(BaseModel):
    scene_id: str
    scene_index: int
    prompt: str = Field(min_length=1)
    project_id: str = "default"
    force_regenerate: bool = False
    aspect_ratio: str = "16:9"


class GenerateImageResponse(BaseModel):
    scene_id: str
    scene_index: int
    image_url: str
    status: str = "completed"


def _ensure_skill_md_prompt_gate(prompt_text: str, aspect_ratio: str = "16:9") -> str:
    """Đảm bảo prompt tuân thủ nghiêm ngặt chuẩn SKILL.md và phong cách truyện tranh 2D (cấm 3D)."""
    p_lower = prompt_text.lower()
    prefix_parts = []
    suffix_parts = []

    # 1. Bắt buộc phong cách truyện tranh 2D / graphic novel
    if not any(k in p_lower for k in ["comic", "graphic novel", "2d", "lianhuanhua", "manhua"]):
        prefix_parts.append("Masterpiece 2D vintage comic book illustration, traditional graphic novel art")

    # 2. Quy chuẩn nền giấy kem ấm cổ #F5EBD7 theo SKILL.md
    if "#f5ebd7" not in p_lower and "cream paper" not in p_lower:
        suffix_parts.append("on warm vintage cream paper #F5EBD7")

    # 3. Nét viền mực và đánh bóng gạch nét bút sắt
    if "ink" not in p_lower and "contour" not in p_lower:
        suffix_parts.append("crisp expressive dark ink contour outlines with fine line cross-hatching")

    # 4. Màu phẳng mờ (flat matte wash), không bóng 3D
    if "matte" not in p_lower and "watercolor" not in p_lower and "cel" not in p_lower:
        suffix_parts.append("flat matte muted vintage watercolor wash")

    # 5. Nghiêm cấm 3D, CGI và chữ
    if "no 3d" not in p_lower:
        suffix_parts.append("strictly 2D flat art, NO 3D render, NO CGI, NO plastic gloss, NO 3D models")
    if "no text" not in p_lower:
        if aspect_ratio == "9:16":
            suffix_parts.append("vertical 9:16 portrait orientation, vertical composition, mobile display, no text, no speech bubbles, no watermark")
        else:
            suffix_parts.append("masterpiece quality, 1080p widescreen, no text, no speech bubbles, no watermark")

    result = prompt_text.rstrip(". ")
    if prefix_parts:
        result = f"{', '.join(prefix_parts)}, {result}"
    if suffix_parts:
        result = f"{result}, {', '.join(suffix_parts)}"
    return result


@router.get("/{project_id}", response_model=list[GenerateImageResponse])
async def get_project_storyboard(project_id: str) -> list[GenerateImageResponse]:
    """Lấy danh sách các ảnh storyboard đã sinh của dự án."""
    out_dir = PROJECT_ROOT / "output" / "storyboard" / project_id
    if not out_dir.exists():
        return []
    import time
    ts = int(time.time() * 1000)
    items: list[GenerateImageResponse] = []
    for f in sorted(out_dir.glob("scene_*.png")):
        try:
            num_str = f.stem.replace("scene_", "")
            idx = int(num_str)
            rel_url = f"/media/storyboard/{project_id}/{f.name}?t={ts}"
            items.append(
                GenerateImageResponse(
                    scene_id=f"scene-{idx}",
                    scene_index=idx,
                    image_url=rel_url,
                    status="completed",
                )
            )
        except ValueError:
            continue
    return items


@router.post("/generate-image", response_model=GenerateImageResponse)
async def generate_scene_image(req: GenerateImageRequest) -> GenerateImageResponse:
    """
    Sinh hình ảnh vẽ tay cho một phân cảnh cụ thể.
    Tuân thủ chất lượng cao SKILL.md:
    - Nền giấy kem #F5EBD7
    - Nét mực đen contour sắc sảo
    - Độ phân giải 1920x1080
    """
    out_dir = PROJECT_ROOT / "output" / "storyboard" / req.project_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"scene_{req.scene_index}.png"

    import time
    timestamp = int(time.time() * 1000)

    # Nếu ảnh đã tồn tại hợp lệ và không yêu cầu vẽ lại, trả về ngay lập tức
    if not req.force_regenerate and out_path.exists() and out_path.stat().st_size > 100000:
        rel_url = f"/media/storyboard/{req.project_id}/{out_path.name}?t={timestamp}"
        return GenerateImageResponse(
            scene_id=req.scene_id,
            scene_index=req.scene_index,
            image_url=rel_url,
            status="completed",
        )

    # Enforce quality prompt gate
    guaranteed_prompt = _ensure_skill_md_prompt_gate(req.prompt, aspect_ratio=req.aspect_ratio)

    try:
        generator = ArtworkGeneratorFactory.create()
        is_vertical = req.aspect_ratio == "9:16"
        target_w, target_h = (1080, 1920) if is_vertical else (1920, 1080)

        prompt_struct = StructuredIllustrationPrompt(
            subject=req.prompt[:120],
            action="",
            full_prompt=guaranteed_prompt,
            scene_context=guaranteed_prompt,
            has_color=True,
            aspect_ratio=req.aspect_ratio,
        )
        saved_file = await generator.generate_artwork(
            prompt=prompt_struct,
            output_path=out_path,
            width=target_w,
            height=target_h,
        )
        rel_url = f"/media/storyboard/{req.project_id}/{saved_file.name}?t={timestamp}"
        return GenerateImageResponse(
            scene_id=req.scene_id,
            scene_index=req.scene_index,
            image_url=rel_url,
            status="completed",
        )
    except Exception as e:
        logger.error(f"[generate_scene_image] Generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi sinh ảnh AI cho cảnh {req.scene_index}: {str(e)}"
        )
