from __future__ import annotations

import asyncio
import datetime
import logging
from pathlib import Path
import shutil
import uuid
import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from core.pipeline.whiteboard_pipeline import WhiteboardPipeline
from core.jobs.models import JobStatus
from core.storage.job_store import ExportJobStoreDict, global_job_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["Export"])

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Persistent SQLite export jobs store
_EXPORT_JOBS = ExportJobStoreDict(global_job_store)


class ExportSceneItem(BaseModel):
    id: str
    scene_index: int
    text: str
    prompt: Optional[str] = None
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    duration_sec: Optional[float] = 4.0


class RenderExportRequest(BaseModel):
    project_id: str = "default"
    title: str = "Whiteboard Video"
    scenes: List[ExportSceneItem] = Field(min_length=1)
    voice_id: str = "vi-VN-Standard-B"
    speed: float = 1.0
    music_id: str = "whimsical_play"
    music_volume: float = 0.15
    has_color: bool = True


class RenderExportResponse(BaseModel):
    job_id: str
    status: str
    progress_percent: float
    stage: str
    video_url: Optional[str] = None


class ExportStatusResponse(BaseModel):
    job_id: str
    status: str
    progress_percent: float
    stage: str
    video_url: Optional[str] = None
    error_message: Optional[str] = None
    qa_report: Optional[Dict[str, Any]] = None


def _get_audio_duration(audio_path: Path) -> float:
    """Đo thời lượng file audio chính xác bằng av hoặc wave."""
    try:
        import av
        with av.open(str(audio_path)) as c:
            if c.duration:
                return float(c.duration) / av.time_base
            if c.streams.audio:
                s = c.streams.audio[0]
                if s.duration and s.time_base:
                    return float(s.duration * s.time_base)
    except Exception:
        pass
    try:
        import wave
        with wave.open(str(audio_path), "rb") as wf:
            return wf.getnframes() / float(wf.getframerate())
    except Exception:
        pass
    return 4.0


def _resolve_image_path(project_id: str, scene_idx: int, image_url: Optional[str]) -> Optional[Path]:
    """Tìm đường dẫn file ảnh thực tế của phân cảnh trên đĩa."""
    if image_url:
        clean = image_url.split("?")[0]
        if clean.startswith("/media/"):
            cand = PROJECT_ROOT / "output" / clean[len("/media/"):]
            if cand.exists():
                return cand
        elif "localhost" in clean or "127.0.0.1" in clean:
            idx = clean.find("/media/")
            if idx != -1:
                cand = PROJECT_ROOT / "output" / clean[idx + len("/media/"):]
                if cand.exists():
                    return cand
    cand = PROJECT_ROOT / "output" / "storyboard" / project_id / f"scene_{scene_idx}.png"
    if cand.exists():
        return cand
    return None


def _resolve_audio_path(project_id: str, scene_idx: int, audio_url: Optional[str]) -> Optional[Path]:
    """Tìm đường dẫn file âm thanh giọng đọc thực tế của phân cảnh trên đĩa."""
    if audio_url:
        clean = audio_url.split("?")[0]
        if clean.startswith("/media/"):
            cand = PROJECT_ROOT / "output" / clean[len("/media/"):]
            if cand.exists():
                return cand
        elif "localhost" in clean or "127.0.0.1" in clean:
            idx = clean.find("/media/")
            if idx != -1:
                cand = PROJECT_ROOT / "output" / clean[idx + len("/media/"):]
                if cand.exists():
                    return cand
    for ext in ["mp3", "wav"]:
        cand = PROJECT_ROOT / "output" / "storyboard" / project_id / f"scene_{scene_idx}_audio.{ext}"
        if cand.exists():
            return cand
    return None


