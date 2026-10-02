from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from .annotation import RegionSchema


class Position(RegionSchema):
    """Vị trí và kích thước hình học tuyệt đối của phần tử trên canvas."""
    pass


class VisualEntity(BaseModel):
    """Đối tượng thị giác trong Scene Graph."""
    id: str = Field(description="Mã định danh duy nhất của thực thể trong scene")
    label: str = Field(description="Nhãn danh từ mô tả đối tượng (ví dụ: 'monkey', 'tree')")
    category: Literal["character", "structure", "object", "text", "background"] = Field(
        default="object",
        description="Phân loại ngữ nghĩa của đối tượng",
    )
    position: Position = Field(description="Vị trí và kích thước trên canvas")
    layer: int = Field(default=0, ge=0, description="Thứ tự lớp vẽ (0 = nền, số cao hơn đè lên)")
    start_ms: int = Field(default=0, ge=0, description="Mốc thời gian bắt đầu xuất hiện (ms)")
    duration_ms: int = Field(default=1000, gt=0, description="Thời lượng vẽ/hiển thị đối tượng (ms)")
    asset_id: Optional[str] = Field(default=None, description="Mã tham chiếu Asset ảnh mẫu nếu có")
    visual_style: Dict[str, Any] = Field(default_factory=dict, description="Thuộc tính style tùy biến")


class VisualRelationship(BaseModel):
    """Mối quan hệ ngữ nghĩa / hành động giữa 2 thực thể trong Scene Graph."""
    id: str = Field(description="Mã định danh duy nhất của quan hệ")
    source_id: str = Field(description="Mã ID của thực thể chủ động / chủ thể")
    target_id: str = Field(description="Mã ID của thực thể bị tác động / đối tượng")
    relation_type: str = Field(
        description="Loại quan hệ vị từ (ví dụ: 'climbing', 'reaching', 'located_on', 'holding')"
    )
    action: Optional[str] = Field(
        default=None,
        description="Hành động cụ thể nếu có (ví dụ: 'leo trèo', 'với tay')",
    )
    start_ms: Optional[int] = Field(default=None, ge=0, description="Thời điểm bắt đầu tương tác")
    end_ms: Optional[int] = Field(default=None, ge=0, description="Thời điểm kết thúc tương tác")
    description: str = Field(default="", description="Mô tả diễn giải quan hệ")


class SceneGraph(BaseModel):
    """Mạng đồ thị cảnh hoàn chỉnh chứa các thực thể và quan hệ liên kết."""
    entities: List[VisualEntity] = Field(
        default_factory=list, description="Danh sách các đối tượng thị giác trong cảnh"
    )
    relationships: List[VisualRelationship] = Field(
        default_factory=list, description="Danh sách các mối quan hệ ngữ nghĩa giữa các đối tượng"
    )

    def get_entity(self, entity_id: str) -> Optional[VisualEntity]:
        for e in self.entities:
            if e.id == entity_id:
                return e
        return None

    def get_relationships_for(self, entity_id: str) -> List[VisualRelationship]:
        return [r for r in self.relationships if r.source_id == entity_id or r.target_id == entity_id]
