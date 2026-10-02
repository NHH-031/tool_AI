from __future__ import annotations

import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from .annotation import AnnotationSchema, CanvasSchema
from .audio import AudioTrack, NarrationSegment
from .drawing import DrawingAction
from .scene_graph import SceneGraph
from .timeline import TimelineEvent


class Asset(BaseModel):
    """File tài nguyên thuộc sở hữu của dự án (hình ảnh, âm thanh, font, config)."""
    id: str = Field(description="Mã định danh duy nhất của Asset")
    name: str = Field(description="Tên hiển thị của file tài nguyên")
    asset_type: Literal["image", "audio", "font", "json", "video"] = Field(
        description="Phân loại tài nguyên",
    )
    file_path_or_uri: str = Field(description="Đường dẫn cục bộ hoặc URI lưu trữ")
    mime_type: str = Field(default="application/octet-stream", description="Định dạng MIME")
    file_size_bytes: int = Field(default=0, ge=0, description="Dung lượng file tính bằng byte")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata mở rộng")


class VideoTemplate(BaseModel):
    """Mẫu định dạng thiết lập mỹ thuật và quy chuẩn render của video."""
    id: str = Field(description="Mã định danh template")
    name: str = Field(description="Tên template (ví dụ: 'notion_minimal_whiteboard')")
    description: str = Field(default="", description="Mô tả phong cách")
    canvas: CanvasSchema = Field(
        default_factory=lambda: CanvasSchema(width=1672, height=941),
        description="Kích thước khung hình mặc định",
    )
    default_fps: int = Field(default=60, ge=15, le=120, description="Tốc độ khung hình")
    bg_color_hex: str = Field(default="#F6F1E3", description="Màu nền giấy mặc định")
    font_family: str = Field(default="Microsoft YaHei", description="Phông chữ mặc định")
    text_required: bool = Field(
        default=False,
        description="Quy định hình ảnh vẽ phác thảo có được chứa chữ viết hay không",
    )


class RenderArtifact(BaseModel):
    """Sản phẩm kết xuất sau quá trình xử lý của Media Engine."""
    id: str = Field(description="Mã artifact")
    artifact_type: Literal[
        "preview_png", "scene_mp4", "final_mp4", "audio_mp3", "annotation_json"
    ] = Field(description="Loại file thành phẩm")
    file_path: str = Field(description="Đường dẫn lưu file trên đĩa")
    file_size_bytes: int = Field(default=0, ge=0, description="Dung lượng byte")
    duration_ms: int = Field(default=0, ge=0, description="Thời lượng nếu là media")
    resolution: str = Field(default="1080x600", description="Độ phân giải video/ảnh")
    checksum: str = Field(default="", description="Mã băm SHA256 kiểm tra tính toàn vẹn")


class QAResult(BaseModel):
    """Kết quả thẩm định chất lượng tự động sau khi kết xuất."""
    is_valid: bool = Field(description="Đạt chuẩn phát hành hay không")
    checks_passed: List[str] = Field(default_factory=list, description="Danh mục các bài kiểm tra đã pass")
    errors: List[str] = Field(default_factory=list, description="Danh sách lỗi phát hiện")
    warnings: List[str] = Field(default_factory=list, description="Danh sách cảnh báo")
    visual_leak_detected: bool = Field(default=False, description="Có phát hiện lộ nét vẽ sớm hay không")
    mask_invariants_preserved: bool = Field(
        default=True, description="Tính bất biến che chắn allowed_mask có được bảo toàn"
    )
    audio_sync_drift_ms: float = Field(default=0.0, description="Độ lệch giữa audio và video (ms)")
    semantic_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Điểm số khớp ngữ nghĩa (0-1)")


class Scene(BaseModel):
    """Một phân cảnh độc lập trong tổng thể kịch bản video."""
    id: str = Field(description="Mã định danh duy nhất của scene (ví dụ: 'scene-01')")
    scene_index: int = Field(ge=1, description="Thứ tự phân cảnh (1..N)")
    title: str = Field(default="", description="Tiêu đề phân cảnh")
    canvas: CanvasSchema = Field(description="Kích thước canvas riêng của cảnh")
    duration_ms: int = Field(gt=0, description="Tổng thời lượng phân cảnh (ms)")
    scene_graph: SceneGraph = Field(default_factory=SceneGraph, description="Đồ thị thực thể và quan hệ")
    narration: List[NarrationSegment] = Field(default_factory=list, description="Các đoạn thuyết minh trong cảnh")
    drawing_actions: List[DrawingAction] = Field(
        default_factory=list, description="Các hành động hạ nét/tô màu"
    )
    timeline_events: List[TimelineEvent] = Field(
        default_factory=list, description="Dòng thời gian sự kiện tổng hợp"
    )
    audio_tracks: List[AudioTrack] = Field(
        default_factory=list, description="Các track âm thanh tương ứng"
    )
    annotation: Optional[AnnotationSchema] = Field(
        default=None, description="Cấu hình annotation tương thích ngược với Whiteboard Engine"
    )


class Project(BaseModel):
    """Dự án sản xuất video Whiteboard hoàn chỉnh."""
    id: str = Field(description="Mã định danh dự án duy nhất")
    title: str = Field(description="Tiêu đề dự án")
    description: str = Field(default="", description="Mô tả ý tưởng dự án")
    template: VideoTemplate = Field(
        default_factory=lambda: VideoTemplate(id="default_template", name="Standard Notion Whiteboard"),
        description="Mẫu thiết lập visual và canvas",
    )
    scenes: List[Scene] = Field(default_factory=list, description="Danh sách các phân cảnh theo thứ tự")
    assets: List[Asset] = Field(default_factory=list, description="Kho tài nguyên đính kèm dự án")
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    updated_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    def get_scene(self, scene_id: str) -> Optional[Scene]:
        for s in self.scenes:
            if s.id == scene_id:
                return s
        return None

    def get_asset(self, asset_id: str) -> Optional[Asset]:
        for a in self.assets:
            if a.id == asset_id:
                return a
        return None