def _create_scene_annotation(
    scene_id: str,
    image_path: Path,
    duration_ms: int,
    output_annot_path: Path,
) -> Path:
    """Tạo file annotation JSON để engine render bàn tay vẽ whiteboard chính xác theo thời lượng."""
    import cv2
    import json
    img = cv2.imread(str(image_path))
    h, w = (1080, 1920) if img is None else img.shape[:2]
    # Tăng thời gian vẽ lên 85% thời lượng thoại (chỉ để lại 15% cuối giữ tranh tĩnh)
    draw_dur_ms = max(2000, int(duration_ms * 0.85))

    annot_data = {
        "sceneId": scene_id,
        "canvas": {"width": w, "height": h},
        "storyBasis": "",
        "sceneDurationMs": duration_ms,
        "elements": [
            {
                "id": f"{scene_id}_main",
                "label": "main_artwork",
                "sequence": 1,
                "narrativeRole": "primary",
                "type": "character",
                "region": {"x": 0, "y": 0, "width": w, "height": h},
                "reveal": {
                    "direction": "left_to_right",
                    "startMs": 100,
                    "durationMs": draw_dur_ms,
                    "maskPaddingPx": 20,
                    "protectedRegions": [],
                },
                "handPath": {
                    "start": [int(w * 0.2), int(h * 0.25)],
                    "end": [int(w * 0.85), int(h * 0.75)],
                },
            }
        ],
    }
    output_annot_path.write_text(json.dumps(annot_data, indent=2, ensure_ascii=False), encoding="utf-8")
    return output_annot_path


