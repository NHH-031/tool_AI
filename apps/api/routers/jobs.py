from __future__ import annotations

import datetime
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from core.jobs.models import JobStage, JobStatus, ProductionJob, JobStageProgress

router = APIRouter(prefix="/jobs", tags=["Jobs"])

# In-memory stores
_JOBS_DB: Dict[str, ProductionJob] = {}
_JOB_DETAILS: Dict[str, Dict[str, Any]] = {}


def _init_demo_job():
    job = ProductionJob.create_default(
        title="Con khỉ trèo cây lấy chuối",
        prompt="Con khỉ đang trèo lên cây để lấy một quả chuối.",
    )
    job.id = "job-monkey-banana-demo"
    job.status = JobStatus.COMPLETED
    job.current_stage = JobStage.COMPLETED
    job.progress_percent = 100.0

    now = datetime.datetime.now(datetime.timezone.utc)
    for s in job.stages:
        s.status = JobStatus.COMPLETED
        s.started_at = now - datetime.timedelta(seconds=12)
        s.completed_at = now

    job.artifacts = {
        "video": "/media/monkey_banana_e2e/scene_default_final.mp4",
        "thumbnail": "/media/monkey_banana_e2e/scene_default.png",
        "audio": "/media/monkey_banana_e2e/narration.wav",
        "annotation": "/media/monkey_banana_e2e/scene_default.annotation.json",
    }

    _JOBS_DB[job.id] = job
    _JOB_DETAILS[job.id] = {
        "idea": "Con khỉ đang trèo lên cây để lấy một quả chuối.",
        "language": "vi",
        "voice_id": "vi-VN-Standard-B",
        "speed": 1.0,
        "music_id": "whimsical_play",
        "music_volume": 0.15,
        "visual_style": "notion_minimal",
        "aspect_ratio": "16:9",
        "video_url": "/media/monkey_banana_e2e/scene_default_final.mp4",
        "thumbnail_url": "/media/monkey_banana_e2e/scene_default.png",
        "audio_url": "/media/monkey_banana_e2e/narration.wav",
        "script": {
            "title": "Con khỉ trèo cây",
            "full_text": "Con khỉ đang trèo lên cây để lấy một quả chuối.",
            "segments": [
                {
                    "segment_id": "seg-01",
                    "text": "Con khỉ đang trèo lên cây để lấy một quả chuối.",
                    "estimated_duration": 5.18,
                    "semantic_meaning": "Khỉ leo trèo hái chuối trên cây cao",
                    "keywords": ["khỉ", "trèo", "cây", "chuối"],
                }
            ],
        },
        "scenes": [
            {
                "id": "scene-01",
                "scene_index": 1,
                "title": "Chú khỉ và buồng chuối trên ngọn cây",
                "duration_ms": 5300,
                "entities_count": 3,
            }
        ],
        "visual_entities": [
            {
                "id": "entity_tree",
                "name": "tree",
                "category": "nature",
                "pose": "tall",
                "action": "standing",
                "layer": 0,
                "importance": 1.0,
                "position": {"x": 300, "y": 150, "width": 550, "height": 700},
                "tags": ["tree", "nature", "trunk", "leaves"],
            },
            {
                "id": "entity_monkey",
                "name": "monkey",
                "category": "character",
                "pose": "climbing",
                "action": "climbing",
                "layer": 1,
                "importance": 1.0,
                "position": {"x": 380, "y": 420, "width": 260, "height": 260},
                "tags": ["monkey", "climbing", "character", "animal"],
            },
            {
                "id": "entity_banana",
                "name": "banana",
                "category": "object",
                "pose": "ripe",
                "action": "hanging",
                "layer": 2,
                "importance": 0.9,
                "position": {"x": 620, "y": 280, "width": 160, "height": 160},
                "tags": ["banana", "food", "yellow", "fruit"],
            },
        ],
        "narration": {
            "voice_id": "vi-VN-Standard-B",
            "voice_name": "Nam Khánh (Bắc Bộ Trầm Ấm)",
            "speed": 1.0,
            "duration_sec": 5.182,
            "sample_rate": 24000,
            "word_timings": [
                {"word": "Con", "start_time": 0.10, "end_time": 0.35},
                {"word": "khỉ", "start_time": 0.35, "end_time": 0.70},
                {"word": "đang", "start_time": 0.85, "end_time": 1.10},
                {"word": "trèo", "start_time": 1.10, "end_time": 1.45},
                {"word": "lên", "start_time": 1.45, "end_time": 1.75},
                {"word": "cây", "start_time": 1.75, "end_time": 2.10},
                {"word": "để", "start_time": 2.20, "end_time": 2.45},
                {"word": "lấy", "start_time": 2.45, "end_time": 2.80},
                {"word": "một", "start_time": 2.80, "end_time": 3.05},
                {"word": "quả", "start_time": 3.05, "end_time": 3.35},
                {"word": "chuối.", "start_time": 3.35, "end_time": 3.75},
            ],
        },
        "timeline_events": [
            {
                "id": "evt-01",
                "asset_id": "asset_tree",
                "action": "draw_trunk_and_branches",
                "start_time": 0.10,
                "end_time": 1.10,
                "semantic_purpose": "Phác họa thân cây và cành bám",
            },
            {
                "id": "evt-02",
                "asset_id": "asset_monkey",
                "action": "draw_monkey_climbing",
                "start_time": 1.10,
                "end_time": 2.45,
                "semantic_purpose": "Vẽ tư thế chú khỉ đang leo trèo trên thân cây",
            },
            {
                "id": "evt-03",
                "asset_id": "asset_banana",
                "action": "draw_ripe_banana",
                "start_time": 2.45,
                "end_time": 3.75,
                "semantic_purpose": "Vẽ quả chuối chín vàng chú khỉ với tới",
            },
            {
                "id": "evt-04",
                "asset_id": "scene",
                "action": "final_hold",
                "start_time": 3.75,
                "end_time": 5.30,
                "semantic_purpose": "Giữ tĩnh toàn cảnh hoàn thiện",
            },
        ],
        "qa_report": {
            "is_valid_mp4": True,
            "duration_sec": 5.3,
            "video_codec": "h264",
            "resolution": "1080x600",
            "fps": 30.0,
            "frame_count": 159,
            "audio_codec": "aac",
            "audio_duration_sec": 5.182,
            "duration_delta": 0.118,
            "is_corrupted": False,
            "visual_qa_pass": True,
        },
    }


