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
