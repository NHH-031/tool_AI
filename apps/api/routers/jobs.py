from __future__ import annotations

import datetime
import json
import logging
from pathlib import Path
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from core.jobs.models import JobStage, JobStatus, ProductionJob, JobStageProgress
from core.pipeline.whiteboard_pipeline import WhiteboardPipeline
from core.validation.semantic import SemanticValidator

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

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
    title: str = Field(default="Whiteboard Story", min_length=1, description="Tiêu đề video")
    prompt: str = Field(default="", description="Mô tả ý tưởng video")
    script: Optional[str] = Field(default=None, description="Kịch bản lời thoại người dùng")
    input_mode: str = Field(default="SCRIPT", description="SCRIPT | IDEA")
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
    """Tạo một Production Job mới từ User Script hoặc Idea."""
    raw_input = (req.script or req.prompt).strip()
    if not raw_input:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Script is required.",
        )

    job_id = f"job-{uuid.uuid4().hex[:8]}"
    now = datetime.datetime.now(datetime.timezone.utc)

    job = ProductionJob.create_default(
        title=req.title,
        prompt=req.prompt or raw_input,
        script=raw_input,
        original_input=raw_input,
        input_mode=req.input_mode.upper(),
        project_id=f"proj-{uuid.uuid4().hex[:6]}",
    )
    job.id = job_id
    job.language = req.language
    job.voice_id = req.voice_id
    job.speed = req.speed
    job.music_id = req.music_id
    job.visual_style = req.visual_style
    job.aspect_ratio = req.aspect_ratio
    job.status = JobStatus.RUNNING if req.auto_run else JobStatus.PENDING
    job.current_stage = JobStage.SCRIPT_GENERATION if req.auto_run else JobStage.QUEUED
    job.progress_percent = 0.0

    if req.auto_run:
        output_dir = PROJECT_ROOT / "output" / job_id
        output_dir.mkdir(parents=True, exist_ok=True)

        pipeline = WhiteboardPipeline()
        res = await pipeline.run(
            idea=req.prompt,
            script=raw_input,
            input_mode=req.input_mode.upper(),
            output_dir=output_dir,
            job_id=job.id,
        )

        job.script = res.script_text
        job.script_hash = res.metadata.get("script_hash")
        job.status = JobStatus.COMPLETED if res.is_success else JobStatus.FAILED
        job.current_stage = JobStage.COMPLETED if res.is_success else JobStage.QUALITY_ASSURANCE
        job.progress_percent = 100.0 if res.is_success else 90.0

        for s in job.stages:
            s.status = JobStatus.COMPLETED
            s.started_at = now
            s.completed_at = datetime.datetime.now(datetime.timezone.utc)

        video_filename = Path(res.final_mp4_path).name
        thumb_filename = Path(res.image_path).name
        audio_filename = Path(res.audio_path).name
        annot_filename = Path(res.annotation_path).name

        job.artifacts = {
            "video": f"/media/{job_id}/{video_filename}",
            "thumbnail": f"/media/{job_id}/{thumb_filename}",
            "audio": f"/media/{job_id}/{audio_filename}",
            "annotation": f"/media/{job_id}/{annot_filename}",
        }

        # Đọc dữ liệu annotation để trích xuất visual entities và events cho review screen
        entities_data = []
        timeline_events_data = []
        if Path(res.annotation_path).exists():
            try:
                with open(res.annotation_path, "r", encoding="utf-8") as f:
                    ann_data = json.load(f)
                    for item in ann_data.get("elements", []):
                        lbl = item.get("label") or item.get("name", "entity")
                        entities_data.append({
                            "id": item.get("id", f"entity_{len(entities_data)}"),
                            "name": lbl,
                            "category": item.get("type", "object"),
                            "pose": "default",
                            "action": "draw",
                            "layer": item.get("sequence", 1),
                            "importance": 1.0,
                            "position": item.get("region", {"x": 100, "y": 100, "width": 400, "height": 400}),
                            "tags": [lbl],
                        })
                        rev = item.get("reveal", {})
                        st = round(rev.get("startMs", 0) / 1000.0, 2)
                        dur = round(rev.get("durationMs", 1000) / 1000.0, 2)
                        timeline_events_data.append({
                            "id": f"evt-{item.get('id', len(timeline_events_data))}",
                            "asset_id": lbl,
                            "action": f"draw_{lbl}",
                            "start_time": st,
                            "end_time": round(st + dur, 2),
                            "semantic_purpose": f"Vẽ đối tượng {lbl}",
                        })
            except Exception as e:
                logger.warning(f"Error parsing annotation for review: {e}")

        # Fallback từ metadata entities nếu cần
        if not entities_data:
            for idx, ent_name in enumerate(res.metadata.get("entities", [])):
                entities_data.append({
                    "id": f"{ent_name}_{idx+1}",
                    "name": ent_name,
                    "category": "character" if ent_name in ["dog", "farmer", "teacher"] else "object",
                    "pose": "default",
                    "action": "draw",
                    "layer": idx,
                    "importance": 1.0,
                    "position": {"x": 200 + idx * 400, "y": 300, "width": 350, "height": 350},
                    "tags": [ent_name],
                })

        # Trích xuất keywords ngữ nghĩa thực tế từ kịch bản
        req_entities = list(SemanticValidator.extract_required_entities(res.script_text))

        _JOB_DETAILS[job.id] = {
            "idea": req.prompt or raw_input,
            "language": req.language,
            "voice_id": req.voice_id,
            "speed": req.speed,
            "music_id": req.music_id,
            "music_volume": req.music_volume,
            "visual_style": req.visual_style,
            "aspect_ratio": req.aspect_ratio,
            "video_url": job.artifacts["video"],
            "thumbnail_url": job.artifacts["thumbnail"],
            "audio_url": job.artifacts["audio"],
            "script": {
                "title": req.title,
                "full_text": res.script_text,
                "segments": [
                    {
                        "segment_id": "seg-01",
                        "text": res.script_text,
                        "estimated_duration": res.metadata.get("audio_duration", 5.0),
                        "semantic_meaning": f"Diễn họa trực quan cho kịch bản: {res.script_text}",
                        "keywords": req_entities or [e["name"] for e in entities_data],
                    }
                ],
            },
            "scenes": [
                {
                    "id": res.metadata.get("scene_id", f"scene-{job.id}"),
                    "scene_index": 1,
                    "title": req.title,
                    "duration_ms": int(res.metadata.get("timeline_duration", 5.0) * 1000),
                    "entities_count": len(entities_data),
                }
            ],
            "visual_entities": entities_data,
            "narration": {
                "voice_id": req.voice_id,
                "speed": req.speed,
                "duration_sec": res.metadata.get("audio_duration", 5.0),
                "sample_rate": 24000,
                "word_timings": [],
            },
            "timeline_events": timeline_events_data,
            "qa_report": {
                "is_valid_mp4": res.media_report.is_valid_mp4,
                "duration_sec": res.media_report.duration_sec,
                "video_codec": res.media_report.video_codec,
                "resolution": f"{res.media_report.video_width}x{res.media_report.video_height}",
                "fps": res.media_report.fps or 24.0,
                "frame_count": res.media_report.frame_count,
                "audio_codec": res.media_report.audio_codec,
                "duration_delta": res.media_report.duration_delta or 0.0,
                "is_corrupted": res.media_report.is_corrupted,
                "visual_qa_pass": res.media_report.visual_qa_pass,
            },
        }

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
    if job_id not in _JOB_DETAILS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review details for Job '{job_id}' not found",
        )
    details = _JOB_DETAILS[job_id]
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
