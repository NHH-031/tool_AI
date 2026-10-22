from __future__ import annotations

import asyncio
import io
import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, Any

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from core.export.format_converter import FormatConverter
from core.hardware.gpu_detector import GPUDetector, EncoderInfo
from core.queue import WorkerQueue, TaskType, TaskStatus


@pytest.fixture
def client():
    return TestClient(app)


# ──────────────────────────────────────────────────────────────
# 1. Tests for Task 10.1: GPU Hardware Acceleration
# ──────────────────────────────────────────────────────────────

def test_gpu_detector_hardware_detection():
    """Kiểm tra GPUDetector phát hiện phần cứng và trả về cấu trúc hợp lệ."""
    info = GPUDetector.detect_hardware(force_refresh=True)
    assert isinstance(info, dict)
    assert "has_gpu" in info
    assert "gpus" in info
    assert "available_codecs" in info
    assert "best_encoder" in info
    assert "best_encoder_name" in info
    assert "platform" in info
    assert info["platform"]["cpu_count"] > 0


def test_gpu_detector_encoder_configs():
    """Kiểm tra GPUDetector cung cấp cấu hình encoder chuẩn xác cho các mode."""
    # 1. Mode CPU
    cpu_cfg = GPUDetector.get_encoder_config("cpu")
    assert isinstance(cpu_cfg, EncoderInfo)
    assert cpu_cfg.codec == "libx264"
    assert cpu_cfg.type == "cpu"
    assert any("-c:v" in arg for arg in cpu_cfg.ffmpeg_args)

    # 2. Mode NVENC
    nvenc_cfg = GPUDetector.get_encoder_config("nvenc")
    assert isinstance(nvenc_cfg, EncoderInfo)
    assert nvenc_cfg.codec == "h264_nvenc"
    assert nvenc_cfg.type == "gpu"
    assert nvenc_cfg.vendor == "nvidia"

    # 3. Mode QSV
    qsv_cfg = GPUDetector.get_encoder_config("qsv")
    assert isinstance(qsv_cfg, EncoderInfo)
    assert qsv_cfg.codec == "h264_qsv"
    assert qsv_cfg.vendor == "intel"

    # 4. Mode VideoToolbox
    vt_cfg = GPUDetector.get_encoder_config("videotoolbox")
    assert isinstance(vt_cfg, EncoderInfo)
    assert vt_cfg.codec == "h264_videotoolbox"
    assert vt_cfg.vendor == "apple"

    # 5. Mode Auto
    auto_cfg = GPUDetector.get_encoder_config("auto")
    assert isinstance(auto_cfg, EncoderInfo)
    assert auto_cfg.codec in ["h264_nvenc", "h264_qsv", "h264_videotoolbox", "libx264"]


def test_api_hardware_endpoints(client):
    """Kiểm tra API endpoints /system/hardware và /export/hardware-info."""
    res1 = client.get("/system/hardware")
    assert res1.status_code == 200
    data1 = res1.json()
    assert "best_encoder" in data1

    res2 = client.get("/export/hardware-info")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["best_encoder"] == data1["best_encoder"]


# ──────────────────────────────────────────────────────────────
# 2. Tests for Task 10.2: Decoupled Worker Queue System
# ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_worker_queue_lifecycle_and_tasks():
    """Kiểm tra WorkerQueue: enqueue, execute handler, update progress, mark completed."""
    queue = WorkerQueue(max_concurrent=2)
    await queue.initialize()

    executed_tasks = []

    async def sample_handler(task):
        executed_tasks.append(task.task_id)
        await queue.update_progress(task.task_id, 50.0, "Đang xử lý phân nửa...")
        return {"output_file": f"{task.task_id}.mp4"}

    queue.register_handler(TaskType.RENDER_VIDEO, sample_handler)

    task_payload = await queue.enqueue(
        task_type=TaskType.RENDER_VIDEO,
        payload={"scene_count": 3, "title": "Test Video"},
    )
    assert task_payload.status in [TaskStatus.PENDING, TaskStatus.RUNNING]

    # Đợi worker hoàn thành
    for _ in range(25):
        await asyncio.sleep(0.1)
        t = queue.get_task(task_payload.task_id)
        if t and t.status == TaskStatus.COMPLETED:
            break

    final_task = queue.get_task(task_payload.task_id)
    assert final_task is not None
    assert final_task.status == TaskStatus.COMPLETED
    assert final_task.progress == 100.0
    assert final_task.result == {"output_file": f"{task_payload.task_id}.mp4"}
    assert task_payload.task_id in executed_tasks

    await queue.shutdown()


# ──────────────────────────────────────────────────────────────
# 3. Tests for Task 10.3: Multi-Format Exporter
# ──────────────────────────────────────────────────────────────

