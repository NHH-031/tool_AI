from __future__ import annotations

from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field


class TimelineEvent(BaseModel):
    """Sự kiện hợp nhất diễn ra trên trục thời gian của phân cảnh."""
    id: str = Field(description="Mã định danh duy nhất của sự kiện")
    event_type: Literal["narration", "drawing", "camera", "transition", "pause"] = Field(
        description="Loại sự kiện trên timeline",
    )
    start_ms: int = Field(ge=0, description="Thời điểm bắt đầu sự kiện (ms)")
    end_ms: int = Field(ge=0, description="Thời điểm kết thúc sự kiện (ms)")
    duration_ms: int = Field(ge=0, description="Thời lượng sự kiện (ms)")
    target_id: Optional[str] = Field(
        default=None,
        description="Mã ID đối tượng liên quan (VisualEntity ID hoặc Narration ID)",
    )
    description: str = Field(default="", description="Mô tả diễn giải sự kiện")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Dữ liệu phụ trợ tùy biến")
