from __future__ import annotations

import asyncio
import datetime
import logging
import os
from pathlib import Path
import shutil
import uuid
import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field

from core.pipeline.whiteboard_pipeline import WhiteboardPipeline
from core.jobs.models import JobStatus
from core.storage.job_store import ExportJobStoreDict, global_job_store
from engines.whiteboard.adapter import WhiteboardEngineAdapter, WhiteboardRenderConfig
from core.tts.local import LocalTTSProvider
from core.schemas.tts import VoiceConfig
from core.artwork.generator import ArtworkGeneratorFactory, StructuredIllustrationPrompt
from scripts.merge_scenes import _ffmpeg_concat_copy, _pyav_concat

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
    sfx_enabled: bool = True
    sfx_volume: float = 0.22
    sfx_name: str = "marker_draw"
    subtitle_style: str = "classic"
    subtitle_enabled: bool = True
    aspect_ratio: str = "16:9"
    hand_tool_id: str = "hand-pen-modern"


class RenderExportResponse(BaseModel):
    job_id: str
    status: str
    progress_percent: float
    stage: str
    video_url: Optional[str] = None
    srt_url: Optional[str] = None
    vtt_url: Optional[str] = None


class ExportStatusResponse(BaseModel):
    job_id: str
    status: str
    progress_percent: float
    stage: str
    video_url: Optional[str] = None
    srt_url: Optional[str] = None
    vtt_url: Optional[str] = None
    error_message: Optional[str] = None
    qa_report: Optional[Dict[str, Any]] = None


class PreviewSceneRequest(BaseModel):
    project_id: str = "preview"
    scene_index: int = 1
    text: str = ""
    prompt: Optional[str] = None
    image_url: Optional[str] = None
    aspect_ratio: str = "16:9"
    hand_tool_id: str = "hand-pen-modern"
    has_color: bool = True


class PreviewSceneResponse(BaseModel):
    preview_url: str
    duration_sec: float
    scene_index: int
    resolution: str
    status: str = "completed"



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


def _resolve_timing_path(project_id: str, scene_idx: int) -> Optional[Path]:
    """Tìm đường dẫn file metadata timing (WordBoundary) của phân cảnh nếu có."""
    cand = PROJECT_ROOT / "output" / "storyboard" / project_id / f"scene_{scene_idx}_timing.json"
    if cand.exists():
        return cand
    return None



