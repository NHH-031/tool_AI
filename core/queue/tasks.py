from __future__ import annotations

import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    RENDER_VIDEO = "render_video"
    CONVERT_FORMAT = "convert_format"
    HANDWRITTEN_SCENE = "handwritten_scene"
    CUSTOM = "custom"


class TaskPayload(BaseModel):
    task_id: str
    task_type: str = TaskType.RENDER_VIDEO
    payload: Dict[str, Any] = Field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    stage: str = "Khởi tạo tác vụ..."
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    def mark_running(self, stage: str = "Đang xử lý...") -> None:
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.stage = stage

    def update_progress(self, progress: float, stage: Optional[str] = None) -> None:
        self.progress = max(0.0, min(100.0, round(progress, 1)))
        if stage:
            self.stage = stage

    def mark_completed(self, result: Optional[Dict[str, Any]] = None, stage: str = "Hoàn tất") -> None:
        self.status = TaskStatus.COMPLETED
        self.progress = 100.0
        self.stage = stage
        self.result = result or {}
        self.completed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def mark_failed(self, error: str, stage: str = "Tác vụ thất bại") -> None:
        self.status = TaskStatus.FAILED
        self.stage = stage
        self.error = error
        self.completed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
