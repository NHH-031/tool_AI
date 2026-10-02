from __future__ import annotations

import datetime
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/projects", tags=["Projects"])


class ProjectSummary(BaseModel):
    id: str
    title: str
    description: str = ""
    aspect_ratio: str = "16:9"
    template_id: str = "notion_minimal"
    status: str = "completed"
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_sec: float = 5.3
    scene_count: int = 1
    created_at: str
    updated_at: str


# In-memory store initialized with Phase 9 demo project
_PROJECTS_DB: Dict[str, ProjectSummary] = {
    "proj-monkey-banana-01": ProjectSummary(
        id="proj-monkey-banana-01",
        title="Con khỉ trèo cây lấy chuối",
        description="Demo sản xuất nội dung Whiteboard hoạt hình tự động từ ý tưởng đến video MP4 Full HD.",
        aspect_ratio="16:9",
        template_id="notion_minimal",
        status="completed",
        video_url="/media/monkey_banana_e2e/scene_default_final.mp4",
        thumbnail_url="/media/monkey_banana_e2e/scene_default.png",
        duration_sec=5.3,
        scene_count=1,
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )
}


class CreateProjectRequest(BaseModel):
    title: str = Field(min_length=1)
    description: str = ""
    template_id: str = "notion_minimal"
    aspect_ratio: str = "16:9"


@router.get("", response_model=List[ProjectSummary])
async def list_projects() -> List[ProjectSummary]:
    """Trả về danh sách các dự án video Whiteboard."""
    return list(_PROJECTS_DB.values())


@router.post("", response_model=ProjectSummary, status_code=status.HTTP_201_CREATED)
async def create_project(req: CreateProjectRequest) -> ProjectSummary:
    """Tạo mới một dự án video Whiteboard."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    proj_id = f"proj-{int(datetime.datetime.now().timestamp())}"
    proj = ProjectSummary(
        id=proj_id,
        title=req.title,
        description=req.description,
        template_id=req.template_id,
        aspect_ratio=req.aspect_ratio,
        status="draft",
        video_url=None,
        thumbnail_url=None,
        duration_sec=0.0,
        scene_count=1,
        created_at=now,
        updated_at=now,
    )
    _PROJECTS_DB[proj_id] = proj
    return proj


@router.get("/{project_id}", response_model=ProjectSummary)
async def get_project(project_id: str) -> ProjectSummary:
    """Lấy chi tiết dự án theo ID."""
    if project_id not in _PROJECTS_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found",
        )
    return _PROJECTS_DB[project_id]
