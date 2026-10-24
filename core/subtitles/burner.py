"""
Subtitle Burner: Directly renders and burns professional subtitles onto video frames.
Supports Classic and TikTok Karaoke highlighting styles with full Vietnamese Unicode support.
"""

from __future__ import annotations

import logging
from pathlib import Path
import re
from pathlib import Path
from typing import List, Optional, Tuple, Union
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import av

from .models import SubtitleSegment, SubtitleWord, SubtitleTypographyConfig

logger = logging.getLogger(__name__)


def _parse_rgba(color_val: Union[str, Tuple[int, int, int], Tuple[int, int, int, int]], default_alpha: int = 255) -> Tuple[int, int, int, int]:
    """Chuyển đổi linh hoạt mã hex hoặc rgba string thành tuple (r, g, b, a)."""
    if isinstance(color_val, (tuple, list)):
        if len(color_val) == 3:
            return (int(color_val[0]), int(color_val[1]), int(color_val[2]), default_alpha)
        if len(color_val) >= 4:
            return (int(color_val[0]), int(color_val[1]), int(color_val[2]), int(color_val[3]))

    s = str(color_val).strip()
    if s.startswith("rgba"):
        m = re.findall(r"[\d\.]+", s)
        if len(m) >= 4:
            r, g, b = int(float(m[0])), int(float(m[1])), int(float(m[2]))
            a_val = float(m[3])
            a = int(a_val * 255) if a_val <= 1.0 else int(a_val)
            return (r, g, b, a)
    elif s.startswith("rgb"):
        m = re.findall(r"\d+", s)
        if len(m) >= 3:
            return (int(m[0]), int(m[1]), int(m[2]), default_alpha)

    # Hex parse
    clean = s.lstrip("#")
    if len(clean) == 6:
        try:
            return (int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16), default_alpha)
        except ValueError:
            pass
    elif len(clean) == 8:
        try:
            return (int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16), int(clean[6:8], 16))
        except ValueError:
            pass

    return (255, 255, 255, default_alpha)


