"""
Whiteboard Drawing Sound Effects (SFX) Synchronizer.
Synchronizes pen/marker scratch sounds with the drawing hand movements,
automatically pausing when the hand lifts and the canvas is held for viewer appreciation.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import av

logger = logging.getLogger(__name__)

DEFAULT_SAMPLE_RATE = 44100
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class DrawingSFXSynchronizer:
    """Đồng bộ hóa âm thanh bút vẽ theo tiến trình bàn tay vẽ trên canvas."""

    def __init__(self, sample_rate: int = DEFAULT_SAMPLE_RATE, root_dir: Optional[Path] = None):
        self.sample_rate = sample_rate
        self.root_dir = root_dir or PROJECT_ROOT
        self.sfx_dir = self.root_dir / "assets" / "audio" / "sfx"

    def load_sfx_sample(self, sfx_name: str = "marker_draw") -> np.ndarray:
        """Đọc file mẫu SFX bút vẽ từ assets/audio/sfx/."""
        if not self.sfx_dir.exists():
            self.sfx_dir.mkdir(parents=True, exist_ok=True)

        matched_file = None
        for ext in [".mp3", ".wav", ".aac"]:
            candidate = self.sfx_dir / f"{sfx_name}{ext}"
            if candidate.exists():
                matched_file = candidate
                break

        if not matched_file:
            # Fallback lấy file bất kỳ trong sfx
            for f in self.sfx_dir.glob("*.mp3"):
                matched_file = f
                break

        if not matched_file:
            logger.warning(f"[DrawingSFX] Không tìm thấy SFX {sfx_name}, sinh mẫu cọ mặc định.")
            # Fallback procedural generation
            dur = 5.0
            t = np.linspace(0, dur, int(self.sample_rate * dur), endpoint=False)
            noise = np.random.randn(len(t)).astype(np.float32)
            d = np.diff(noise, prepend=0)
            return np.vstack([d, d])

        container = av.open(str(matched_file))
        resampler = av.AudioResampler(format="fltp", layout="stereo", rate=self.sample_rate)
        frames = []
        for frame in container.decode(audio=0):
            for r in resampler.resample(frame):
                frames.append(r.to_ndarray())
        container.close()

        if not frames:
            return np.zeros((2, 0), dtype=np.float32)
        return np.concatenate(frames, axis=1).astype(np.float32)

    def generate_sfx_track_for_scenes(
        self,
        scenes_timing: List[Dict[str, Any]],
        total_duration_sec: float,
        sfx_name: str = "marker_draw",
        draw_ratio: float = 0.85,
    ) -> np.ndarray:
        """
        Sinh luồng âm thanh bút vẽ đồng bộ trải dài toàn bộ các phân cảnh.
        Mỗi cảnh: vẽ trong draw_ratio (85% thời lượng thoại), 15% cuối tắt âm khi bàn tay rời đi.
        """
        total_samples = int(math_round(total_duration_sec * self.sample_rate))
        sfx_sample = self.load_sfx_sample(sfx_name)
        sample_len = sfx_sample.shape[1]
        if sample_len == 0 or total_samples == 0:
            return np.zeros((2, total_samples), dtype=np.float32)

        track = np.zeros((2, total_samples), dtype=np.float32)

        cur_offset_sec = 0.0
        for sc in scenes_timing:
            dur_sec = float(sc.get("duration_sec", 4.0))
            draw_dur_sec = dur_sec * draw_ratio

            start_sample = int(cur_offset_sec * self.sample_rate)
            draw_samples = int(draw_dur_sec * self.sample_rate)
            end_sample = min(total_samples, start_sample + draw_samples)

            actual_len = end_sample - start_sample
            if actual_len > 0:
                # Loop sample để lấp đầy khoảng thời gian vẽ
                repeats = int(np.ceil(actual_len / sample_len))
                tiled = np.tile(sfx_sample, (1, repeats))[:, :actual_len].copy()

                # Fade-in 50ms đầu nét vẽ
                fade_in_len = min(int(0.05 * self.sample_rate), actual_len // 4)
                if fade_in_len > 0:
                    tiled[:, :fade_in_len] *= np.linspace(0.0, 1.0, fade_in_len, dtype=np.float32)

                # Fade-out 100ms khi tay vẽ dừng lại
                fade_out_len = min(int(0.10 * self.sample_rate), actual_len // 4)
                if fade_out_len > 0:
                    tiled[:, -fade_out_len:] *= np.linspace(1.0, 0.0, fade_out_len, dtype=np.float32)

                track[:, start_sample:end_sample] += tiled

            cur_offset_sec += dur_sec

        return track


def math_round(val: float) -> int:
    return int(round(val))


def generate_drawing_sfx_track(
    scenes_timing: List[Dict[str, Any]],
    total_duration_sec: float,
    output_path: Optional[Path] = None,
    sfx_name: str = "marker_draw",
    sfx_volume: float = 0.22,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> np.ndarray:
    """
    Tiện ích tạo nhanh luồng audio SFX bút vẽ cho danh sách cảnh.
    """
    syncer = DrawingSFXSynchronizer(sample_rate=sample_rate)
    track = syncer.generate_sfx_track_for_scenes(
        scenes_timing=scenes_timing,
        total_duration_sec=total_duration_sec,
        sfx_name=sfx_name,
    )
    track *= float(sfx_volume)

    if output_path is not None:
        from .mixer import AudioMixer
        mixer = AudioMixer(sample_rate=sample_rate)
        mixer.write_audio(track, output_path)

    return track
