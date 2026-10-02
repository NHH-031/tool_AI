from __future__ import annotations

from typing import List
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/voices", tags=["Voices"])


class VoiceItem(BaseModel):
    id: str
    name: str
    language: str
    locale: str
    gender: str
    accent: str
    sample_text: str
    supported_speeds: List[float] = Field(default_factory=lambda: [0.8, 1.0, 1.2, 1.5])
    is_neural: bool = True
    tags: List[str] = Field(default_factory=list)


VOICES_CATALOG: List[VoiceItem] = [
    VoiceItem(
        id="vi-VN-Standard-A",
        name="Mai Chi",
        language="Tiếng Việt",
        locale="vi-VN",
        gender="female",
        accent="Bắc Bộ (Truyền Cảm)",
        sample_text="Xin chào các bạn, hôm nay chúng ta sẽ cùng khám phá thế giới tự nhiên kỳ thú.",
        tags=["natural", "storytelling", "vietnamese", "female"],
    ),
    VoiceItem(
        id="vi-VN-Standard-B",
        name="Nam Khánh",
        language="Tiếng Việt",
        locale="vi-VN",
        gender="male",
        accent="Bắc Bộ (Trầm Ấm)",
        sample_text="Con khỉ đang trèo lên cây để lấy một quả chuối.",
        tags=["warm", "explainer", "vietnamese", "male"],
    ),
    VoiceItem(
        id="vi-VN-Neural-C",
        name="Thảo My",
        language="Tiếng Việt",
        locale="vi-VN",
        gender="female",
        accent="Nam Bộ (Ngọt Ngào)",
        sample_text="Chào bạn! Hãy cùng tôi tìm hiểu bài học thú vị ngày hôm nay nhé.",
        tags=["friendly", "educational", "vietnamese", "female"],
    ),
    VoiceItem(
        id="en-US-Standard-A",
        name="Arthur",
        language="English",
        locale="en-US",
        gender="male",
        accent="American (Professional)",
        sample_text="Welcome to AI Whiteboard Studio, turning your ideas into hand-drawn stories.",
        tags=["authoritative", "corporate", "english", "male"],
    ),
    VoiceItem(
        id="en-US-Standard-B",
        name="Elena",
        language="English",
        locale="en-US",
        gender="female",
        accent="American (Lively)",
        sample_text="Watch as complex ideas unfold through real-time dynamic hand drawings.",
        tags=["expressive", "youtube", "english", "female"],
    ),
]


@router.get("", response_model=List[VoiceItem])
async def list_voices() -> List[VoiceItem]:
    """Trả về danh mục giọng đọc TTS khả dụng."""
    return VOICES_CATALOG
