from __future__ import annotations

from typing import List
from pydantic import BaseModel, Field


class SubtitleCue(BaseModel):
    index: int = Field(ge=1, description="Thứ tự dòng phụ đề")
    startMs: int = Field(ge=0, description="Mốc bắt đầu (ms)")
    endMs: int = Field(ge=0, description="Mốc kết thúc (ms)")
    durMs: int = Field(ge=0, description="Thời lượng thoại (ms)")
    text: str = Field(description="Nội dung câu thoại")


class SceneScript(BaseModel):
    sceneIndex: int = Field(ge=1, description="Số thứ tự phân cảnh")
    title: str = Field(default="", description="Tiêu đề phân cảnh")
    narrativeSummary: str = Field(default="", description="Tóm tắt ý đồ biểu đạt của cảnh")
    startMs: int = Field(ge=0, description="Mốc bắt đầu của cảnh")
    endMs: int = Field(ge=0, description="Mốc kết thúc của cảnh")
    sceneDurationMs: int = Field(gt=0, description="Tổng thời lượng cảnh (ms)")
    cueRange: List[int] = Field(default_factory=list, description="Chỉ số các câu subtitle [start, end]")
    cues: List[SubtitleCue] = Field(default_factory=list, description="Danh sách các cue phụ đề trong cảnh")


class ProductionScript(BaseModel):
    title: str = Field(description="Tiêu đề video toàn dự án")
    overview: str = Field(default="", description="Mô tả ý tưởng chung")
    targetAudience: str = Field(default="", description="Đối tượng khán giả mục tiêu")
    scenes: List[SceneScript] = Field(default_factory=list, description="Danh sách các phân cảnh")


class ScriptSegment(BaseModel):
    """Phân đoạn kịch bản có thời lượng ước tính và ngữ nghĩa (Phase 04 Script Agent output)."""
    cue_index: int = Field(default=1, ge=1, description="Thứ tự phân đoạn")
    text: str = Field(description="Nội dung câu thoại / narration text")
    estimated_duration_sec: float = Field(gt=0, description="Thời lượng ước tính (giây)")
    semantic_meaning: str = Field(
        default="",
        description="Ý nghĩa cốt lõi / thông điệp trực quan cần thể hiện",
    )
    key_entities: List[str] = Field(
        default_factory=list,
        description="Các thực thể mấu chốt được đề cập trong phân đoạn",
    )
    suggested_actions: List[str] = Field(
        default_factory=list,
        description="Các hành động cốt lõi diễn ra",
    )


class ScriptOutput(BaseModel):
    """Output chuẩn hóa từ ScriptAgent theo đặc tả Phase 04."""
    title: str = Field(description="Tiêu đề kịch bản video")
    script: str = Field(description="Toàn bộ kịch bản lời dẫn xuyên suốt (full narrative script)")
    segments: List[ScriptSegment] = Field(
        description="Danh sách các phân đoạn narration có thời lượng và ý nghĩa ngữ nghĩa",
    )
    language: str = Field(default="vi", description="Ngôn ngữ kịch bản")
    target_duration_sec: int = Field(default=30, ge=5, description="Thời lượng tổng mục tiêu (giây)")
    style: str = Field(default="educational", description="Phong cách truyền tải")

