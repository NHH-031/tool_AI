from __future__ import annotations

from typing import List
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/templates", tags=["Templates"])


class TemplateItem(BaseModel):
    id: str
    name: str
    description: str
    category: str
    aspect_ratio: str = "16:9"
    default_fps: int = 30
    bg_color_hex: str = "#FFFFFF"
    accent_color_hex: str = "#2563EB"
    preview_style: str = "whiteboard"
    tags: List[str] = Field(default_factory=list)


TEMPLATES_CATALOG: List[TemplateItem] = [
    TemplateItem(
        id="notion_minimal",
        name="Notion Minimalist Whiteboard",
        description="Phong cách vẽ nét thanh mảnh, thanh lịch, nền trắng ngà tối giản tương tự Notion & Excalidraw.",
        category="minimalist",
        aspect_ratio="16:9",
        default_fps=30,
        bg_color_hex="#FBFBF9",
        accent_color_hex="#0F172A",
        preview_style="clean_ink",
        tags=["notion", "minimalist", "clean", "lineart"],
    ),
    TemplateItem(
        id="hand_drawn_sketch",
        name="Hand-Drawn Charcoal Sketch",
        description="Nét vẽ tay chì than chân thực với bàn tay họa sĩ di chuyển sinh động, phù hợp giải thích khái niệm.",
        category="sketch",
        aspect_ratio="16:9",
        default_fps=30,
        bg_color_hex="#FFFFFF",
        accent_color_hex="#334155",
        preview_style="charcoal_sketch",
        tags=["hand_drawn", "charcoal", "doodle", "educational"],
    ),
    TemplateItem(
        id="vibrant_explainer",
        name="Vibrant Marketing Explainer",
        description="Phong cách sinh động kết hợp nét vẽ viền đen nổi bật với các mảng màu pastel tương phản cao.",
        category="marketing",
        aspect_ratio="16:9",
        default_fps=60,
        bg_color_hex="#F8FAFC",
        accent_color_hex="#4F46E5",
        preview_style="contour_wipe",
        tags=["vibrant", "marketing", "youtube", "colorful"],
    ),
    TemplateItem(
        id="dark_chalkboard",
        name="Academic Blackboard Chalk",
        description="Mô phỏng bảng phấn đen trường học cổ điển với nét phấn trắng và độ tương phản quang học dịu mắt.",
        category="academic",
        aspect_ratio="16:9",
        default_fps=30,
        bg_color_hex="#1E293B",
        accent_color_hex="#38BDF8",
        preview_style="chalk",
        tags=["chalkboard", "academic", "dark_mode", "science"],
    ),
    TemplateItem(
        id="social_vertical",
        name="TikTok / Reels Vertical Whiteboard",
        description="Tỉ lệ dọc 9:16 tối ưu cho mạng xã hội Shorts/TikTok/Reels với cỡ nét to và tốc độ vẽ tăng cường.",
        category="social",
        aspect_ratio="9:16",
        default_fps=30,
        bg_color_hex="#FFFFFF",
        accent_color_hex="#E11D48",
        preview_style="fast_stream",
        tags=["tiktok", "shorts", "reels", "vertical"],
    ),
]


@router.get("", response_model=List[TemplateItem])
async def list_templates() -> List[TemplateItem]:
    """Trả về danh mục Video Templates sẵn có trong hệ thống."""
    return TEMPLATES_CATALOG