_init_demo_job()


class CreateJobRequest(BaseModel):
    title: str = Field(min_length=1, description="Tiêu đề video")
    prompt: str = Field(default="", description="Mô tả ý tưởng video")
    language: str = "vi"
    voice_id: str = "vi-VN-Standard-B"
    speed: float = 1.0
    music_id: str = "whimsical_play"
    music_volume: float = 0.15
    visual_style: str = "notion_minimal"
    aspect_ratio: str = "16:9"
    auto_run: bool = False


class RegenerateRequest(BaseModel):
    target: str = Field(
        description="Mục tiêu tái tạo: 'script' | 'scene' | 'asset' | 'voice' | 'drawing'",
    )
    instructions: Optional[str] = Field(
        default=None, description="Chỉ dẫn bổ sung khi yêu cầu làm lại"
    )


@router.post("", response_model=ProductionJob, status_code=status.HTTP_201_CREATED)
async def create_job(req: CreateJobRequest) -> ProductionJob:
    """Tạo một Production Job mới."""
    job = ProductionJob.create_default(title=req.title, prompt=req.prompt)

    job.artifacts = {
        "video": "/media/monkey_banana_e2e/scene_default_final.mp4",
        "thumbnail": "/media/monkey_banana_e2e/scene_default.png",
        "audio": "/media/monkey_banana_e2e/narration.wav",
    }

    _JOB_DETAILS[job.id] = {
        "idea": req.prompt or req.title,
        "language": req.language,
        "voice_id": req.voice_id,
        "speed": req.speed,
        "music_id": req.music_id,
        "music_volume": req.music_volume,
        "visual_style": req.visual_style,
        "aspect_ratio": req.aspect_ratio,
        "video_url": "/media/monkey_banana_e2e/scene_default_final.mp4",
        "thumbnail_url": "/media/monkey_banana_e2e/scene_default.png",
        "audio_url": "/media/monkey_banana_e2e/narration.wav",
        "script": {
            "title": req.title,
            "full_text": req.prompt or "Con khỉ đang trèo lên cây để lấy một quả chuối.",
            "segments": [
                {
                    "segment_id": "seg-01",
                    "text": req.prompt or "Con khỉ đang trèo lên cây để lấy một quả chuối.",
                    "estimated_duration": 5.18,
                    "semantic_meaning": "Tái hiện phân cảnh theo ý tưởng người dùng",
                    "keywords": ["khỉ", "cây", "chuối"],
                }
            ],
        },
        "scenes": [
            {
                "id": "scene-01",
                "scene_index": 1,
                "title": req.title,
                "duration_ms": 5300,
                "entities_count": 3,
            }
        ],
        "visual_entities": [
            {
                "id": "entity_tree",
                "name": "tree",
                "category": "nature",
                "pose": "tall",
                "action": "standing",
                "layer": 0,
                "importance": 1.0,
                "position": {"x": 300, "y": 150, "width": 550, "height": 700},
                "tags": ["tree", "nature"],
            },
            {
                "id": "entity_monkey",
                "name": "monkey",
                "category": "character",
                "pose": "climbing",
                "action": "climbing",
                "layer": 1,
                "importance": 1.0,
                "position": {"x": 380, "y": 420, "width": 260, "height": 260},
                "tags": ["monkey", "character"],
            },
            {
                "id": "entity_banana",
                "name": "banana",
                "category": "object",
                "pose": "ripe",
                "action": "hanging",
                "layer": 2,
                "importance": 0.9,
                "position": {"x": 620, "y": 280, "width": 160, "height": 160},
                "tags": ["banana", "fruit"],
            },
        ],
        "narration": {
            "voice_id": req.voice_id,
            "speed": req.speed,
            "duration_sec": 5.182,
            "sample_rate": 24000,
            "word_timings": [
                {"word": "Con", "start_time": 0.10, "end_time": 0.35},
                {"word": "khỉ", "start_time": 0.35, "end_time": 0.70},
                {"word": "đang", "start_time": 0.85, "end_time": 1.10},
                {"word": "trèo", "start_time": 1.10, "end_time": 1.45},
                {"word": "lên", "start_time": 1.45, "end_time": 1.75},
                {"word": "cây", "start_time": 1.75, "end_time": 2.10},
                {"word": "để", "start_time": 2.20, "end_time": 2.45},
                {"word": "lấy", "start_time": 2.45, "end_time": 2.80},
                {"word": "một", "start_time": 2.80, "end_time": 3.05},
                {"word": "quả", "start_time": 3.05, "end_time": 3.35},
                {"word": "chuối.", "start_time": 3.35, "end_time": 3.75},
            ],
        },
        "timeline_events": [
            {
                "id": "evt-01",
                "asset_id": "asset_tree",
                "action": "draw_trunk_and_branches",
                "start_time": 0.10,
                "end_time": 1.10,
                "semantic_purpose": "Vẽ thân cây và tán lá",
            },
            {
                "id": "evt-02",
                "asset_id": "asset_monkey",
                "action": "draw_monkey_climbing",
                "start_time": 1.10,
                "end_time": 2.45,
                "semantic_purpose": "Vẽ tư thế chú khỉ đang trèo",
            },
            {
                "id": "evt-03",
                "asset_id": "asset_banana",
                "action": "draw_ripe_banana",
                "start_time": 2.45,
                "end_time": 3.75,
                "semantic_purpose": "Vẽ quả chuối vàng",
            },
        ],
        "qa_report": {
            "is_valid_mp4": True,
            "duration_sec": 5.3,
            "video_codec": "h264",
            "resolution": "1080x600",
            "fps": 30.0,
            "frame_count": 159,
            "audio_codec": "aac",
            "duration_delta": 0.118,
            "is_corrupted": False,
            "visual_qa_pass": True,
        },
    }

    if req.auto_run:
        job.status = JobStatus.COMPLETED
        job.current_stage = JobStage.COMPLETED
        job.progress_percent = 100.0
        now = datetime.datetime.now(datetime.timezone.utc)
        for s in job.stages:
            s.status = JobStatus.COMPLETED
            s.started_at = now
            s.completed_at = now

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


