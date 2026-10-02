from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


class NarrationSegment(BaseModel):
    """Một đoạn lời thoại/thuyết minh tương ứng với một phân đoạn video."""
    id: str = Field(description="Mã định danh duy nhất của đoạn thuyết minh")
    text: str = Field(description="Nội dung lời thuyết minh")
    cue_index: int = Field(default=1, ge=1, description="Chỉ số thứ tự trong danh sách thoại")
    start_ms: int = Field(default=0, ge=0, description="Mốc thời gian bắt đầu nói (ms)")
    end_ms: int = Field(default=0, ge=0, description="Mốc thời gian kết thúc nói (ms)")
    duration_ms: int = Field(default=0, ge=0, description="Thời lượng phát âm thanh (ms)")
    audio_asset_id: Optional[str] = Field(default=None, description="Mã ID của asset file âm thanh đã sinh")
    voice_id: Optional[str] = Field(default=None, description="Mã giọng đọc TTS đã sử dụng")


class AudioTrack(BaseModel):
    """Một rãnh âm thanh trong cảnh hoặc dự án (voiceover, bgm, sfx)."""
    id: str = Field(description="Mã định danh rãnh âm thanh")
    track_type: Literal["voiceover", "bgm", "sfx"] = Field(
        default="voiceover",
        description="Phân loại rãnh âm thanh",
    )
    asset_id: str = Field(description="Mã tham chiếu tới Asset âm thanh")
    start_ms: int = Field(default=0, ge=0, description="Mốc bắt đầu phát trên timeline (ms)")
    duration_ms: int = Field(gt=0, description="Thời lượng phát (ms)")
    volume: float = Field(default=1.0, ge=0.0, le=1.0, description="Mức âm lượng (0.0 đến 1.0)")
    loop: bool = Field(default=False, description="Tự động lặp lại khi hết track")
