from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import av
import numpy as np
from pydantic import BaseModel, Field


class MediaReport(BaseModel):
    """Báo cáo kiểm định toàn diện chất lượng kỹ thuật và trực quan của video (Media & Visual QA)."""
    file_path: str = Field(description="Đường dẫn file video MP4")
    file_exists: bool = Field(description="Tồn tại trên đĩa")
    file_size_bytes: int = Field(default=0, description="Kích thước file (bytes)")
    is_valid_mp4: bool = Field(default=False, description="Container MP4 hợp lệ theo chuẩn ISO base media")
    duration_sec: float = Field(default=0.0, description="Tổng thời lượng video (giây)")
    video_streams_count: int = Field(default=0, description="Số lượng luồng video")
    audio_streams_count: int = Field(default=0, description="Số lượng luồng âm thanh")
    video_codec: Optional[str] = Field(default=None, description="Codec video (h264, etc.)")
    video_width: Optional[int] = Field(default=None, description="Độ phân giải ngang (pixels)")
    video_height: Optional[int] = Field(default=None, description="Độ phân giải dọc (pixels)")
    fps: Optional[float] = Field(default=None, description="Tốc độ khung hình (fps)")
    frame_count: int = Field(default=0, description="Tổng số khung hình video đã giải mã")
    audio_codec: Optional[str] = Field(default=None, description="Codec audio (aac, mp3, etc.)")
    audio_channels: Optional[int] = Field(default=None, description="Số kênh âm thanh (1=mono, 2=stereo)")
    audio_sample_rate: Optional[int] = Field(default=None, description="Tần số lấy mẫu âm thanh (Hz)")
    audio_duration_sec: Optional[float] = Field(default=None, description="Thời lượng luồng âm thanh (giây)")
    duration_delta: Optional[float] = Field(default=None, description="Độ chênh lệch giữa video và audio (giây)")
    is_duration_compatible: bool = Field(default=True, description="Video và audio có thời lượng tương thích")
    is_corrupted: bool = Field(default=False, description="Có lỗi hỏng file hoặc lỗi giải mã frame")
    first_frame_mean_luminance: Optional[float] = Field(default=None, description="Độ sáng trung bình frame đầu")
    final_frame_mean_luminance: Optional[float] = Field(default=None, description="Độ sáng trung bình frame cuối")
    visual_qa_pass: bool = Field(default=True, description="Đạt toàn bộ tiêu chuẩn trực quan Whiteboard")
    details: Dict[str, Any] = Field(default_factory=dict, description="Thông số chi tiết bổ sung")


