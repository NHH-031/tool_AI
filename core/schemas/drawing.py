from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, Field

from .annotation import RegionSchema


class DrawingStroke(BaseModel):
    """
    Nét vẽ chi tiết có thứ tự (Ordered Vector Stroke) phục vụ Whiteboard Drawing Engine.
    Hỗ trợ cả định dạng snake_case lẫn camelCase theo đặc tả Phase 06.
    """
    model_config = {"populate_by_name": True}

    id: str = Field(default="", description="Mã định danh nét vẽ", alias="strokeId")
    asset_id: str = Field(default="", description="Mã định danh asset chứa nét vẽ", alias="assetId")
    path: str = Field(default="", description="Chuỗi SVG path d hoặc định nghĩa vector")
    order: int = Field(default=0, ge=0, description="Thứ tự vẽ tuần tự của nét")
    duration: float = Field(default=0.5, ge=0, description="Thời lượng vẽ nét (giây)")
    start_point: Tuple[float, float] = Field(
        default=(0.0, 0.0), description="Tọa độ điểm bắt đầu [x, y]", alias="startPoint"
    )
    end_point: Tuple[float, float] = Field(
        default=(0.0, 0.0), description="Tọa độ điểm kết thúc [x, y]", alias="endPoint"
    )
    semantic_purpose: str = Field(
        default="outline",
        description="Ý nghĩa ngữ nghĩa của nét (ví dụ: 'trunk', 'branches', 'leaves', 'body', 'head', 'arms', 'legs')",
        alias="semanticPurpose",
    )
    points: List[Tuple[float, float]] = Field(
        default_factory=list,
        description="Danh sách các điểm tọa độ liên tục theo thời gian",
    )
    length: float = Field(default=0.0, ge=0, description="Độ dài hình học của nét (pixel)")
    color_hex: str = Field(default="#1A1A1A", description="Mã màu nét bút")
    stroke_width: float = Field(default=6.0, gt=0, description="Độ dày nét bút")
    path_mode: Literal["grid", "skeleton", "vector"] = Field(
        default="vector",
        description="Thuật toán tạo đường nét (grid, skeleton Zhang-Suen, hoặc vector)",
    )

    @property
    def strokeId(self) -> str:
        return self.id

    @property
    def assetId(self) -> str:
        return self.asset_id

    @property
    def startPoint(self) -> Tuple[float, float]:
        return self.start_point

    @property
    def endPoint(self) -> Tuple[float, float]:
        return self.end_point

    @property
    def semanticPurpose(self) -> str:
        return self.semantic_purpose


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
    strokes: List[DrawingStroke] = Field(
        default_factory=list,
        description="Danh sách các nét vẽ vector tuần tự tạo nên hành động này",
    )
    protected_regions: List[RegionSchema] = Field(
        default_factory=list,
        description="Các vùng che chắn không được lộ nét trong khi thực hiện hành động này",
    )