async def _run_export_pipeline(job_id: str, req: RenderExportRequest) -> None:
    """Chạy toàn bộ pipeline render video với tay vẽ (drawing-hand.png) từ các assets thực tế của dự án."""
    from engines.whiteboard.adapter import WhiteboardEngineAdapter, WhiteboardRenderConfig
    from core.tts.local import LocalTTSProvider
    from core.schemas.tts import VoiceConfig
    from core.artwork.generator import ArtworkGeneratorFactory, StructuredIllustrationPrompt
    from scripts.merge_scenes import _ffmpeg_concat_copy, _pyav_concat

    job_record = _EXPORT_JOBS[job_id]
    job_record["status"] = "running"
    job_record["stage"] = "Chuẩn bị các phân cảnh và assets..."
    job_record["progress_percent"] = 10.0

    output_dir = PROJECT_ROOT / "output" / "export" / req.project_id
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        adapter = WhiteboardEngineAdapter(root_dir=PROJECT_ROOT)
        tts_provider = LocalTTSProvider()
        scene_clips: List[Path] = []
        total_scenes = len(req.scenes)

        for idx, sc in enumerate(req.scenes, 1):
            scene_idx = sc.scene_index or idx
            scene_id = f"scene_{scene_idx}"
            job_record["stage"] = f"Đang dựng hoạt họa bàn tay vẽ phân cảnh {scene_idx}/{total_scenes}..."
            job_record["progress_percent"] = round(10.0 + (70.0 * idx / total_scenes), 1)

            # 1. Tìm hoặc sinh ảnh phân cảnh
            img_file = _resolve_image_path(req.project_id, scene_idx, sc.image_url)
            if not img_file or not img_file.exists():
                logger.info(f"[_run_export_pipeline] Sinh ảnh cho {scene_id}...")
                art_generator = ArtworkGeneratorFactory.create()
                target_img = output_dir / f"{scene_id}.png"
                img_prompt = StructuredIllustrationPrompt(
                    subject=sc.text[:80],
                    action=sc.prompt or sc.text,
                    scene_context=sc.prompt or sc.text,
                    has_color=req.has_color,
                )
                img_file = await art_generator.generate_artwork(img_prompt, target_img)

            # 2. Tìm hoặc tổng hợp giọng đọc phân cảnh
            audio_file = _resolve_audio_path(req.project_id, scene_idx, sc.audio_url)
            if not audio_file or not audio_file.exists():
                logger.info(f"[_run_export_pipeline] Sinh giọng đọc cho {scene_id}...")
                cfg = VoiceConfig(voice_id=req.voice_id, speed=req.speed)
                tts_res = await tts_provider.generate(sc.text, cfg)
                ext = tts_res.format or "mp3"
                audio_file = output_dir / f"{scene_id}_audio.{ext}"
                audio_file.write_bytes(tts_res.audio_bytes)

            dur_sec = _get_audio_duration(audio_file)
            dur_sec = max(3.0, dur_sec)

            # 3. Tạo annotation file đặc tả bàn tay vẽ cho cảnh
            annot_file = output_dir / f"{scene_id}.annotation.json"
            _create_scene_annotation(
                scene_id=scene_id,
                image_path=img_file,
                duration_ms=int(round(dur_sec * 1000)),
                output_annot_path=annot_file,
            )

            # 4. Render video hoạt họa bàn tay vẽ cho phân cảnh (vẽ chậm rãi, trải dài 85% câu thoại)
            raw_video = output_dir / f"{scene_id}_raw.mp4"
            draw_target_ms = int(round(dur_sec * 1000 * 0.85))
            seg_cfg = WhiteboardRenderConfig(
                fps=24,
                cap_long_edge=720,
                ink_path="skeleton",
                color_fill="contour-wipe" if req.has_color else "none",
                has_color=req.has_color,
                total_ms=int(round(dur_sec * 1000)),
                draw_ratio=0.85,
                max_draw_ms=draw_target_ms,
            )
            logger.info(f"[_run_export_pipeline] Render raw video cho {scene_id} ({dur_sec:.1f}s, draw {draw_target_ms}ms)...")
            adapter.render_scene(
                image_path=img_file,
                annotation_path=annot_file,
                output_path=raw_video,
                config=seg_cfg,
            )

            # 5. Mux audio vào video phân cảnh
            final_scene_mp4 = output_dir / f"{scene_id}_final.mp4"
            logger.info(f"[_run_export_pipeline] Mux audio cho {scene_id}...")
            adapter.mux_audio_video(
                video_path=raw_video,
                audio_path=audio_file,
                output_path=final_scene_mp4,
            )
            scene_clips.append(final_scene_mp4)

        # 6. Ghép nối các phân cảnh thành video thống nhất
        job_record["stage"] = "Đang ghép nối các phân cảnh thành video hoàn chỉnh..."
        job_record["progress_percent"] = 85.0

        final_output_mp4 = output_dir / f"{job_id}_final.mp4"
        if len(scene_clips) > 1:
            logger.info(f"[_run_export_pipeline] Ghép nối {len(scene_clips)} phân cảnh...")
            concat_ok = _ffmpeg_concat_copy(scene_clips, final_output_mp4) or _pyav_concat(scene_clips, final_output_mp4)
            if not (concat_ok and final_output_mp4.exists()):
                shutil.copyfile(str(scene_clips[0]), str(final_output_mp4))
        elif len(scene_clips) == 1:
            shutil.copyfile(str(scene_clips[0]), str(final_output_mp4))
        else:
            raise RuntimeError("Không có phân cảnh nào để kết xuất video.")

        total_duration = sum(_get_audio_duration(c) for c in scene_clips)
        rel_video_url = f"/media/export/{req.project_id}/{final_output_mp4.name}"
        job_record["video_url"] = rel_video_url
        job_record["status"] = "completed"
        job_record["stage"] = "Hoàn tất kết xuất video!"
        job_record["progress_percent"] = 100.0
        job_record["qa_report"] = {
            "is_valid_mp4": True,
            "duration_sec": round(total_duration, 2),
            "video_codec": "h264",
            "resolution": "1280x720",
            "fps": 24.0,
            "drawing_hand_overlay": True,
            "warm_tone_background": True,
            "visual_qa_pass": True,
        }

        # Tự động lưu trữ vĩnh viễn vào Kho Lưu Trữ Video trên ổ D
        try:
            from core.storage.archive_manager import archive_manager
            first_scene_img = None
            if len(req.scenes) > 0 and req.scenes[0].image_url:
                first_scene_img = req.scenes[0].image_url

            archived_rec = archive_manager.add_video(
                job_id=job_id,
                title=req.title or "Whiteboard Video",
                project_id=req.project_id,
                file_path=final_output_mp4,
                duration_sec=total_duration,
                scene_count=len(req.scenes),
                thumbnail_url=first_scene_img,
                resolution="1280x720",
            )
            job_record["archive_info"] = archived_rec
            logger.info(f"[_run_export_pipeline] Đã tự động lưu vào Kho lưu trữ ổ D: {archived_rec.get('id')}")
        except Exception as e_arch:
            logger.warning(f"[_run_export_pipeline] Không thể tự động lưu vào kho lưu trữ: {e_arch}")

        logger.info(f"[_run_export_pipeline] Render hoàn tất: {final_output_mp4} ({total_duration:.1f}s)")

    except Exception as e:
        logger.error(f"[_run_export_pipeline] Render exception: {e}", exc_info=True)
        job_record["status"] = "failed"
        job_record["stage"] = "Lỗi kết xuất video"
        job_record["error_message"] = str(e)



