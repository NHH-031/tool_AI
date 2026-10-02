from __future__ import annotations

from typing import List, Literal, Tuple
from pydantic import BaseModel, Field

from .annotation import RegionSchema


class DrawingStroke(BaseModel):
    """Nét vẽ chi tiết được engine tính toán theo đường đi của bút."""
    id: str = Field(description="Mã định danh nét vẽ")
    path_mode: Literal["grid", "skeleton"] = Field(
        default="grid",
        description="Thuật toán tạo đường nét (grid hoặc skeleton Zhang-Suen)",
    )
    points: List[Tuple[int, int]] = Field(
        default_factory=list,
        description="Danh sách các điểm pixel tọa độ [x, y] liên tục của nét bút",
    )
    color_hex: str = Field(default="#000000", description="Mã màu nét vẽ")
    stroke_width: float = Field(default=2.0, gt=0, description="Độ dày nét bút")
    order: int = Field(default=0, ge=0, description="Thứ tự vẽ của nét")


class DrawingAction(BaseModel):
    """Hành động vẽ của bàn tay lên một thực thể cụ thể trên canvas."""
    id: str = Field(description="Mã hành động vẽ")
    entity_id: str = Field(description="Mã ID của VisualEntity đang được vẽ")
    action_type: Literal["ink", "color", "wipe", "erase", "gaze"] = Field(
        default="ink",
        description="Loại thao tác vẽ (ink: hạ nét, color: lên màu, gaze: dừng ngắm)",
    )
    start_ms: int = Field(ge=0, description="Thời điểm bắt đầu hành động (ms)")
    duration_ms: int = Field(gt=0, description="Thời lượng thực hiện hành động (ms)")
    ink_weight: int = Field(default=2, ge=0, description="Trọng số thời gian hạ nét mực")
    color_weight: int = Field(default=1, ge=0, description="Trọng số thời gian lên màu")
    protected_regions: List[RegionSchema] = Field(
        default_factory=list,
        description="Các vùng che chắn không được lộ nét trong khi thực hiện hành động này",
    )
