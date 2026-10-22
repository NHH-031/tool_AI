from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class EncoderInfo:
    codec: str
    name: str
    type: str  # "gpu" or "cpu"
    vendor: str  # "nvidia", "intel", "apple", "generic"
    description: str
    ffmpeg_args: List[str] = field(default_factory=list)
    pyav_options: Dict[str, str] = field(default_factory=dict)


class GPUDetector:
    """
    Tự động phát hiện chip đồ họa và bộ giải mã/mã hóa phần cứng (Hardware Acceleration):
    - NVIDIA GPU: h264_nvenc, hevc_nvenc (CUDA/NVENC)
    - Intel QuickSync: h264_qsv
    - Apple Silicon: h264_videotoolbox (M1/M2/M3/M4)
    - Fallback: libx264 CPU đa luồng tối ưu
    """

    _cached_hardware_info: Optional[Dict[str, Any]] = None

    @classmethod
    def detect_hardware(cls, force_refresh: bool = False) -> Dict[str, Any]:
        """Phát hiện toàn bộ thông tin GPU phần cứng và các bộ mã hóa video có sẵn."""
        if cls._cached_hardware_info and not force_refresh:
            return cls._cached_hardware_info

        gpus: List[Dict[str, Any]] = []
        available_codecs: List[str] = []

        # 1. Kiểm tra PyAV codecs
        try:
            import av
            pyav_codecs = set(av.codec.codecs_available)
            for cand in ["h264_nvenc", "h264_qsv", "h264_videotoolbox", "libx264", "h264"]:
                if cand in pyav_codecs:
                    available_codecs.append(cand)
        except Exception as e:
            logger.debug(f"[GPUDetector] Lỗi kiểm tra PyAV codecs: {e}")

        # 2. Kiểm tra NVIDIA GPU via nvidia-smi
        nvidia_smi = shutil.which("nvidia-smi")
        if nvidia_smi:
            try:
                res = subprocess.run(
                    [nvidia_smi, "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                if res.returncode == 0 and res.stdout.strip():
                    for line in res.stdout.strip().splitlines():
                        parts = [p.strip() for p in line.split(",")]
                        if len(parts) >= 2:
                            gpus.append({
                                "vendor": "nvidia",
                                "name": parts[0],
                                "memory": parts[1],
                                "driver_version": parts[2] if len(parts) > 2 else "Unknown",
                            })
            except Exception as e:
                logger.debug(f"[GPUDetector] nvidia-smi failed: {e}")

        # 3. Kiểm tra Apple Silicon VideoToolbox
        system = platform.system()
        machine = platform.machine()
        is_apple_silicon = (system == "Darwin" and machine in ["arm64", "aarch64"])
        if is_apple_silicon:
            gpus.append({
                "vendor": "apple",
                "name": f"Apple Silicon {platform.processor() or 'M-Series'}",
                "memory": "Unified Memory",
                "driver_version": "macOS VideoToolbox",
            })

        # 4. Kiểm tra Intel QSV
        intel_qsv_available = "h264_qsv" in available_codecs

        # 5. Phân tích bộ mã hóa khuyến nghị tốt nhất
        best_encoder = cls._resolve_best_encoder(gpus, available_codecs, is_apple_silicon)

        info = {
            "has_gpu": len(gpus) > 0,
            "gpu_count": len(gpus),
            "gpus": gpus,
            "platform": {
                "os": system,
                "release": platform.release(),
                "machine": machine,
                "processor": platform.processor(),
                "cpu_count": os.cpu_count() or 4,
            },
            "available_codecs": available_codecs,
            "best_encoder": best_encoder.codec,
            "best_encoder_name": best_encoder.name,
            "best_encoder_vendor": best_encoder.vendor,
            "best_encoder_description": best_encoder.description,
            "ffmpeg_available": shutil.which("ffmpeg") is not None,
            "pyav_available": "av" in available_codecs or len(available_codecs) > 0,
        }

        cls._cached_hardware_info = info
        return info

    @classmethod
    def _resolve_best_encoder(
        cls,
        gpus: List[Dict[str, Any]],
        available_codecs: List[str],
        is_apple_silicon: bool,
    ) -> EncoderInfo:
        # Ưu tiên 1: NVIDIA NVENC
        has_nvidia = any(g.get("vendor") == "nvidia" for g in gpus)
        if has_nvidia and "h264_nvenc" in available_codecs:
            gpu_name = next((g["name"] for g in gpus if g.get("vendor") == "nvidia"), "NVIDIA GPU")
            return EncoderInfo(
                codec="h264_nvenc",
                name="NVIDIA NVENC Hardware Acceleration",
                type="gpu",
                vendor="nvidia",
                description=f"Tăng tốc phần cứng GPU {gpu_name} (Siêu tốc ~10-15s)",
                ffmpeg_args=["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "23", "-pix_fmt", "yuv420p"],
                pyav_options={"preset": "p4", "cq": "23"},
            )

        # Ưu tiên 2: Apple Silicon VideoToolbox
        if is_apple_silicon and ("h264_videotoolbox" in available_codecs or platform.system() == "Darwin"):
            return EncoderInfo(
                codec="h264_videotoolbox",
                name="Apple VideoToolbox Hardware Acceleration",
                type="gpu",
                vendor="apple",
                description="Tăng tốc phần cứng chip Apple Silicon M-Series",
                ffmpeg_args=["-c:v", "h264_videotoolbox", "-b:v", "5M", "-pix_fmt", "yuv420p"],
                pyav_options={"b:v": "5M"},
            )

        # Ưu tiên 3: Intel QuickSync QSV
        if "h264_qsv" in available_codecs:
            return EncoderInfo(
                codec="h264_qsv",
                name="Intel QuickSync (QSV) Hardware Acceleration",
                type="gpu",
                vendor="intel",
                description="Tăng tốc phần cứng Intel QuickSync Video",
                ffmpeg_args=["-c:v", "h264_qsv", "-global_quality", "23", "-pix_fmt", "yuv420p"],
                pyav_options={"preset": "medium"},
            )

        # Fallback: CPU libx264
        return EncoderInfo(
            codec="libx264",
            name="CPU Software Encoder (libx264)",
            type="cpu",
            vendor="cpu",
            description=f"Mã hóa tối ưu đa luồng CPU ({os.cpu_count() or 4} cores)",
            ffmpeg_args=["-c:v", "libx264", "-crf", "22", "-preset", "fast", "-pix_fmt", "yuv420p"],
            pyav_options={"crf": "26", "preset": "fast"},
        )

    @classmethod
    def get_encoder_config(cls, preference: str = "auto") -> EncoderInfo:
        """
        Lấy thông số bộ mã hóa theo tùy chọn:
        - "auto": Tự động phát hiện tốt nhất
        - "nvenc" / "h264_nvenc": Ép dùng NVIDIA NVENC
        - "qsv" / "h264_qsv": Ép dùng Intel QSV
        - "videotoolbox" / "h264_videotoolbox": Ép dùng Apple VideoToolbox
        - "cpu" / "libx264": Ép dùng CPU libx264
        """
        info = cls.detect_hardware()
        pref = (preference or "auto").strip().lower()

        if pref in ["nvenc", "h264_nvenc", "nvidia"]:
            gpu_name = info["gpus"][0]["name"] if info["gpus"] else "NVIDIA GPU"
            return EncoderInfo(
                codec="h264_nvenc",
                name="NVIDIA NVENC Hardware Acceleration",
                type="gpu",
                vendor="nvidia",
                description=f"Tăng tốc phần cứng GPU {gpu_name}",
                ffmpeg_args=["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "23", "-pix_fmt", "yuv420p"],
                pyav_options={"preset": "p4", "cq": "23"},
            )

        if pref in ["qsv", "h264_qsv", "intel"]:
            return EncoderInfo(
                codec="h264_qsv",
                name="Intel QuickSync (QSV) Hardware Acceleration",
                type="gpu",
                vendor="intel",
                description="Tăng tốc phần cứng Intel QuickSync Video",
                ffmpeg_args=["-c:v", "h264_qsv", "-global_quality", "23", "-pix_fmt", "yuv420p"],
                pyav_options={"preset": "medium"},
            )

        if pref in ["videotoolbox", "h264_videotoolbox", "apple"]:
            return EncoderInfo(
                codec="h264_videotoolbox",
                name="Apple VideoToolbox Hardware Acceleration",
                type="gpu",
                vendor="apple",
                description="Tăng tốc phần cứng chip Apple Silicon",
                ffmpeg_args=["-c:v", "h264_videotoolbox", "-b:v", "5M", "-pix_fmt", "yuv420p"],
                pyav_options={"b:v": "5M"},
            )

        if pref in ["cpu", "libx264", "software"]:
            return EncoderInfo(
                codec="libx264",
                name="CPU Software Encoder (libx264)",
                type="cpu",
                vendor="cpu",
                description="Mã hóa đa luồng CPU tiêu chuẩn",
                ffmpeg_args=["-c:v", "libx264", "-crf", "22", "-preset", "fast", "-pix_fmt", "yuv420p"],
                pyav_options={"crf": "26", "preset": "fast"},
            )

        # Mặc định: auto
        best_codec = info.get("best_encoder", "libx264")
        return cls.get_encoder_config(best_codec)
