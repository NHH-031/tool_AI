from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple, Union
from pydantic import BaseModel, Field

from .annotation import RegionSchema


class Position(RegionSchema):
    """Vị trí và kích thước hình học tuyệt đối của phần tử trên canvas."""
    pass


class VisualAction(BaseModel):
    """Hành động thị giác độc lập hoặc liên kết của thực thể trong phân cảnh (First-class Action)."""
    model_config = {"populate_by_name": True}

    id: str = Field(default="", description="Mã định danh duy nhất của hành động")
    entity_id: str = Field(description="Mã ID của thực thể thực hiện hành động", alias="entityId")
    action_type: str = Field(description="Loại hành động (climbing, reaching, running, chasing, etc.)", alias="actionType")
    motion_path: List[Tuple[float, float]] = Field(default_factory=list, description="Quỹ đạo chuyển động nếu có", alias="motionPath")
    start_constraint: Optional[str] = Field(default=None, description="Ràng buộc thời điểm bắt đầu", alias="startConstraint")
    end_constraint: Optional[str] = Field(default=None, description="Ràng buộc thời điểm kết thúc", alias="endConstraint")
    required: bool = Field(default=True, description="Hành động bắt buộc phải thể hiện trong video")
    completed: bool = Field(default=False, description="Trạng thái đã được thể hiện hoàn tất trên video")

    def model_post_init(self, __context: Any) -> None:
        if not self.id:
            self.id = f"act_{self.entity_id}_{self.action_type}"


class VisualEntity(BaseModel):
    """Đối tượng thị giác trong Scene Graph với đầy đủ metadata vẽ và tính hoàn thiện (Completeness)."""
    model_config = {"populate_by_name": True}

    id: str = Field(description="Mã định danh duy nhất của thực thể trong scene")
    label: str = Field(default="", description="Nhãn danh từ mô tả đối tượng (ví dụ: 'monkey', 'tree')")
    name: Optional[str] = Field(default=None, description="Tên thực thể (alias cho label)")
    semantic_type: str = Field(
        default="object",
        description="Phân loại ngữ nghĩa (character, structure, object, diagram, metaphor, background, etc.)",
        alias="semanticType",
    )
    category: Literal["character", "structure", "object", "diagram", "metaphor", "text", "background"] = Field(
        default="object",
        description="Phân loại danh mục tổng quát",
    )
    visual_type: Literal["character", "object", "diagram", "metaphor", "structure", "background", "text"] = Field(
        default="object",
        description="Kiểu thị giác chi tiết",
    )
    visual_role: str = Field(
        default="primary",
        description="Vai trò trực quan trong khung cảnh (actor, target, structure, environment, metaphor)",
        alias="visualRole",
    )
    importance: Literal["primary", "secondary", "background"] = Field(
        default="primary",
        description="Mức độ quan trọng trong khung hình",
    )
    required: bool = Field(default=True, description="Thực thể bắt buộc phải xuất hiện đầy đủ trong video")
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
    region: Optional[Position] = Field(
        default=None,
        description="Vùng giới hạn trên canvas (alias cho position)",
    )
    layer: int = Field(default=0, ge=0, description="Thứ tự lớp vẽ (0 = nền, số cao hơn đè lên)")
    priority: int = Field(default=1, description="Độ ưu tiên vẽ tuần tự trong scene", alias="priority")
    start_ms: int = Field(default=0, ge=0, description="Mốc thời gian bắt đầu xuất hiện (ms)")
    duration_ms: int = Field(default=1000, gt=0, description="Thời lượng vẽ/hiển thị đối tượng (ms)")
    asset_id: Optional[str] = Field(default=None, description="Mã tham chiếu Asset ảnh mẫu nếu có", alias="assetId")
    asset_variant: Optional[str] = Field(default=None, description="Biến thể asset (pose/variant)", alias="assetVariant")
    pose: Optional[str] = Field(default=None, description="Tư thế thực thể")
    visual_style: Dict[str, Any] = Field(default_factory=dict, description="Thuộc tính style tùy biến")

    # Tracking tính hoàn thiện nét vẽ & Asset Completeness (Section 8)
    asset_resolved: bool = Field(
        default=False,
        description="Đã tìm thấy asset vector tương ứng",
        alias="assetResolved",
    )
    vector_available: bool = Field(
        default=False,
        description="Đã sẵn sàng file SVG vector chuẩn",
        alias="vectorAvailable",
    )
    stroke_plan_available: bool = Field(
        default=False,
        description="Đã trích xuất thành công kế hoạch nét vẽ",
        alias="strokePlanAvailable",
    )
    stroke_count: int = Field(
        default=0,
        description="Tổng số nét vẽ bắt buộc",
        alias="strokeCount",
    )
    completed_stroke_count: int = Field(
        default=0,
        description="Số nét vẽ đã hoàn thành",
        alias="completedStrokeCount",
    )
    required_stroke_ids: List[str] = Field(
        default_factory=list,
        description="Danh sách ID các nét vẽ bắt buộc để hoàn thành đối tượng",
        alias="requiredStrokeIds",
    )
    completed_stroke_ids: List[str] = Field(
        default_factory=list,
        description="Danh sách ID các nét vẽ đã hoàn thành trên video",
        alias="completedStrokeIds",
    )
    completion_ratio: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Tỉ lệ hoàn thiện nét vẽ (1.0 = 100% hoàn tất)",
        alias="completionRatio",
    )

    def model_post_init(self, __context: Any) -> None:
        if not self.label and self.name:
            self.label = self.name
        elif not self.name and self.label:
            self.name = self.label
        if not self.actions and self.action:
            self.actions = [self.action]
        elif not self.action and self.actions:
            self.action = self.actions[0]
        if self.region is not None:
            self.position = self.region
        elif self.position is not None:
            self.region = self.position
        if not self.pose and self.action:
            self.pose = self.action

    def update_stroke_progress(self, completed_ids: List[str]) -> None:
        """Cập nhật tiến độ hoàn thành các nét vẽ."""
        self.completed_stroke_ids = list(set(completed_ids))
        if self.required_stroke_ids:
            completed_set = set(self.completed_stroke_ids)
            done = sum(1 for sid in self.required_stroke_ids if sid in completed_set)
            self.completion_ratio = round(done / len(self.required_stroke_ids), 3)
        else:
            self.completion_ratio = 1.0 if self.completed_stroke_ids else 0.0


