"""
Subtitle Burner: Directly renders and burns professional subtitles onto video frames.
Supports Classic and TikTok Karaoke highlighting styles with full Vietnamese Unicode support.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import av

from .models import SubtitleSegment, SubtitleWord

logger = logging.getLogger(__name__)


class SubtitleBurner:
    """Bộ ghi đè (burn-in) phụ đề lên khung hình video MP4 bằng Pillow và PyAV."""

    FONT_CANDIDATES = [
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "arial.ttf",
    ]

    def __init__(self, font_size: int = 34, aspect_ratio: str = "16:9"):
        self.font_size = font_size
        self.aspect_ratio = aspect_ratio
        self._font: Optional[ImageFont.FreeTypeFont] = None
        self._font_bold: Optional[ImageFont.FreeTypeFont] = None
        self._init_fonts()

    def _init_fonts(self):
        for candidate in self.FONT_CANDIDATES:
            try:
                self._font = ImageFont.truetype(candidate, self.font_size)
                self._font_bold = ImageFont.truetype(candidate, int(self.font_size * 1.08))
                logger.debug(f"[SubtitleBurner] Loaded font: {candidate}")
                break
            except Exception:
                continue

        if self._font is None:
            self._font = ImageFont.load_default()
            self._font_bold = self._font

    def _render_classic_subtitle(
        self,
        img: Image.Image,
        text: str,
        width: int,
        height: int,
    ) -> None:
        """Kiểu phụ đề Classic: Chữ trắng viền đen trên khung nền tối bo góc ở 1/6 dưới màn hình."""
        draw = ImageDraw.Draw(img, "RGBA")
        bbox = draw.textbbox((0, 0), text, font=self._font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        # Vùng an toàn (safe-zone): 9:16 cần nâng cao hơn để tránh bị che bởi UI TikTok/Shorts
        margin_ratio = 0.16 if (self.aspect_ratio == "9:16" or height > width) else 0.08
        x = max(10, (width - text_w) // 2)
        y = height - text_h - int(height * margin_ratio)

        pad_x, pad_y = 20, 10
        # Nền tối bán trong suốt (Slate 950 alpha 210)
        draw.rounded_rectangle(
            [x - pad_x, y - pad_y, x + text_w + pad_x, y + text_h + pad_y],
            radius=14,
            fill=(15, 23, 42, 215),
        )

        # Chữ trắng viền nhẹ
        draw.text(
            (x, y - 2),
            text,
            font=self._font,
            fill=(255, 255, 255, 255),
            stroke_width=2,
            stroke_fill=(0, 0, 0, 255),
        )

    def _render_karaoke_subtitle(
        self,
        img: Image.Image,
        segment: SubtitleSegment,
        current_time_sec: float,
        width: int,
        height: int,
    ) -> None:
        """Kiểu phụ đề Karaoke (TikTok): Từ đang đọc sáng lên màu Vàng Kim (#FACC15), các từ khác màu trắng."""
        draw = ImageDraw.Draw(img, "RGBA")
        words = segment.words
        if not words:
            self._render_classic_subtitle(img, segment.text, width, height)
            return

        # Tính toán kích thước của từng từ kèm khoảng trắng
        word_metrics = []
        total_w = 0
        space_w = draw.textbbox((0, 0), " ", font=self._font)[2]

        for w in words:
            bbox = draw.textbbox((0, 0), w.word, font=self._font)
            w_w = bbox[2] - bbox[0]
            w_h = bbox[3] - bbox[1]
            word_metrics.append((w, w_w, w_h))
            total_w += w_w

        total_w += space_w * (len(words) - 1)
        max_h = max(m[2] for m in word_metrics)

        # Vùng an toàn (safe-zone): 9:16 cần nâng cao hơn để tránh bị che bởi UI TikTok/Shorts
        margin_ratio = 0.16 if (self.aspect_ratio == "9:16" or height > width) else 0.08
        start_x = max(10, (width - total_w) // 2)
        y = height - max_h - int(height * margin_ratio)

        pad_x, pad_y = 24, 12
        # Nền tối bán trong suốt
        draw.rounded_rectangle(
            [start_x - pad_x, y - pad_y, start_x + total_w + pad_x, y + max_h + pad_y],
            radius=16,
            fill=(15, 23, 42, 225),
        )

        cur_x = start_x
        for w_obj, w_w, w_h in word_metrics:
            is_active = (w_obj.start_sec <= current_time_sec <= w_obj.end_sec)
            if is_active:
                # Active word: Highlight màu Vàng Kim sáng chói (#FACC15)
                fill_color = (250, 204, 21, 255)
                font_to_use = self._font_bold
                stroke_color = (0, 0, 0, 255)
                stroke_w = 2
            else:
                # Inactive words: Màu trắng dịu
                fill_color = (241, 245, 249, 255)
                font_to_use = self._font
                stroke_color = (0, 0, 0, 220)
                stroke_w = 1

            draw.text(
                (cur_x, y - 2),
                w_obj.word,
                font=font_to_use,
                fill=fill_color,
                stroke_width=stroke_w,
                stroke_fill=stroke_color,
            )
            cur_x += w_w + space_w

    def burn_subtitles_to_video(
        self,
        video_path: Path,
        subtitles: List[SubtitleSegment],
        output_path: Path,
        style: str = "classic",
        crf: int = 22,
    ) -> Path:
        """
        Ghi phụ đề đè lên video và xuất file MP4 mới bằng PyAV.
        Bảo toàn toàn bộ luồng audio và đồng bộ timestamp chính xác.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if style in ["none", "off"] or not subtitles:
            import shutil
            shutil.copyfile(str(video_path), str(output_path))
            return output_path

        container_in = av.open(str(video_path))
        if not container_in.streams.video:
            container_in.close()
            raise ValueError(f"File video không có luồng hình ảnh: {video_path}")

        v_in = container_in.streams.video[0]
        has_audio = len(container_in.streams.audio) > 0
        a_in = container_in.streams.audio[0] if has_audio else None

        w, h = v_in.codec_context.width, v_in.codec_context.height
        fps = v_in.average_rate or 24
        time_base = v_in.time_base

        container_out = av.open(str(output_path), mode="w", format="mp4")
        v_out = container_out.add_stream("h264", rate=fps)
        v_out.width = w
        v_out.height = h
        v_out.pix_fmt = "yuv420p"
        v_out.time_base = time_base
        v_out.options = {"crf": str(crf), "preset": "fast"}

        a_out = None
        resampler_a = None
        if has_audio and a_in:
            sample_rate = a_in.rate or 44100
            layout = "stereo" if getattr(a_in, "channels", 2) == 2 else "mono"
            a_out = container_out.add_stream("aac", rate=sample_rate)
            a_out.layout = layout
            a_out.format = "fltp"
            resampler_a = av.AudioResampler(format="fltp", layout=layout, rate=sample_rate)

        # 1. Xử lý video frames và vẽ phụ đề
        for frame in container_in.decode(v_in):
            pts = frame.pts or 0
            t_sec = float(pts * time_base)

            # Tìm đoạn phụ đề đang phát tại thời điểm t_sec
            active_seg = None
            for seg in subtitles:
                if seg.start_sec <= t_sec <= seg.end_sec:
                    active_seg = seg
                    break

            if active_seg is not None:
                # Chuyển frame sang PIL Image RGB
                pil_img = frame.to_image()
                if style == "karaoke":
                    self._render_karaoke_subtitle(pil_img, active_seg, t_sec, w, h)
                else:
                    self._render_classic_subtitle(pil_img, active_seg.text, w, h)

                new_frame = av.VideoFrame.from_image(pil_img)
                new_frame.pts = pts
                new_frame.time_base = time_base
            else:
                new_frame = frame

            for pkt in v_out.encode(new_frame):
                container_out.mux(pkt)

        for pkt in v_out.encode(None):
            container_out.mux(pkt)

        # 2. Xử lý audio frames (nếu có)
        if has_audio and a_in and a_out and resampler_a:
            container_in.seek(0)
            for frame in container_in.decode(a_in):
                for r in resampler_a.resample(frame):
                    for pkt in a_out.encode(r):
                        container_out.mux(pkt)

            for pkt in a_out.encode(None):
                container_out.mux(pkt)

        container_in.close()
        container_out.close()
        logger.info(f"[SubtitleBurner] Đã ghi phụ đề ({style}) vào: {output_path}")
        return output_path
