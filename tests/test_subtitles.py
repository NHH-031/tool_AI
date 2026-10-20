"""
Unit tests for Core Subtitles Engine (Phase 2).
Tests SubtitleGenerator (SRT, VTT) and SubtitleBurner (Classic, Karaoke).
"""

from pathlib import Path
import numpy as np
import pytest
from PIL import Image
import av

from core.subtitles.models import SubtitleSegment, SubtitleWord
from core.subtitles.srt_generator import SubtitleGenerator
from core.subtitles.burner import SubtitleBurner


def test_srt_generator_timestamps():
    # 0 seconds
    assert SubtitleGenerator.format_timestamp(0.0, vtt=False) == "00:00:00,000"
    assert SubtitleGenerator.format_timestamp(0.0, vtt=True) == "00:00:00.000"

    # 65.42 seconds -> 1m 5s 420ms
    assert SubtitleGenerator.format_timestamp(65.42, vtt=False) == "00:01:05,420"
    assert SubtitleGenerator.format_timestamp(65.42, vtt=True) == "00:01:05.420"


def test_srt_generator_from_scene():
    text = "Con khỉ đang trèo lên cây để lấy một quả chuối chín vàng."
    dur = 6.0
    segments = SubtitleGenerator.create_segments_from_scene(
        text=text,
        duration_sec=dur,
        max_words_per_segment=6,
    )

    assert len(segments) >= 2
    assert segments[0].index == 1
    assert segments[0].start_sec == 0.0
    assert segments[-1].end_sec == 6.0

    srt_str = SubtitleGenerator.to_srt(segments)
    assert "00:00:00,000 -->" in srt_str
    assert "Con khỉ đang trèo" in srt_str

    vtt_str = SubtitleGenerator.to_vtt(segments)
    assert "WEBVTT" in vtt_str
    assert "00:00:00.000 -->" in vtt_str


def test_subtitle_burner_video(tmp_path: Path):
    # 1. Create a 1-second dummy video with PyAV
    raw_video = tmp_path / "test_raw.mp4"
    container = av.open(str(raw_video), mode="w", format="mp4")
    stream = container.add_stream("h264", rate=24)
    stream.width = 640
    stream.height = 360
    stream.pix_fmt = "yuv420p"

    for i in range(24):
        # Background vintage cream
        img = Image.new("RGB", (640, 360), (245, 235, 215))
        frame = av.VideoFrame.from_image(img)
        frame.pts = i
        for pkt in stream.encode(frame):
            container.mux(pkt)
    for pkt in stream.encode(None):
        container.mux(pkt)
    container.close()

    # 2. Test burning subtitle in Classic style
    segments = [
        SubtitleSegment(
            index=1,
            start_sec=0.1,
            end_sec=0.9,
            text="Xin chào các bạn",
            words=[
                SubtitleWord(word="Xin", start_sec=0.1, end_sec=0.3),
                SubtitleWord(word="chào", start_sec=0.3, end_sec=0.6),
                SubtitleWord(word="các", start_sec=0.6, end_sec=0.8),
                SubtitleWord(word="bạn", start_sec=0.8, end_sec=0.9),
            ],
        )
    ]

    burner = SubtitleBurner(font_size=24)
    out_classic = tmp_path / "test_classic.mp4"
    burner.burn_subtitles_to_video(raw_video, segments, out_classic, style="classic")

    assert out_classic.exists()
    assert out_classic.stat().st_size > 500

    # 3. Test burning subtitle in Karaoke style
    out_karaoke = tmp_path / "test_karaoke.mp4"
    burner.burn_subtitles_to_video(raw_video, segments, out_karaoke, style="karaoke")

    assert out_karaoke.exists()
    assert out_karaoke.stat().st_size > 500


def test_export_subtitle_endpoint():
    from fastapi.testclient import TestClient
    from apps.api.main import app
    from apps.api.routers.export import _EXPORT_JOBS, PROJECT_ROOT

    client = TestClient(app)

    job_id = "test-sub-job-123"
    proj_id = "test_sub_proj"
    out_dir = PROJECT_ROOT / "output" / "export" / proj_id
    out_dir.mkdir(parents=True, exist_ok=True)
    srt_file = out_dir / f"{job_id}.srt"
    vtt_file = out_dir / f"{job_id}.vtt"
    srt_file.write_text("1\n00:00:01,000 --> 00:00:03,000\nXin chào\n", encoding="utf-8")
    vtt_file.write_text("WEBVTT\n\n1\n00:00:01.000 --> 00:00:03.000\nXin chào\n", encoding="utf-8")

    _EXPORT_JOBS[job_id] = {
        "job_id": job_id,
        "project_id": proj_id,
        "title": "Video Thu Nghiem",
        "status": "completed",
    }

    try:
        # 1. Download SRT
        res_srt = client.get(f"/export/{job_id}/subtitle?format=srt")
        assert res_srt.status_code == 200
        assert "Xin chào" in res_srt.text
        assert "application/x-subrip" in res_srt.headers.get("content-type", "")

        # 2. Download VTT
        res_vtt = client.get(f"/export/{job_id}/subtitle?format=vtt")
        assert res_vtt.status_code == 200
        assert "WEBVTT" in res_vtt.text

        # 3. Nonexistent job
        res_404 = client.get("/export/non-existent-job-999/subtitle")
        assert res_404.status_code == 404
    finally:
        # Clean up test files
        srt_file.unlink(missing_ok=True)
        vtt_file.unlink(missing_ok=True)
        if job_id in _EXPORT_JOBS:
            del _EXPORT_JOBS[job_id]

