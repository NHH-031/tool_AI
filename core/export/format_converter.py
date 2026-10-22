from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


class FormatConverter:
    """
    Bộ chuyển đổi đa định dạng video Whiteboard (Phase 10 - Task 10.3):
    1. GIF hoạt họa chất lượng cao (two-pass palettegen).
    2. Video WebM nền trong suốt (Alpha Channel Chroma Key).
    3. Độ phân giải đa tầng: 480p, 720p, 1080p, 4K UHD.
    4. Watermark / Logo đóng dấu thương hiệu.
    """

    RESOLUTION_PRESETS = {
        "480p": {"16:9": (854, 480), "9:16": (480, 854), "bitrate": "1500k"},
        "720p": {"16:9": (1280, 720), "9:16": (720, 1280), "bitrate": "3000k"},
        "1080p": {"16:9": (1920, 1080), "9:16": (1080, 1920), "bitrate": "6000k"},
        "4k": {"16:9": (3840, 2160), "9:16": (2160, 3840), "bitrate": "18000k"},
    }

    @classmethod
    def convert_to_gif(
        cls,
        video_path: Path,
        output_path: Path,
        fps: int = 12,
        scale_width: int = 480,
        max_colors: int = 128,
        max_duration_sec: float = 12.0,
    ) -> Path:
        """
        Chuyển đổi video MP4 thành ảnh động GIF tối ưu dung lượng và chất lượng.
        Sử dụng two-pass palettegen (ffmpeg) hoặc Pillow quantization fallback.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        ffmpeg = shutil.which("ffmpeg")

        # 1. Thử dùng hệ thống ffmpeg với thuật toán two-pass palettegen
        if ffmpeg is not None:
            cmd = [
                ffmpeg, "-y", "-loglevel", "error",
                "-t", str(max_duration_sec),
                "-i", str(video_path),
                "-vf", f"fps={fps},scale={scale_width}:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors={max_colors}[p];[s1][p]paletteuse=dither=bayer:bayer_scale=3",
                str(output_path),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0 and output_path.exists() and output_path.stat().st_size > 500:
                logger.info(f"[FormatConverter] Đã xuất GIF thành công qua ffmpeg: {output_path}")
                return output_path
            logger.warning(f"[FormatConverter] ffmpeg GIF thất bại: {res.stderr}. Fallback sang PyAV/Pillow.")

        # 2. PyAV + Pillow fallback (đảm bảo chạy 100% trên mọi máy không có ffmpeg)
        import av
        container = av.open(str(video_path))
        stream = container.streams.video[0]
        v_fps = float(stream.average_rate or 24.0)
        step = max(1, int(round(v_fps / fps)))

        frames: list[Image.Image] = []
        frame_idx = 0
        total_time = 0.0

        for frame in container.decode(video=0):
            frame_idx += 1
            if frame_idx % step != 0:
                continue

            img = frame.to_image().convert("RGB")
            # Resize
            w, h = img.size
            new_h = int(h * (scale_width / w))
            img_resized = img.resize((scale_width, new_h), Image.Resampling.LANCZOS)
            # Quantize
            img_quantized = img_resized.quantize(colors=max_colors, method=Image.Quantize.MEDIANCUT)
            frames.append(img_quantized)

            total_time += 1.0 / fps
            if total_time >= max_duration_sec:
                break

        container.close()

        if frames:
            frames[0].save(
                str(output_path),
                save_all=True,
                append_images=frames[1:],
                optimize=True,
                duration=int(1000 / fps),
                loop=0,
            )
            logger.info(f"[FormatConverter] Đã xuất GIF thành công qua Pillow ({len(frames)} frames): {output_path}")
            return output_path

        raise RuntimeError(f"Không thể xuất file GIF từ: {video_path}")

    @classmethod
    def convert_to_transparent_webm(
        cls,
        video_path: Path,
        output_path: Path,
        bg_hex: str = "#F5EBD7",
        similarity: float = 0.16,
        blend: float = 0.08,
    ) -> Path:
        """
        Tách nền giấy kem (#F5EBD7) thành video WebM có kênh trong suốt Alpha Channel (yuva420p).
        Cho phép nhúng bàn tay vẽ lồng ghép lên bài thuyết trình hoặc video khác.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        ffmpeg = shutil.which("ffmpeg")

        clean_hex = bg_hex.lstrip("#")
        # FFmpeg colorkey syntax: 0xRRGGBB
        colorkey_hex = f"0x{clean_hex}"

        if ffmpeg is not None:
            cmd = [
                ffmpeg, "-y", "-loglevel", "error",
                "-i", str(video_path),
                "-vf", f"colorkey={colorkey_hex}:{similarity}:{blend}",
                "-c:v", "libvpx-vp9",
                "-pix_fmt", "yuva420p",
                "-b:v", "2500k",
                "-auto-alt-ref", "0",
                str(output_path),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0 and output_path.exists() and output_path.stat().st_size > 500:
                logger.info(f"[FormatConverter] Xuất WebM trong suốt thành công qua ffmpeg: {output_path}")
                return output_path
            logger.warning(f"[FormatConverter] ffmpeg transparent WebM failed: {res.stderr}")

        # PyAV + OpenCV alpha keying fallback
        import av
        in_container = av.open(str(video_path))
        in_stream = in_container.streams.video[0]
        w = in_stream.codec_context.width
        h = in_stream.codec_context.height
        fps = in_stream.average_rate or 24

        # Parse target BGR color
        r = int(clean_hex[0:2], 16)
        g = int(clean_hex[2:4], 16)
        b = int(clean_hex[4:6], 16)
        target_bgr = np.array([b, g, r], dtype=np.float32)

        out_container = av.open(str(output_path), mode="w")
        # VP8 or VP9 with yuva420p
        codec_name = "vp9" if "vp9" in av.codec.codecs_available else ("vp8" if "vp8" in av.codec.codecs_available else "qtrle")
        out_stream = out_container.add_stream(codec_name, rate=fps)
        out_stream.width = w
        out_stream.height = h
        out_stream.pix_fmt = "yuva420p"

        thresh_dist = 255.0 * similarity * 1.5

        for frame in in_container.decode(video=0):
            bgr = frame.to_ndarray(format="bgr24").astype(np.float32)
            # Distance from target bg color
            dist = np.linalg.norm(bgr - target_bgr, axis=2)
            alpha = np.clip((dist / max(1.0, thresh_dist)) * 255.0, 0, 255).astype(np.uint8)

            bgra = np.dstack([bgr.astype(np.uint8), alpha])
            out_frame = av.VideoFrame.from_ndarray(bgra, format="bgra")
            for packet in out_stream.encode(out_frame):
                out_container.mux(packet)

        # flush
        for packet in out_stream.encode(None):
            out_container.mux(packet)

        out_container.close()
        in_container.close()
        logger.info(f"[FormatConverter] Xuất WebM trong suốt thành công qua PyAV: {output_path}")
        return output_path

    @classmethod
    def rescale_video(
        cls,
        video_path: Path,
        output_path: Path,
        preset: str = "1080p",
        aspect_ratio: str = "16:9",
        hwaccel: str = "auto",
    ) -> Path:
        """
        Đổi độ phân giải video (480p, 720p, 1080p, 4K UHD) giữ nguyên toàn bộ âm thanh và tỷ lệ khung hình.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        ar = "9:16" if aspect_ratio in ["9:16", "vertical", "portrait"] else "16:9"
        preset_info = cls.RESOLUTION_PRESETS.get(preset.lower(), cls.RESOLUTION_PRESETS["1080p"])
        target_w, target_h = preset_info[ar]

        # 1. Thử dùng ffmpeg nếu có
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg is not None:
            cmd = [
                ffmpeg, "-y", "-loglevel", "error",
                "-i", str(video_path),
                "-vf", f"scale={target_w}:{target_h}:flags=lanczos",
                "-c:v", "libx264",
                "-crf", "20",
                "-preset", "medium",
                "-c:a", "copy",
                str(output_path),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0 and output_path.exists() and output_path.stat().st_size > 1000:
                logger.info(f"[FormatConverter] Rescale sang {preset} ({target_w}x{target_h}) qua ffmpeg hoàn tất: {output_path}")
                return output_path

        # 2. PyAV rescale
        import av
        in_c = av.open(str(video_path))
        in_v = in_c.streams.video[0]
        fps = in_v.average_rate or 24

        out_c = av.open(str(output_path), mode="w")
        out_v = out_c.add_stream("h264", rate=fps)
        out_v.width = target_w
        out_v.height = target_h
        out_v.pix_fmt = "yuv420p"
        out_v.options = {"crf": "22", "preset": "medium"}

        has_audio = len(in_c.streams.audio) > 0
        out_a = None
        if has_audio:
            in_a = in_c.streams.audio[0]
            out_a = out_c.add_stream_from_template(in_a)

        for packet in in_c.demux():
            if packet.stream.type == "video":
                for frame in packet.decode():
                    bgr = frame.to_ndarray(format="bgr24")
                    resized = cv2.resize(bgr, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
                    new_frame = av.VideoFrame.from_ndarray(resized, format="bgr24")
                    for p in out_v.encode(new_frame):
                        out_c.mux(p)
            elif packet.stream.type == "audio" and out_a is not None:
                packet.stream = out_a
                out_c.mux(packet)

        # flush
        for p in out_v.encode(None):
            out_c.mux(p)

        out_c.close()
        in_c.close()
        logger.info(f"[FormatConverter] Rescale sang {preset} ({target_w}x{target_h}) qua PyAV hoàn tất: {output_path}")
        return output_path

    @classmethod
    def apply_watermark(
        cls,
        video_path: Path,
        output_path: Path,
        watermark_text: str = "",
        watermark_image_path: Optional[Path] = None,
        position: str = "bottom-right",
        opacity: float = 0.75,
    ) -> Path:
        """
        Đóng dấu Watermark thương hiệu hoặc logo cá nhân ở góc video kèm độ mờ trong suốt.
        Vị trí: 'bottom-right', 'bottom-left', 'top-right', 'top-left'.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        import av

        in_c = av.open(str(video_path))
        in_v = in_c.streams.video[0]
        w = in_v.codec_context.width
        h = in_v.codec_context.height
        fps = in_v.average_rate or 24

        out_c = av.open(str(output_path), mode="w")
        out_v = out_c.add_stream("h264", rate=fps)
        out_v.width = w
        out_v.height = h
        out_v.pix_fmt = "yuv420p"
        out_v.options = {"crf": "22", "preset": "fast"}

        has_audio = len(in_c.streams.audio) > 0
        out_a = None
        if has_audio:
            in_a = in_c.streams.audio[0]
            out_a = out_c.add_stream_from_template(in_a)

        # Chuẩn bị overlay watermark
        wm_rgba = None
        if watermark_image_path and watermark_image_path.exists():
            try:
                pil_wm = Image.open(str(watermark_image_path)).convert("RGBA")
                wm_w = int(w * 0.16)
                wm_h = int(pil_wm.height * (wm_w / pil_wm.width))
                pil_wm = pil_wm.resize((wm_w, wm_h), Image.Resampling.LANCZOS)
                # Apply opacity
                alpha = pil_wm.split()[3]
                alpha = alpha.point(lambda p: int(p * opacity))
                pil_wm.putalpha(alpha)
                wm_rgba = np.array(pil_wm)
            except Exception as e:
                logger.warning(f"Lỗi tải watermark image: {e}")

        if wm_rgba is None and watermark_text:
            # Tạo watermark text bằng PIL
            text = watermark_text.strip()
            font_size = max(18, int(h * 0.035))
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except Exception:
                font = ImageFont.load_default()

            dummy = Image.new("RGBA", (10, 10))
            draw = ImageDraw.Draw(dummy)
            bbox = draw.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0] + 24
            th = bbox[3] - bbox[1] + 16

            txt_img = Image.new("RGBA", (tw, th), (15, 23, 42, int(180 * opacity)))
            t_draw = ImageDraw.Draw(txt_img)
            t_draw.text((12, 8), text, font=font, fill=(255, 255, 255, int(240 * opacity)))
            wm_rgba = np.array(txt_img)

        # Tính toán tọa độ vị trí (x, y)
        pad = 24
        if wm_rgba is not None:
            wm_h, wm_w = wm_rgba.shape[:2]
            if position == "top-left":
                pos_x, pos_y = pad, pad
            elif position == "top-right":
                pos_x, pos_y = w - wm_w - pad, pad
            elif position == "bottom-left":
                pos_x, pos_y = pad, h - wm_h - pad
            else:  # bottom-right
                pos_x, pos_y = w - wm_w - pad, h - wm_h - pad

            wm_rgb = wm_rgba[:, :, :3]
            wm_a = (wm_rgba[:, :, 3:] / 255.0).astype(np.float32)

        for packet in in_c.demux():
            if packet.stream.type == "video":
                for frame in packet.decode():
                    bgr = frame.to_ndarray(format="bgr24")
                    if wm_rgba is not None:
                        # Blend watermark overlay
                        roi = bgr[pos_y:pos_y + wm_h, pos_x:pos_x + wm_w]
                        wm_bgr = cv2.cvtColor(wm_rgb, cv2.COLOR_RGB2BGR).astype(np.float32)
                        blended = (wm_bgr * wm_a + roi.astype(np.float32) * (1.0 - wm_a)).astype(np.uint8)
                        bgr[pos_y:pos_y + wm_h, pos_x:pos_x + wm_w] = blended

                    new_frame = av.VideoFrame.from_ndarray(bgr, format="bgr24")
                    for p in out_v.encode(new_frame):
                        out_c.mux(p)
            elif packet.stream.type == "audio" and out_a is not None:
                packet.stream = out_a
                out_c.mux(packet)

        # flush
        for p in out_v.encode(None):
            out_c.mux(p)

        out_c.close()
        in_c.close()
        logger.info(f"[FormatConverter] Đóng dấu watermark ({position}) hoàn tất: {output_path}")
        return output_path