class VisualRelationship(BaseModel):
    """Mối quan hệ ngữ nghĩa / tương tác giữa 2 thực thể trong Scene Graph."""
    model_config = {"populate_by_name": True}

    id: str = Field(default="", description="Mã định danh duy nhất của quan hệ")
    source_id: str = Field(default="", description="Mã ID của thực thể chủ động / chủ thể", alias="sourceEntityId")
    target_id: str = Field(default="", description="Mã ID của thực thể bị tác động / đối tượng", alias="targetEntityId")
    relation_type: str = Field(
        default="",
        description="Loại quan hệ vị từ (ví dụ: 'climbing', 'reaching', 'located_on', 'chasing')",
        alias="relationType",
    )
    visual_representation: str = Field(
        default="",
        description="Cách thức thể hiện trực quan quan hệ (motion, connection line, contact pose)",
        alias="visualRepresentation",
    )
    required: bool = Field(default=True, description="Quan hệ bắt buộc phải được biểu diễn")
    action: Optional[str] = Field(
        default=None,
        description="Hành động cụ thể nếu có (ví dụ: 'leo trèo', 'với tay')",
    )
    start_ms: Optional[int] = Field(default=None, ge=0, description="Thời điểm bắt đầu tương tác")
    end_ms: Optional[int] = Field(default=None, ge=0, description="Thời điểm kết thúc tương tác")
    description: str = Field(default="", description="Mô tả diễn giải quan hệ")

    def model_post_init(self, __context: Any) -> None:
        if not self.id and self.source_id and self.target_id:
            self.id = f"rel_{self.source_id}_{self.relation_type}_{self.target_id}"

    @property
    def sourceEntityId(self) -> str:
        return self.source_id

    @property
    def targetEntityId(self) -> str:
        return self.target_id

    @property
    def relationType(self) -> str:
        return self.relation_type


class SceneGraph(BaseModel):
    """Mạng đồ thị cảnh hoàn chỉnh chứa các thực thể, quan hệ, hành động và yêu cầu trực quan."""
    model_config = {"populate_by_name": True}

    scene_id: str = Field(default="scene_default", description="Mã định danh phân cảnh", alias="sceneId")
    narration: str = Field(default="", description="Lời thuyết minh của cảnh")
    description: str = Field(default="", description="Mô tả phân cảnh")
    entities: List[VisualEntity] = Field(
        default_factory=list, description="Danh sách các đối tượng thị giác trong cảnh"
    )
    relationships: List[VisualRelationship] = Field(
        default_factory=list, description="Danh sách các mối quan hệ ngữ nghĩa giữa các đối tượng"
    )
    actions: List[VisualAction] = Field(
        default_factory=list, description="Danh sách các hành động thị giác cần thực hiện"
    )
    visual_requirements: List[str] = Field(
        default_factory=list, description="Danh sách các yêu cầu thị giác cốt lõi", alias="visualRequirements"
    )
    text_requirements: List[str] = Field(
        default_factory=list, description="Danh sách chữ viết nếu thật sự cần thiết", alias="textRequirements"
    )
    timing: Dict[str, Any] = Field(
        default_factory=dict, description="Metadata điều phối thời gian của cảnh"
    )

    def model_post_init(self, __context: Any) -> None:
        if not self.narration and self.description:
            self.narration = self.description
        elif not self.description and self.narration:
            self.description = self.narration

    def add_entity(self, entity: VisualEntity) -> None:
        """Thêm thực thể vào scene graph."""
        self.entities.append(entity)

    def add_relationship(self, relationship: VisualRelationship) -> None:
        """Thêm mối quan hệ vào scene graph."""
        self.relationships.append(relationship)

    def add_action(self, action: VisualAction) -> None:
        """Thêm hành động vào scene graph."""
        self.actions.append(action)

    def get_entity(self, entity_id: str) -> Optional[VisualEntity]:
        for e in self.entities:
            if e.id == entity_id:
                return e
        return None

    def get_relationships_for(self, entity_id: str) -> List[VisualRelationship]:
        return [r for r in self.relationships if r.source_id == entity_id or r.target_id == entity_id]

    def get_actions_for(self, entity_id: str) -> List[VisualAction]:
        return [a for a in self.actions if a.entity_id == entity_id]


# Alias theo đặc tả Phase 10.1
Scene = SceneGraph