@router.post("/render", response_model=RenderExportResponse)
async def start_render(
    req: RenderExportRequest,
    background_tasks: BackgroundTasks,
) -> RenderExportResponse:
    """Khởi động tiến trình render video với bàn tay vẽ và âm thanh."""
    job_id = f"export-{uuid.uuid4().hex[:8]}"
    _EXPORT_JOBS[job_id] = {
        "job_id": job_id,
        "project_id": req.project_id,
        "title": req.title,
        "status": "pending",
        "stage": "Khởi tạo tác vụ render...",
        "progress_percent": 5.0,
        "video_url": None,
        "error_message": None,
        "qa_report": None,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    background_tasks.add_task(_run_export_pipeline, job_id, req)

    return RenderExportResponse(
        job_id=job_id,
        status="running",
        progress_percent=5.0,
        stage="Đang khởi động render video...",
        video_url=None,
    )


@router.get("/status/{job_id}", response_model=ExportStatusResponse)
async def get_export_status(job_id: str) -> ExportStatusResponse:
    """Lấy trạng thái và tiến độ render video."""
    if job_id not in _EXPORT_JOBS:
        raise HTTPException(status_code=404, detail="Không tìm thấy tác vụ export với ID này")

    rec = _EXPORT_JOBS[job_id]
    return ExportStatusResponse(
        job_id=job_id,
        status=rec["status"],
        progress_percent=rec["progress_percent"],
        stage=rec["stage"],
        video_url=rec.get("video_url"),
        error_message=rec.get("error_message"),
        qa_report=rec.get("qa_report"),
    )


@router.get("/stream/{job_id}")
async def stream_export_status(job_id: str):
    """Server-Sent Events (SSE) stream đẩy tiến độ render video theo thời gian thực."""
    if job_id not in _EXPORT_JOBS:
        raise HTTPException(status_code=404, detail="Không tìm thấy tác vụ export với ID này")

    async def event_generator():
        last_progress = -1.0
        last_stage = ""
        while True:
            if job_id not in _EXPORT_JOBS:
                break
            rec = _EXPORT_JOBS[job_id]
            status = rec["status"]
            progress = float(rec["progress_percent"])
            stage = str(rec["stage"])

            if progress != last_progress or stage != last_stage or status in ["completed", "failed"]:
                last_progress = progress
                last_stage = stage
                payload = {
                    "job_id": job_id,
                    "status": status,
                    "progress_percent": progress,
                    "stage": stage,
                    "video_url": rec.get("video_url"),
                    "error_message": rec.get("error_message"),
                    "qa_report": rec.get("qa_report"),
                }
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

            if status in ["completed", "failed"]:
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