class SubtitleBurner:
    """Bộ ghi đè (burn-in) phụ đề lên khung hình video MP4 bằng Pillow và PyAV với tùy biến typography toàn diện."""

    SYSTEM_FONT_DIRS = [
        Path(__file__).resolve().parent.parent.parent / "assets" / "fonts",
        Path("C:/Windows/Fonts"),
    ]

    def __init__(
        self,
        font_size: Optional[int] = None,
        aspect_ratio: str = "16:9",
        typography: Optional[SubtitleTypographyConfig] = None,
    ):
        self.aspect_ratio = aspect_ratio
        self.typography = typography or SubtitleTypographyConfig()
        if font_size:
            self.font_size = font_size
            self.typography.font_size = font_size
        else:
            self.font_size = self.typography.resolve_font_size(aspect_ratio)

        self._font: Optional[ImageFont.FreeTypeFont] = None
        self._font_bold: Optional[ImageFont.FreeTypeFont] = None
        self._init_fonts()

    def _resolve_font_candidates(self, family: str) -> List[str]:
        """Tạo danh sách các ứng viên font tương ứng với họ font được yêu cầu."""
        fam = (family or "").strip().lower()
        candidates: List[str] = []

        # 1. Đường dẫn trực tiếp nếu có
        for font_dir in self.SYSTEM_FONT_DIRS:
            if not font_dir.exists():
                continue
            if "patrick" in fam:
                p = font_dir / "PatrickHand-Regular.ttf"
                if p.exists():
                    candidates.append(str(p))
            elif "mali" in fam:
                p = font_dir / "Mali-Regular.ttf"
                if p.exists():
                    candidates.append(str(p))
            elif "caveat" in fam:
                p = font_dir / "Caveat-Regular.ttf"
                if p.exists():
                    candidates.append(str(p))

        # 2. Font viết tay / bảng đen Windows
        if any(k in fam for k in ["patrick", "mali", "caveat", "itim", "hand", "comic", "draw", "brush"]):
            candidates.extend([
                "C:/Windows/Fonts/comicbd.ttf",
                "C:/Windows/Fonts/comic.ttf",
                "C:/Windows/Fonts/segoepr.ttf",
                "C:/Windows/Fonts/inkfree.ttf",
            ])

        # 3. Font hiện đại Windows
        candidates.extend([
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
            "arial.ttf",
        ])
        return candidates

    def _init_fonts(self):
        candidates = self._resolve_font_candidates(self.typography.font_family)
        for candidate in candidates:
            try:
                self._font = ImageFont.truetype(candidate, self.font_size)
                self._font_bold = ImageFont.truetype(candidate, int(self.font_size * 1.08))
                logger.debug(f"[SubtitleBurner] Đã nạp font thành công: {candidate}")
                break
            except Exception:
                continue

        if self._font is None:
            self._font = ImageFont.load_default()
            self._font_bold = self._font

    def _calculate_y_pos(self, text_h: int, height: int, width: int) -> int:
        """Xác định tọa độ Y theo vị trí: top, center, bottom có tính vùng an toàn TikTok/Shorts."""
        pos = (self.typography.position or "bottom").lower()

        if self.typography.y_offset_percent is not None:
            margin_ratio = max(0.01, min(0.50, self.typography.y_offset_percent))
        else:
            margin_ratio = 0.16 if (self.aspect_ratio == "9:16" or height > width) else 0.08

        if pos == "top":
            return int(height * margin_ratio)
        elif pos == "center":
            return (height - text_h) // 2
        else:  # default "bottom"
            return height - text_h - int(height * margin_ratio)

    def _render_classic_subtitle(
        self,
        img: Image.Image,
        text: str,
        width: int,
        height: int,
    ) -> None:
        """Kiểu phụ đề Classic: Chữ có viền nét, nền đệm mờ bo góc hỗ trợ tùy biến typography."""
        draw = ImageDraw.Draw(img, "RGBA")
        bbox = draw.textbbox((0, 0), text, font=self._font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        x = max(12, (width - text_w) // 2)
        y = self._calculate_y_pos(text_h, height, width)

        pad_x, pad_y = 20, 10
        # Vẽ nền bo góc nếu được kích hoạt
        if self.typography.bg_enabled:
            bg_rgba = _parse_rgba(self.typography.bg_color, default_alpha=215)
            draw.rounded_rectangle(
                [x - pad_x, y - pad_y, x + text_w + pad_x, y + text_h + pad_y],
                radius=14,
                fill=bg_rgba,
            )

        # Chữ tùy biến màu và nét viền
        text_rgba = _parse_rgba(self.typography.text_color, default_alpha=255)
        stroke_rgba = _parse_rgba(self.typography.stroke_color, default_alpha=255)

        draw.text(
            (x, y - 2),
            text,
            font=self._font,
            fill=text_rgba,
            stroke_width=self.typography.stroke_width,
            stroke_fill=stroke_rgba if self.typography.stroke_width > 0 else None,
        )

    def _render_karaoke_subtitle(
        self,
        img: Image.Image,
        segment: SubtitleSegment,
        current_time_sec: float,
        width: int,
        height: int,
    ) -> None:
        """Kiểu phụ đề Karaoke (TikTok): Từ đang đọc sáng bừng theo màu highlight tùy chọn, các từ khác màu chuẩn."""
        draw = ImageDraw.Draw(img, "RGBA")
        words = segment.words
        if not words:
            self._render_classic_subtitle(img, segment.text, width, height)
            return

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
        max_h = max(m[2] for m in word_metrics) if word_metrics else 30

        start_x = max(12, (width - total_w) // 2)
        y = self._calculate_y_pos(max_h, height, width)

        pad_x, pad_y = 24, 12
        if self.typography.bg_enabled:
            bg_rgba = _parse_rgba(self.typography.bg_color, default_alpha=225)
            draw.rounded_rectangle(
                [start_x - pad_x, y - pad_y, start_x + total_w + pad_x, y + max_h + pad_y],
                radius=16,
                fill=bg_rgba,
            )

        cur_x = start_x
        # Màu chữ và highlight từ typography
        active_color = _parse_rgba(self.typography.highlight_color, default_alpha=255)
        inactive_color = _parse_rgba(self.typography.text_color, default_alpha=245)
        stroke_rgba = _parse_rgba(self.typography.stroke_color, default_alpha=255)
        s_width = self.typography.stroke_width

        for w_obj, w_w, w_h in word_metrics:
            is_active = (w_obj.start_sec <= current_time_sec <= w_obj.end_sec)
            if is_active:
                fill_color = active_color
                font_to_use = self._font_bold
                stroke_w = max(2, s_width)
            else:
                fill_color = inactive_color
                font_to_use = self._font
                stroke_w = max(1, s_width - 1)

            draw.text(
                (cur_x, y - 2),
                w_obj.word,
                font=font_to_use,
                fill=fill_color,
                stroke_width=stroke_w,
                stroke_fill=stroke_rgba if stroke_w > 0 else None,
            )
            cur_x += w_w + space_w

    def burn_subtitles_to_video(
        self,
        video_path: Path,
        subtitles: List[SubtitleSegment],
        output_path: Path,
        style: str = "classic",
        crf: int = 22,
        typography: Optional[SubtitleTypographyConfig] = None,
    ) -> Path:
        """
        Ghi phụ đề đè lên video và xuất file MP4 mới bằng PyAV.
        Bảo toàn toàn bộ luồng audio và đồng bộ timestamp chính xác.
        Hỗ trợ tùy biến typography, màu sắc và vị trí hiển thị linh hoạt.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if typography is not None:
            self.typography = typography
            self.font_size = typography.resolve_font_size(self.aspect_ratio)
            self._init_fonts()

        if style in ["none", "off"] or not subtitles:
            import shutil
            shutil.copyfile(str(video_path), str(output_path))
            return output_path

        # Chuẩn hóa danh sách subtitle: hỗ trợ cả dict lẫn SubtitleSegment
        from core.subtitles.models import SubtitleSegment
        parsed_subtitles = []
        for s in subtitles:
            if isinstance(s, dict):
                try:
                    parsed_subtitles.append(SubtitleSegment(**s))
                except Exception:
                    pass
            else:
                parsed_subtitles.append(s)
        subtitles = parsed_subtitles

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
