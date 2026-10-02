from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .scene_graph import SceneGraph, VisualEntity, VisualRelationship
from .drawing import DrawingAction
from .annotation import CanvasSchema


class SceneVisualPlan(BaseModel):
    """Kế hoạch thị giác chi tiết cho một phân cảnh video."""
    scene_index: int = Field(default=1, ge=1, description="Số thứ tự cảnh")
    scene_id: str = Field(
        default_factory=lambda: f"scene_{uuid.uuid4().hex[:6]}",
        description="Mã định danh duy nhất của scene",
    )
    title: str = Field(default="", description="Tiêu đề scene")
    duration_ms: int = Field(default=5000, gt=0, description="Thời lượng cảnh (ms)")
    narration_text: str = Field(default="", description="Câu thoại thuyết minh của cảnh")
    canvas: CanvasSchema = Field(
        default_factory=lambda: CanvasSchema(width=1920, height=1080),
        description="Thông số kích thước canvas chuẩn",
    )
    scene_graph: SceneGraph = Field(
        default_factory=SceneGraph,
        description="Đồ thị cảnh trực quan (Entities + Relationships)",
    )
    drawing_actions: List[DrawingAction] = Field(
        default_factory=list,
        description="Chuỗi hành động vẽ trên bảng trắng tương ứng",
    )


class VisualPlanOutput(BaseModel):
    """Output chuẩn hóa từ VisualPlannerAgent theo đặc tả Phase 04."""
    project_title: str = Field(default="", description="Tiêu đề tổng thể dự án")
    scenes: List[SceneVisualPlan] = Field(
        default_factory=list,
        description="Danh sách kế hoạch trực quan cho từng scene",
    )
    notes: str = Field(default="", description="Ghi chú mỹ thuật bổ trợ")
