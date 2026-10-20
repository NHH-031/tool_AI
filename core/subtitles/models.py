"""
Data models for Subtitles (SRT / VTT / Word Timing).
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class SubtitleWord(BaseModel):
    word: str
    start_sec: float
    end_sec: float
    duration: float = 0.0


class SubtitleSegment(BaseModel):
    index: int
    start_sec: float
    end_sec: float
    text: str
    words: List[SubtitleWord] = Field(default_factory=list)

    @property
    def duration_sec(self) -> float:
        return max(0.1, self.end_sec - self.start_sec)


class SubtitleTypographyConfig(BaseModel):
    """
    Cấu hình hiển thị và định dạng phụ đề chuyên sâu theo chuẩn nhận diện thương hiệu.
    Hỗ trợ font bảng đen viết tay (Patrick Hand, Mali, Caveat) và font hiện đại (Inter, Roboto, Segoe UI).
    """
    font_family: str = Field(default="Patrick Hand", description="Tên font chữ (Patrick Hand, Mali, Caveat, Comic Sans, Segoe UI, Roboto, Inter, Arial)")
    font_size_preset: str = Field(default="md", description="Kích thước chữ: sm, md, lg, xl")
    font_size: Optional[int] = Field(default=None, description="Kích thước chữ tính theo pixel nguyên bản (ghi đè preset nếu có)")
    text_color: str = Field(default="#FFFFFF", description="Màu chữ chính (hex)")
    stroke_color: str = Field(default="#000000", description="Màu viền chữ (hex)")
    stroke_width: int = Field(default=2, ge=0, le=8, description="Độ dày nét viền chữ (px)")
    bg_color: str = Field(default="#0F172AD0", description="Màu nền đệm bán trong suốt (hex hoặc rgba)")
    bg_enabled: bool = Field(default=True, description="Có vẽ khung nền đệm bo góc hay không")
    highlight_color: str = Field(default="#FFE600", description="Màu highlight Karaoke khi đọc tới từ (Vàng neon #FFE600, Xanh mint #00FFCC, Cam rực #FF5500, Vàng kim #FACC15)")
    position: str = Field(default="bottom", description="Vị trí hiển thị: bottom, center, top")
    y_offset_percent: Optional[float] = Field(default=None, description="Khoảng cách tùy chỉnh so với biên (0.02 - 0.40)")

    def resolve_font_size(self, aspect_ratio: str = "16:9") -> int:
        """Tính toán kích cỡ font phù hợp theo tỷ lệ khung hình và preset."""
        if self.font_size and self.font_size > 8:
            return self.font_size
        is_vertical = aspect_ratio == "9:16"
        scale = 0.85 if is_vertical else 1.0
        preset_map = {
            "sm": 24,
            "md": 32,
            "lg": 40,
            "xl": 48,
        }
        base = preset_map.get(self.font_size_preset.lower(), 32)
        return int(base * scale)