def _create_synthetic_video(file_path: Path, width: int = 320, height: int = 180, fps: int = 15, duration_sec: float = 1.0):
    """Tạo video giả lập với nền kem #F5EBD7 và hình tròn đen di chuyển."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(file_path), fourcc, fps, (width, height))
    total_frames = int(fps * duration_sec)

    bg_color = (215, 235, 245)  # BGR for #F5EBD7

    for f in range(total_frames):
        frame = np.full((height, width, 3), bg_color, dtype=np.uint8)
        # Nét vẽ đen di chuyển
        cx = int(50 + (width - 100) * (f / total_frames))
        cy = height // 2
        cv2.circle(frame, (cx, cy), 15, (26, 26, 26), -1)
        writer.write(frame)

    writer.release()
    return file_path


def test_format_converter_gif(tmp_path):
    """Kiểm tra chuyển đổi video sang ảnh động GIF."""
    src_video = _create_synthetic_video(tmp_path / "test_src.mp4", width=320, height=180, fps=12, duration_sec=1.0)
    out_gif = tmp_path / "test.gif"

    res = FormatConverter.convert_to_gif(src_video, out_gif, fps=10, scale_width=240)
    assert res.exists()
    assert res.stat().st_size > 500
    assert res.suffix.lower() == ".gif"


def test_format_converter_transparent_webm(tmp_path):
    """Kiểm tra tách nền kem #F5EBD7 xuất video WebM trong suốt."""
    src_video = _create_synthetic_video(tmp_path / "test_webm_src.mp4", width=320, height=180, fps=12, duration_sec=1.0)
    out_webm = tmp_path / "test_transparent.webm"

    res = FormatConverter.convert_to_transparent_webm(src_video, out_webm, bg_hex="#F5EBD7")
    assert res.exists()
    assert res.stat().st_size > 500
    assert res.suffix.lower() == ".webm"


def test_format_converter_rescale(tmp_path):
    """Kiểm tra đổi độ phân giải video (720p / 480p)."""
    src_video = _create_synthetic_video(tmp_path / "test_rescale_src.mp4", width=320, height=180, fps=12, duration_sec=1.0)
    out_rescaled = tmp_path / "test_480p.mp4"

    res = FormatConverter.rescale_video(src_video, out_rescaled, preset="480p")
    assert res.exists()
    assert res.stat().st_size > 1000


def test_format_converter_watermark(tmp_path):
    """Kiểm tra đóng dấu Watermark lên video."""
    src_video = _create_synthetic_video(tmp_path / "test_wm_src.mp4", width=320, height=180, fps=12, duration_sec=1.0)
    out_wm = tmp_path / "test_watermarked.mp4"

    res = FormatConverter.apply_watermark(
        src_video,
        out_wm,
        watermark_text="WHITEBOARD AI",
        position="bottom-right",
        opacity=0.8,
    )
    assert res.exists()
    assert res.stat().st_size > 1000


# ──────────────────────────────────────────────────────────────
# 4. Tests for Task 10.4: Deep Project Management (Duplicate, Export/Import)
# ──────────────────────────────────────────────────────────────

def test_project_duplicate(client):
    """Kiểm tra API nhân bản dự án (POST /projects/{id}/duplicate)."""
    # 1. Tạo project gốc
    create_res = client.post("/projects", json={"title": "Original Project", "aspect_ratio": "16:9"})
    assert create_res.status_code == 201
    orig_id = create_res.json()["id"]

    # 2. Nhân bản
    dup_res = client.post(f"/projects/{orig_id}/duplicate")
    assert dup_res.status_code == 201
    dup_data = dup_res.json()
    assert dup_data["id"] != orig_id
    assert "Original Project (Bản sao)" in dup_data["title"]
    assert dup_data["aspect_ratio"] == "16:9"


def test_project_export_and_import_package(client):
    """Kiểm tra xuất gói .whiteboard (ZIP) và nhập lại khôi phục dự án."""
    # 1. Tạo dự án
    create_res = client.post("/projects", json={"title": "Package Test Project", "description": "Testing ZIP package"})
    proj_id = create_res.json()["id"]

    # 2. Xuất gói
    export_res = client.get(f"/projects/{proj_id}/export-package")
    assert export_res.status_code == 200
    assert "application/zip" in export_res.headers.get("content-type", "")
    pkg_bytes = export_res.content
    assert len(pkg_bytes) > 50

    # Kiểm tra cấu trúc file zip
    with zipfile.ZipFile(io.BytesIO(pkg_bytes), "r") as zf:
        namelist = zf.namelist()
        assert "project.json" in namelist
        proj_json = json.loads(zf.read("project.json").decode("utf-8"))
        assert proj_json["id"] == proj_id
        assert proj_json["title"] == "Package Test Project"

    # 3. Nhập lại gói .whiteboard
    import_res = client.post(
        "/projects/import-package",
        files={"file": ("test.whiteboard", pkg_bytes, "application/zip")},
    )
    assert import_res.status_code == 201
    imported_data = import_res.json()
    assert imported_data["id"] != proj_id
    assert "Package Test Project (Đã nhập)" in imported_data["title"]
    assert imported_data["description"] == "Testing ZIP package"