@router.get("/{job_id}/review")
async def get_job_review(job_id: str) -> Dict[str, Any]:
    """Lấy toàn bộ dữ liệu chi tiết màn hình Review cho Job."""
    if job_id not in _JOBS_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found",
        )
    job = _JOBS_DB[job_id]
    details = _JOB_DETAILS.get(job_id, {})
    return {
        "job_id": job.id,
        "title": job.title,
        "status": job.status,
        "current_stage": job.current_stage,
        "progress_percent": job.progress_percent,
        "stages": [s.model_dump() for s in job.stages],
        "artifacts": job.artifacts,
        "review_data": details,
    }


@router.post("/{job_id}/regenerate", response_model=ProductionJob)
async def regenerate_component(job_id: str, req: RegenerateRequest) -> ProductionJob:
    """Tái sinh (Regenerate) một thành phần cụ thể trong pipeline (script, scene, asset, voice, drawing)."""
    if job_id not in _JOBS_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found",
        )

    job = _JOBS_DB[job_id]
    target = req.target.lower()

    stage_map = {
        "script": JobStage.SCRIPT_GENERATION,
        "scene": JobStage.VISUAL_PLANNING,
        "asset": JobStage.ASSET_GENERATION,
        "voice": JobStage.NARRATION_SYNTHESIS,
        "drawing": JobStage.WHITEBOARD_RENDERING,
    }

    target_stage = stage_map.get(target, JobStage.VISUAL_PLANNING)
    now = datetime.datetime.now(datetime.timezone.utc)

    for s in job.stages:
        if s.stage == target_stage:
            s.status = JobStatus.COMPLETED
            s.details["regenerated"] = True
            s.details["regenerated_at"] = now.isoformat()
            if req.instructions:
                s.details["instructions"] = req.instructions

    job.status = JobStatus.COMPLETED
    job.current_stage = JobStage.COMPLETED
    job.updated_at = now

    details = _JOB_DETAILS.get(job_id, {})
    if "regeneration_history" not in details:
        details["regeneration_history"] = []
    details["regeneration_history"].append(
        {
            "target": target,
            "instructions": req.instructions,
            "timestamp": now.isoformat(),
            "status": "success",
        }
    )

    return job