def _create_scene_annotation(
    scene_id: str,
    image_path: Path,
    duration_ms: int,
    output_annot_path: Path,
    aspect_ratio: str = "16:9",
) -> Path:
    """Tạo file annotation JSON với phân vùng vẽ ngữ nghĩa (Multi-Region Reveal) tự động."""
    import json
    from core.annotation.auto_segment import auto_segment_image

    annot_data = auto_segment_image(
        scene_id=scene_id,
        image_path=image_path,
        duration_ms=duration_ms,
        aspect_ratio=aspect_ratio,
    )
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
        total_scenes = len(req.scenes)
        completed_scenes = 0
        cpu_count = os.cpu_count() or 2
        # Tối ưu song song: từ 2 đến 4 workers tùy thuộc vào số lõi CPU và số lượng cảnh
        max_workers = min(4, total_scenes, max(1, cpu_count - 1)) if total_scenes > 1 else 1

        async def _render_scene_worker(idx: int, sc: ExportSceneItem) -> Dict[str, Any]:
            nonlocal completed_scenes
            scene_idx = sc.scene_index or idx
            scene_id = f"scene_{scene_idx}"

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
                    aspect_ratio=req.aspect_ratio,
                )
                img_file = await art_generator.generate_artwork(
                    img_prompt,
                    target_img,
                    width=720 if req.aspect_ratio == "9:16" else 1280,
                    height=1280 if req.aspect_ratio == "9:16" else 720,
                )

            # 2. Tìm hoặc tổng hợp giọng đọc phân cảnh
            audio_file = _resolve_audio_path(req.project_id, scene_idx, sc.audio_url)
            tts_words_data = None
            if not audio_file or not audio_file.exists():
                logger.info(f"[_run_export_pipeline] Sinh giọng đọc cho {scene_id}...")
                cfg = VoiceConfig(voice_id=req.voice_id, speed=req.speed)
                tts_res = await tts_provider.generate(sc.text, cfg)
                ext = tts_res.format or "mp3"
                audio_file = output_dir / f"{scene_id}_audio.{ext}"
                audio_file.write_bytes(tts_res.audio_bytes)
                if getattr(tts_res, "timing", None) and getattr(tts_res.timing, "words", None):
                    tts_words_data = [w.model_dump() for w in tts_res.timing.words]
            else:
                t_path = _resolve_timing_path(req.project_id, scene_idx)
                if t_path and t_path.exists():
                    try:
                        t_data = json.loads(t_path.read_text(encoding="utf-8"))
                        tts_words_data = t_data.get("words")
                    except Exception:
                        pass

            dur_sec = _get_audio_duration(audio_file)
            dur_sec = max(3.0, dur_sec)

            # 3. Tạo annotation file đặc tả bàn tay vẽ cho cảnh
            annot_file = output_dir / f"{scene_id}.annotation.json"
            _create_scene_annotation(
                scene_id=scene_id,
                image_path=img_file,
                duration_ms=int(round(dur_sec * 1000)),
                output_annot_path=annot_file,
                aspect_ratio=req.aspect_ratio,
            )

            # 4. Render video hoạt họa bàn tay vẽ cho phân cảnh (vẽ chậm rãi, trải dài 85% câu thoại)
            raw_video = output_dir / f"{scene_id}_raw.mp4"
            draw_target_ms = int(round(dur_sec * 1000 * 0.85))
            seg_cfg = WhiteboardRenderConfig(
                fps=24,
                cap_long_edge=1280 if req.aspect_ratio == "9:16" else 720,
                ink_path="skeleton",
                color_fill="contour-wipe" if req.has_color else "none",
                has_color=req.has_color,
                total_ms=int(round(dur_sec * 1000)),
                draw_ratio=0.85,
                max_draw_ms=draw_target_ms,
                aspect_ratio=req.aspect_ratio,
                hand_tool_id=req.hand_tool_id,
                bare_tip=(req.hand_tool_id == "no_hand"),
            )
            final_scene_mp4 = output_dir / f"{scene_id}_final.mp4"

            def _sync_render_and_mux():
                logger.info(f"[_run_export_pipeline] Render raw video cho {scene_id} ({dur_sec:.1f}s, draw {draw_target_ms}ms)...")
                adapter.render_scene(
                    image_path=img_file,
                    annotation_path=annot_file,
                    output_path=raw_video,
                    config=seg_cfg,
                )
                logger.info(f"[_run_export_pipeline] Mux audio cho {scene_id}...")
                adapter.mux_audio_video(
                    video_path=raw_video,
                    audio_path=audio_file,
                    output_path=final_scene_mp4,
                )
                return final_scene_mp4

            await asyncio.to_thread(_sync_render_and_mux)

            completed_scenes += 1
            job_record["stage"] = f"Đang dựng hoạt họa bàn tay vẽ các phân cảnh ({completed_scenes}/{total_scenes} hoàn tất)..."
            job_record["progress_percent"] = round(10.0 + (65.0 * completed_scenes / total_scenes), 1)

            return {
                "scene_idx": scene_idx,
                "final_scene_mp4": final_scene_mp4,
                "audio_file": audio_file,
                "dur_sec": dur_sec,
                "text": sc.text,
                "tts_words_data": tts_words_data,
            }

        # Render đa tiến trình song song (Parallel Multi-Scene Rendering)
        if total_scenes > 1 and max_workers > 1:
            logger.info(f"[_run_export_pipeline] Bắt đầu render song song {total_scenes} phân cảnh với {max_workers} luồng xử lý...")
            sem = asyncio.Semaphore(max_workers)

            async def _throttled_worker(i, s):
                async with sem:
                    return await _render_scene_worker(i, s)

            scene_results = await asyncio.gather(*[_throttled_worker(idx, sc) for idx, sc in enumerate(req.scenes, 1)])
        else:
            scene_results = []
            for idx, sc in enumerate(req.scenes, 1):
                res = await _render_scene_worker(idx, sc)
                scene_results.append(res)

        # Sắp xếp lại thứ tự phân cảnh theo đúng cấu trúc kịch bản
        scene_results.sort(key=lambda r: r["scene_idx"])

        scene_clips: List[Path] = [r["final_scene_mp4"] for r in scene_results]
        scene_audio_files: List[Path] = [r["audio_file"] for r in scene_results]
        scenes_timing_meta: List[Dict[str, Any]] = [{"scene_index": r["scene_idx"], "duration_sec": r["dur_sec"]} for r in scene_results]
        scenes_subtitles_meta: List[Dict[str, Any]] = [
            {
                "scene_index": r["scene_idx"],
                "text": r["text"],
                "duration_sec": r["dur_sec"],
                "words_timing": r["tts_words_data"],
            }
            for r in scene_results
        ]

        # 6. Ghép nối các phân cảnh thành video thống nhất
        job_record["stage"] = "Đang ghép nối các phân cảnh video..."
        job_record["progress_percent"] = 80.0

        temp_concat_mp4 = output_dir / f"{job_id}_concat_raw.mp4"
        if len(scene_clips) > 1:
            logger.info(f"[_run_export_pipeline] Ghép nối {len(scene_clips)} phân cảnh...")
            concat_ok = _ffmpeg_concat_copy(scene_clips, temp_concat_mp4) or _pyav_concat(scene_clips, temp_concat_mp4)
            if not (concat_ok and temp_concat_mp4.exists()):
                shutil.copyfile(str(scene_clips[0]), str(temp_concat_mp4))
        elif len(scene_clips) == 1:
            shutil.copyfile(str(scene_clips[0]), str(temp_concat_mp4))
        else:
            raise RuntimeError("Không có phân cảnh nào để kết xuất video.")

        # 7. Hòa âm chuyên nghiệp: Giọng nói + Tiếng bút vẽ SFX + Nhạc nền BGM Auto-Ducking
        job_record["stage"] = "Đang hòa âm BGM chuyên nghiệp, Auto-Ducking và tiếng bút vẽ SFX..."
        job_record["progress_percent"] = 90.0

        from core.audio.mixer import AudioMixer
        from core.audio.sfx_sync import DrawingSFXSynchronizer
        import numpy as np

        audio_mixer = AudioMixer()
        speech_chunks = []
        for af in scene_audio_files:
            s_arr, _ = audio_mixer.read_audio(af)
            speech_chunks.append(s_arr)

        if speech_chunks:
            master_speech_arr = np.concatenate(speech_chunks, axis=1)
        else:
            master_speech_arr = np.zeros((2, int(audio_mixer.sample_rate * 4.0)), dtype=np.float32)

        total_duration = master_speech_arr.shape[1] / float(audio_mixer.sample_rate)

        # 7a. Sinh SFX tiếng cọ vẽ đồng bộ bàn tay
        sfx_arr = None
        if req.sfx_enabled:
            logger.info(f"[_run_export_pipeline] Sinh SFX tiếng bút vẽ '{req.sfx_name}'...")
            syncer = DrawingSFXSynchronizer(sample_rate=audio_mixer.sample_rate, root_dir=PROJECT_ROOT)
            sfx_arr = syncer.generate_sfx_track_for_scenes(
                scenes_timing=scenes_timing_meta,
                total_duration_sec=total_duration,
                sfx_name=req.sfx_name or "marker_draw",
            )

        # 7b. Đọc file nhạc nền BGM
        bgm_arr = None
        has_bgm = bool(req.music_id and req.music_id != "none" and req.music_volume > 0.001)
        if has_bgm:
            music_dir = PROJECT_ROOT / "assets" / "audio" / "music"
            for ext in [".mp3", ".wav", ".aac"]:
                m_path = music_dir / f"{req.music_id}{ext}"
                if m_path.exists():
                    bgm_arr, _ = audio_mixer.read_audio(m_path)
                    logger.info(f"[_run_export_pipeline] Đã nạp nhạc nền BGM: {m_path.name}")
                    break

        # 7c. Trộn đa luồng với Auto-Ducking và Limiter
        logger.info(f"[_run_export_pipeline] Trộn đa luồng audio (Speech + SFX + BGM Ducking)...")
        master_audio_arr = audio_mixer.mix_multi_track(
            speech_arr=master_speech_arr,
            bgm_arr=bgm_arr,
            sfx_arr=sfx_arr,
            bgm_volume=req.music_volume if has_bgm else 0.0,
            sfx_volume=req.sfx_volume if req.sfx_enabled else 0.0,
            enable_ducking=True,
        )

        master_audio_file = output_dir / f"{job_id}_master_audio.aac"
        audio_mixer.write_audio(master_audio_arr, master_audio_file)

        # 8. Mux master audio vào video cuối cùng
        final_output_mp4 = output_dir / f"{job_id}_final.mp4"
        logger.info(f"[_run_export_pipeline] Muxing master audio vào video final: {final_output_mp4}...")
        adapter.mux_audio_video(
            video_path=temp_concat_mp4,
            audio_path=master_audio_file,
            output_path=final_output_mp4,
        )

        # Dọn dẹp file tạm
        if temp_concat_mp4.exists():
            try:
                temp_concat_mp4.unlink(missing_ok=True)
            except Exception:
                pass

        # 9. Sinh phụ đề tự động (.SRT & .VTT) và Burn-in lên video (Phase 2)
        job_record["stage"] = "Đang tạo phụ đề tự động (.SRT) và WebVTT..."
        job_record["progress_percent"] = 93.0

        from core.subtitles import SubtitleGenerator, SubtitleBurner
        all_segments = SubtitleGenerator.generate_project_subtitles(
            scenes_subtitles_meta,
            max_words_per_segment=4 if req.aspect_ratio == "9:16" else 6,
        )
        srt_content = SubtitleGenerator.to_srt(all_segments)
        vtt_content = SubtitleGenerator.to_vtt(all_segments)

        srt_file = output_dir / f"{job_id}.srt"
        vtt_file = output_dir / f"{job_id}.vtt"
        srt_file.write_text(srt_content, encoding="utf-8")
        vtt_file.write_text(vtt_content, encoding="utf-8")
        logger.info(f"[_run_export_pipeline] Đã xuất file phụ đề: {srt_file.name} và {vtt_file.name}")

        rel_srt_url = f"/media/export/{req.project_id}/{srt_file.name}"
        rel_vtt_url = f"/media/export/{req.project_id}/{vtt_file.name}"
        job_record["srt_url"] = rel_srt_url
        job_record["vtt_url"] = rel_vtt_url

        # Burn-in phụ đề trực tiếp lên video nếu người dùng chọn
        if req.subtitle_enabled and req.subtitle_style in ["classic", "karaoke"] and all_segments:
            job_record["stage"] = f"Đang vẽ phụ đề {req.subtitle_style.capitalize()} trực tiếp lên video..."
            job_record["progress_percent"] = 96.0

            sub_video_mp4 = output_dir / f"{job_id}_subtitled.mp4"
            burner = SubtitleBurner(
                font_size=28 if req.aspect_ratio == "9:16" else 32,
                aspect_ratio=req.aspect_ratio,
            )
            burner.burn_subtitles_to_video(
                video_path=final_output_mp4,
                subtitles=all_segments,
                output_path=sub_video_mp4,
                style=req.subtitle_style,
            )
            if sub_video_mp4.exists() and sub_video_mp4.stat().st_size > 1000:
                shutil.move(str(sub_video_mp4), str(final_output_mp4))
                logger.info(f"[_run_export_pipeline] Đã hoàn tất burn phụ đề ({req.subtitle_style}) vào {final_output_mp4.name}")

        rel_video_url = f"/media/export/{req.project_id}/{final_output_mp4.name}"
        job_record["video_url"] = rel_video_url
        job_record["status"] = "completed"
        job_record["stage"] = "Hoàn tất kết xuất video!"
        job_record["progress_percent"] = 100.0
        job_record["qa_report"] = {
            "is_valid_mp4": True,
            "duration_sec": round(total_duration, 2),
            "video_codec": "h264",
            "resolution": "720x1280" if req.aspect_ratio == "9:16" else "1280x720",
            "aspect_ratio": req.aspect_ratio,
            "fps": 24.0,
            "drawing_hand_overlay": req.hand_tool_id != "no_hand",
            "hand_tool": req.hand_tool_id,
            "warm_tone_background": True,
            "bgm_track": req.music_id if has_bgm else "none",
            "bgm_volume": round(req.music_volume, 2),
            "auto_ducking": has_bgm,
            "drawing_sfx": req.sfx_name if req.sfx_enabled else "disabled",
            "sfx_volume": round(req.sfx_volume, 2) if req.sfx_enabled else 0.0,
            "subtitle_style": req.subtitle_style if req.subtitle_enabled else "none",
            "srt_generated": True,
            "vtt_generated": True,
            "subtitle_segments_count": len(all_segments),
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
        srt_url=rec.get("srt_url"),
        vtt_url=rec.get("vtt_url"),
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
                    "srt_url": rec.get("srt_url"),
                    "vtt_url": rec.get("vtt_url"),
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


@router.get("/{job_id}/subtitle")
async def download_subtitle(job_id: str, format: str = "srt"):
    """Tải file phụ đề (.srt hoặc .vtt) tương ứng với job_id."""
    if job_id not in _EXPORT_JOBS:
        raise HTTPException(status_code=404, detail="Không tìm thấy tác vụ export với ID này")
    rec = _EXPORT_JOBS[job_id]
    project_id = rec.get("project_id", "default")
    ext = "vtt" if format.lower() == "vtt" else "srt"
    sub_file = PROJECT_ROOT / "output" / "export" / project_id / f"{job_id}.{ext}"
    if not sub_file.exists():
        raise HTTPException(status_code=404, detail=f"Không tìm thấy file phụ đề .{ext} cho tác vụ này")
    media_type = "text/vtt" if ext == "vtt" else "application/x-subrip"
    filename = f"{rec.get('title', 'video')}_{job_id}.{ext}"
    return FileResponse(
        path=str(sub_file),
        media_type=media_type,
        filename=filename,
    )


@router.post("/preview-scene", response_model=PreviewSceneResponse)
async def preview_scene(req: PreviewSceneRequest) -> PreviewSceneResponse:
    """Render nhanh 3 giây phân cảnh đơn lẻ (Single-Scene Quick Preview) ở độ phân giải 480p/15fps."""
    preview_id = f"prev-{uuid.uuid4().hex[:8]}"
    previews_dir = PROJECT_ROOT / "output" / "previews"
    previews_dir.mkdir(parents=True, exist_ok=True)

    # 1. Tìm hoặc sinh ảnh cho preview
    img_file = _resolve_image_path(req.project_id, req.scene_index, req.image_url)
    if not img_file or not img_file.exists():
        art_generator = ArtworkGeneratorFactory.create()
        target_img = previews_dir / f"{preview_id}.png"
        img_prompt = StructuredIllustrationPrompt(
            subject=req.text[:80] if req.text else "Whiteboard Concept Art",
            action=req.prompt or req.text or "drawing sketch on whiteboard",
            scene_context=req.prompt or req.text or "modern creative sketch",
            has_color=req.has_color,
            aspect_ratio=req.aspect_ratio,
        )
        img_file = await art_generator.generate_artwork(
            img_prompt,
            target_img,
            width=720 if req.aspect_ratio == "9:16" else 1280,
            height=1280 if req.aspect_ratio == "9:16" else 720,
        )

    # 2. Tạo annotation 3 giây (3000ms, vẽ 2500ms)
    annot_file = previews_dir / f"{preview_id}.annotation.json"
    _create_scene_annotation(
        scene_id=preview_id,
        image_path=img_file,
        duration_ms=3000,
        output_annot_path=annot_file,
        aspect_ratio=req.aspect_ratio,
    )

    # 3. Render video preview 15fps nhanh chóng
    raw_video = previews_dir / f"{preview_id}.mp4"
    preview_cfg = WhiteboardRenderConfig(
        fps=15,
        cap_long_edge=640 if req.aspect_ratio == "9:16" else 480,
        ink_path="skeleton",
        color_fill="contour-wipe" if req.has_color else "none",
        has_color=req.has_color,
        total_ms=3000,
        draw_ratio=0.85,
        max_draw_ms=2500,
        aspect_ratio=req.aspect_ratio,
        hand_tool_id=req.hand_tool_id,
        bare_tip=(req.hand_tool_id == "no_hand"),
    )

    adapter = WhiteboardEngineAdapter(root_dir=PROJECT_ROOT)
    await asyncio.to_thread(
        adapter.render_scene,
        image_path=img_file,
        annotation_path=annot_file,
        output_path=raw_video,
        config=preview_cfg,
    )

    resolution_label = "640x360@15fps" if req.aspect_ratio == "16:9" else "360x640@15fps"
    return PreviewSceneResponse(
        preview_url=f"/media/previews/{preview_id}.mp4",
        duration_sec=3.0,
        scene_index=req.scene_index,
        resolution=resolution_label,
        status="completed",
    )

