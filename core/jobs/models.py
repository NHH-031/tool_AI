from __future__ import annotations

import datetime
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobStage(str, Enum):
    QUEUED = "queued"
    SCRIPT_GENERATION = "script_generation"
    NARRATION_SYNTHESIS = "narration_synthesis"
    VISUAL_PLANNING = "visual_planning"
    ASSET_GENERATION = "asset_generation"
    TIMELINE_ANNOTATION = "timeline_annotation"
    WHITEBOARD_RENDERING = "whiteboard_rendering"
    AUDIO_COMPOSITING = "audio_compositing"
    QUALITY_ASSURANCE = "quality_assurance"
    COMPLETED = "completed"


class JobStageProgress(BaseModel):
    stage: JobStage
    status: JobStatus = JobStatus.PENDING
    started_at: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None
    error: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class ProductionJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Mã định danh job duy nhất")
    title: str = Field(description="Tiêu đề dự án video")
    prompt: str = Field(default="", description="Yêu cầu / ý tưởng kịch bản ban đầu của người dùng")
    status: JobStatus = Field(default=JobStatus.PENDING, description="Trạng thái thực thi hiện tại")
    current_stage: JobStage = Field(default=JobStage.QUEUED, description="Giai đoạn pipeline đang thực hiện")
    progress_percent: float = Field(default=0.0, ge=0.0, le=100.0, description="Tiến độ tổng thể 0-100%")
    stages: List[JobStageProgress] = Field(default_factory=list, description="Chi tiết tiến trình từng bước")
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    artifacts: Dict[str, str] = Field(default_factory=dict, description="Danh sách các file artifact sinh ra (script, mp4, preview)")
    error_message: Optional[str] = Field(default=None, description="Chi tiết thông báo lỗi nếu thất bại")

    @classmethod
    def create_default(cls, title: str, prompt: str = "") -> ProductionJob:
        stages = [
            JobStageProgress(stage=s)
            for s in [
                JobStage.SCRIPT_GENERATION,
                JobStage.NARRATION_SYNTHESIS,
                JobStage.VISUAL_PLANNING,
                JobStage.ASSET_GENERATION,
                JobStage.TIMELINE_ANNOTATION,
                JobStage.WHITEBOARD_RENDERING,
                JobStage.AUDIO_COMPOSITING,
                JobStage.QUALITY_ASSURANCE,
            ]
        ]
        return cls(title=title, prompt=prompt, stages=stages)

    def transition_to(self, stage: JobStage, status: JobStatus = JobStatus.RUNNING) -> None:
        self.current_stage = stage
        self.status = status
        self.updated_at = datetime.datetime.now(datetime.timezone.utc)
        for s in self.stages:
            if s.stage == stage:
                s.status = status
                if status == JobStatus.RUNNING and not s.started_at:
                    s.started_at = self.updated_at
                elif status in (JobStatus.COMPLETED, JobStatus.FAILED):
                    s.completed_at = self.updated_at