class MediaProbe:
    """
    Công cụ Media QA dựa trên chuẩn libavformat/libavcodec (tương đương ffprobe đầy đủ).
    Kiểm tra tính toàn vẹn của container, các luồng stream, độ tương thích audio-video và trực quan.
    """

    @classmethod
    def inspect_media(cls, file_path: Path | str, audio_tolerance_sec: float = 1.5) -> MediaReport:
        p = Path(file_path).resolve()
        if not p.exists():
            return MediaReport(
                file_path=str(p),
                file_exists=False,
                is_valid_mp4=False,
            )

        file_size = p.stat().st_size
        if file_size == 0:
            return MediaReport(
                file_path=str(p),
                file_exists=True,
                file_size_bytes=0,
                is_valid_mp4=False,
                is_corrupted=True,
            )

        try:
            container = av.open(str(p))
        except Exception as e:
            return MediaReport(
                file_path=str(p),
                file_exists=True,
                file_size_bytes=file_size,
                is_valid_mp4=False,
                is_corrupted=True,
                details={"open_error": str(e)},
            )

        fmt_name = container.format.name or ""
        is_mp4 = any(k in fmt_name for k in ["mp4", "mov", "m4a", "3gp"])
        dur = float(container.duration) / av.time_base if container.duration else 0.0

        v_streams = container.streams.video
        a_streams = container.streams.audio

        v_count = len(v_streams)
        a_count = len(a_streams)

        v_codec = None
        v_width = None
        v_height = None
        v_fps = None
        if v_count > 0:
            vs = v_streams[0]
            v_codec = vs.codec_context.name
            v_width = vs.width
            v_height = vs.height
            if vs.average_rate:
                v_fps = float(vs.average_rate)

        a_codec = None
        a_channels = None
        a_rate = None
        a_dur = None
        if a_count > 0:
            as_ = a_streams[0]
            a_codec = as_.codec_context.name
            if as_.layout and as_.layout.channels:
                a_channels = len(as_.layout.channels)
            elif hasattr(as_, "channels") and isinstance(as_.channels, int):
                a_channels = as_.channels
            else:
                a_channels = 1
            a_rate = as_.rate
            if as_.duration and as_.time_base:
                a_dur = float(as_.duration * as_.time_base)
            else:
                a_dur = dur

        # Kiểm tra độ tương thích thời lượng video và audio
        duration_delta = None
        is_dur_compat = True
        if a_count > 0 and a_dur is not None:
            duration_delta = round(abs(dur - a_dur), 3)
            # Audio phải khớp với video trong ngưỡng tolerance
            is_dur_compat = duration_delta <= audio_tolerance_sec

        # Giải mã toàn bộ frames để phát hiện lỗi corruption
        frame_count = 0
        is_corrupted = False
        first_frame_mean = None
        final_frame_mean = None
        last_frame_bgr = None

        try:
            for frame in container.decode(video=0):
                frame_count += 1
                bgr = frame.to_ndarray(format="bgr24")
                if frame_count == 1:
                    first_frame_mean = float(np.mean(bgr))
                last_frame_bgr = bgr

            if last_frame_bgr is not None:
                final_frame_mean = float(np.mean(last_frame_bgr))

        except Exception as e:
            is_corrupted = True
            container.close()
            return MediaReport(
                file_path=str(p),
                file_exists=True,
                file_size_bytes=file_size,
                is_valid_mp4=is_mp4,
                duration_sec=dur,
                video_streams_count=v_count,
                audio_streams_count=a_count,
                video_codec=v_codec,
                video_width=v_width,
                video_height=v_height,
                fps=v_fps,
                frame_count=frame_count,
                audio_codec=a_codec,
                audio_channels=a_channels,
                audio_sample_rate=a_rate,
                audio_duration_sec=a_dur,
                duration_delta=duration_delta,
                is_duration_compatible=is_dur_compat,
                is_corrupted=True,
                details={"decode_error": str(e)},
            )

        container.close()

        # Tiêu chuẩn trực quan Whiteboard Animation:
        # 1. Khung hình đầu: Bảng trắng sáng (> 180), không bị màn hình đen
        # 2. Khung hình cuối: Chứa nét vẽ mực đen (mean < 254), không bị trắng trơn
        # 3. Không có lỗi giải mã, không bị crash hoặc vỡ hình
        visual_pass = not is_corrupted and is_mp4 and v_count >= 1
        if first_frame_mean is not None and first_frame_mean < 180.0:
            visual_pass = False
        if final_frame_mean is not None and final_frame_mean > 254.0:
            visual_pass = False

        return MediaReport(
            file_path=str(p),
            file_exists=True,
            file_size_bytes=file_size,
            is_valid_mp4=is_mp4,
            duration_sec=round(dur, 3),
            video_streams_count=v_count,
            audio_streams_count=a_count,
            video_codec=v_codec,
            video_width=v_width,
            video_height=v_height,
            fps=v_fps,
            frame_count=frame_count,
            audio_codec=a_codec,
            audio_channels=a_channels,
            audio_sample_rate=a_rate,
            audio_duration_sec=round(a_dur, 3) if a_dur is not None else None,
            duration_delta=duration_delta,
            is_duration_compatible=is_dur_compat,
            is_corrupted=is_corrupted,
            first_frame_mean_luminance=round(first_frame_mean, 2) if first_frame_mean is not None else None,
            final_frame_mean_luminance=round(final_frame_mean, 2) if final_frame_mean is not None else None,
            visual_qa_pass=visual_pass,
            details={
                "container_format": fmt_name,
            },
        )
