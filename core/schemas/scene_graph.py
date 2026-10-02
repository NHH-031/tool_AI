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
    label: str = Field(default="", description="Nhãn danh từ mô tả đối tượng (ví dụ: 'monkey', 'tree')")
    name: Optional[str] = Field(default=None, description="Tên thực thể (alias cho label)")
    category: Literal["character", "structure", "object", "diagram", "metaphor", "text", "background"] = Field(
        default="object",
        description="Phân loại ngữ nghĩa của đối tượng",
    )
    visual_type: Literal["character", "object", "diagram", "metaphor", "structure", "background", "text"] = Field(
        default="object",
        description="Kiểu thị giác chi tiết (tránh dùng text làm phần tử chính)",
    )
    importance: Literal["primary", "secondary", "background"] = Field(
        default="primary",
        description="Mức độ quan trọng trong khung hình",
    )
    drawing_intent: str = Field(
        default="",
        description="Ý đồ phác thảo thị giác (line art style, sketch instructions)",
    )
    actions: List[str] = Field(
        default_factory=list,
        description="Các động tác hoặc chuyển động thực thể thực hiện",
    )
    action: Optional[str] = Field(default=None, description="Hành động đơn lẻ đại diện")
    position: Position = Field(
        default_factory=lambda: Position(x=0, y=0, width=500, height=500),
        description="Vị trí và kích thước trên canvas",
    )
    layer: int = Field(default=0, ge=0, description="Thứ tự lớp vẽ (0 = nền, số cao hơn đè lên)")
    start_ms: int = Field(default=0, ge=0, description="Mốc thời gian bắt đầu xuất hiện (ms)")
    duration_ms: int = Field(default=1000, gt=0, description="Thời lượng vẽ/hiển thị đối tượng (ms)")
    asset_id: Optional[str] = Field(default=None, description="Mã tham chiếu Asset ảnh mẫu nếu có")
    visual_style: Dict[str, Any] = Field(default_factory=dict, description="Thuộc tính style tùy biến")

    def model_post_init(self, __context: Any) -> None:
        if not self.label and self.name:
            self.label = self.name
        elif not self.name and self.label:
            self.name = self.label
        if not self.actions and self.action:
            self.actions = [self.action]
        elif not self.action and self.actions:
            self.action = self.actions[0]


class VisualRelationship(BaseModel):
    """Mối quan hệ ngữ nghĩa / hành động giữa 2 thực thể trong Scene Graph."""
    id: str = Field(default="", description="Mã định danh duy nhất của quan hệ")
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

    def model_post_init(self, __context: Any) -> None:
        if not self.id:
            self.id = f"rel_{self.source_id}_{self.relation_type}_{self.target_id}"


class SceneGraph(BaseModel):
    """Mạng đồ thị cảnh hoàn chỉnh chứa các thực thể và quan hệ liên kết."""
    scene_id: str = Field(default="scene_default", description="Mã định danh phân cảnh")
    entities: List[VisualEntity] = Field(
        default_factory=list, description="Danh sách các đối tượng thị giác trong cảnh"
    )
    relationships: List[VisualRelationship] = Field(
        default_factory=list, description="Danh sách các mối quan hệ ngữ nghĩa giữa các đối tượng"
    )

    def add_entity(self, entity: VisualEntity) -> None:
        """Thêm thực thể vào scene graph."""
        self.entities.append(entity)

    def add_relationship(self, relationship: VisualRelationship) -> None:
        """Thêm mối quan hệ vào scene graph."""
        self.relationships.append(relationship)

    def get_entity(self, entity_id: str) -> Optional[VisualEntity]:
        for e in self.entities:
            if e.id == entity_id:
                return e
        return None

    def get_relationships_for(self, entity_id: str) -> List[VisualRelationship]:
        return [r for r in self.relationships if r.source_id == entity_id or r.target_id == entity_id]
