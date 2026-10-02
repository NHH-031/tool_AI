from __future__ import annotations

from typing import Dict, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from core.jobs.models import JobStage, JobStatus, ProductionJob

router = APIRouter(prefix="/jobs", tags=["Jobs"])

# In-memory store for skeleton/Phase 2 demo
_JOBS_DB: Dict[str, ProductionJob] = {}


class CreateJobRequest(BaseModel):
    title: str = Field(min_length=1, description="Tiêu đề video")
    prompt: str = Field(default="", description="Mô tả ý tưởng video")


@router.post("", response_model=ProductionJob, status_code=status.HTTP_201_CREATED)
async def create_job(req: CreateJobRequest) -> ProductionJob:
    """Tạo một Production Job mới."""
    job = ProductionJob.create_default(title=req.title, prompt=req.prompt)
    _JOBS_DB[job.id] = job
    return job


@router.get("", response_model=List[ProductionJob])
async def list_jobs() -> List[ProductionJob]:
    """Liệt kê danh sách các Production Jobs."""
    return list(_JOBS_DB.values())


@router.get("/{job_id}", response_model=ProductionJob)
async def get_job(job_id: str) -> ProductionJob:
    """Lấy thông tin chi tiết một Production Job theo id."""
    if job_id not in _JOBS_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found",
        )
    return _JOBS_DB[job_id]
