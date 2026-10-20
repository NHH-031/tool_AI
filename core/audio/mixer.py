"""
Audio Mixer and Auto-Ducking Engine.
Handles decoding, looping, sidechain auto-ducking, master limiting, and multi-track composition.
"""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Optional, Tuple
import numpy as np
import av

logger = logging.getLogger(__name__)

DEFAULT_SAMPLE_RATE = 44100


class AudioMixer:
    """Bộ xử lý trộn âm thanh chuyên nghiệp chuẩn phát thanh cho video Whiteboard."""

    def __init__(self, sample_rate: int = DEFAULT_SAMPLE_RATE):
        self.sample_rate = sample_rate

    def read_audio(self, path: Path) -> Tuple[np.ndarray, int]:
        """
        Đọc file audio bất kỳ (MP3, WAV, AAC, M4A, etc.) bằng PyAV.
        Tự động resample và chuẩn hóa về dạng Stereo (2, N) kiểu float32 [-1.0, 1.0].
        """
        if not path.exists():
            raise FileNotFoundError(f"File audio không tồn tại: {path}")

        container = av.open(str(path))
        if not container.streams.audio:
            container.close()
            raise ValueError(f"Không tìm thấy luồng audio trong file: {path}")

        stream = container.streams.audio[0]
        resampler = av.AudioResampler(format="fltp", layout="stereo", rate=self.sample_rate)

        frames = []
        for frame in container.decode(stream):
            for r in resampler.resample(frame):
                frames.append(r.to_ndarray())
        container.close()

        if not frames:
            return np.zeros((2, 0), dtype=np.float32), self.sample_rate

        arr = np.concatenate(frames, axis=1)
        return arr.astype(np.float32), self.sample_rate

    def write_audio(
        self,
        audio_data: np.ndarray,
        output_path: Path,
        codec: str = "aac",
        bit_rate: int = 192000,
    ) -> Path:
        """
        Lưu mảng audio (2, N) ra file MP4/AAC/MP3/WAV bằng PyAV.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fmt = output_path.suffix.lstrip(".").lower()
        if fmt == "mp3":
            codec = "libmp3lame"
            av_format = "mp3"
        elif fmt in ["wav"]:
            codec = "pcm_s16le"
            av_format = "wav"
        else:
            codec = "aac"
            av_format = "adts" if fmt == "aac" else None

        container = av.open(str(output_path), mode="w", format=av_format)
        stream = container.add_stream(codec, rate=self.sample_rate)
        stream.layout = "stereo"
        stream.format = "fltp" if codec != "pcm_s16le" else "s16"
        if codec != "pcm_s16le":
            stream.bit_rate = bit_rate

        chunk_size = 1024
        num_samples = audio_data.shape[1]

        # Chuẩn hóa nếu vượt ngưỡng biên độ
        peak = np.max(np.abs(audio_data))
        if peak > 0.98:
            audio_data = np.tanh(audio_data / peak) * 0.95

        for i in range(0, num_samples, chunk_size):
            chunk = audio_data[:, i : i + chunk_size]
            if chunk.shape[1] < chunk_size:
                pad = np.zeros((2, chunk_size - chunk.shape[1]), dtype=np.float32)
                chunk = np.hstack([chunk, pad])

            frame = av.AudioFrame.from_ndarray(chunk, format="fltp", layout="stereo")
            frame.rate = self.sample_rate
            frame.pts = i

            if codec == "pcm_s16le":
                # Convert to s16
                resampler_s16 = av.AudioResampler(format="s16", layout="stereo", rate=self.sample_rate)
                for r in resampler_s16.resample(frame):
                    for pkt in stream.encode(r):
                        container.mux(pkt)
            else:
                for pkt in stream.encode(frame):
                    container.mux(pkt)

        for pkt in stream.encode(None):
            container.mux(pkt)
        container.close()
        return output_path

    def compute_ducking_envelope(
        self,
        speech_arr: np.ndarray,
        duck_ratio: float = 0.35,
        threshold: float = 0.015,
        attack_sec: float = 0.08,
        release_sec: float = 0.35,
    ) -> np.ndarray:
        """
        Tính toán đường cong tự động hạ âm BGM (Auto-Ducking gain curve) từ giọng thuyết minh.
        Khi có giọng nói (RMS > threshold): gain hạ xuống duck_ratio.
        Khi có khoảng lặng: gain mượt mà phục hồi về 1.0.
        """
        num_samples = speech_arr.shape[1]
        if num_samples == 0:
            return np.ones(0, dtype=np.float32)

        # Trộn mono để đo năng lượng
        mono = 0.5 * (speech_arr[0] + speech_arr[1])

        # Tính rolling RMS qua cửa sổ 60ms
        win_size = int(self.sample_rate * 0.06)
        if win_size < 1:
            win_size = 1

        squared = mono * mono
        # Downsample để tính toán cực nhanh (bước nhảy ~10ms = 441 samples)
        step = int(self.sample_rate * 0.01)
        if step < 1:
            step = 1

        num_steps = int(math.ceil(num_samples / step))
        block_rms = np.zeros(num_steps, dtype=np.float32)

        # Tính mean squared trên các khối
        for s in range(num_steps):
            st = s * step
            en = min(num_samples, st + win_size)
            if en > st:
                block_rms[s] = np.sqrt(np.mean(squared[st:en]))

        # Target gain ở mỗi bước
        target_gain = np.where(block_rms > threshold, duck_ratio, 1.0).astype(np.float32)

        # Bộ lọc 1-pole làm mượt (Attack & Release)
        alpha_attack = float(np.exp(-step / (self.sample_rate * attack_sec)))
        alpha_release = float(np.exp(-step / (self.sample_rate * release_sec)))

        smooth_block_gain = np.zeros(num_steps, dtype=np.float32)
        cur_gain = 1.0
        for s in range(num_steps):
            tg = target_gain[s]
            alpha = alpha_attack if tg < cur_gain else alpha_release
            cur_gain = alpha * cur_gain + (1.0 - alpha) * tg
            smooth_block_gain[s] = cur_gain

        # Nội suy mượt trở lại toàn bộ mẫu
        step_indices = np.arange(num_steps) * step
        full_indices = np.arange(num_samples)
        full_envelope = np.interp(full_indices, step_indices, smooth_block_gain).astype(np.float32)
        return full_envelope

    def loop_and_fit_bgm(
        self,
        bgm_arr: np.ndarray,
        target_samples: int,
        start_offset_sec: float = 0.0,
        fade_in_sec: float = 0.5,
        fade_out_sec: float = 2.0,
    ) -> np.ndarray:
        """
        Cắt đoạn bắt đầu theo start_offset_sec, lặp bản nhạc BGM liền mạch nếu video dài hơn bản nhạc,
        và tự động áp dụng Fade-in / Fade-out (Task 8.3).
        """
        if bgm_arr.shape[1] == 0 or target_samples == 0:
            return np.zeros((2, target_samples), dtype=np.float32)

        # Cắt gọt đoạn nhạc bắt đầu theo start_offset_sec
        offset_samples = int(max(0.0, start_offset_sec) * self.sample_rate)
        if 0 < offset_samples < bgm_arr.shape[1]:
            active_bgm = bgm_arr[:, offset_samples:]
        else:
            active_bgm = bgm_arr

        bgm_samples = active_bgm.shape[1]
        if bgm_samples == 0:
            return np.zeros((2, target_samples), dtype=np.float32)

        if target_samples <= bgm_samples:
            result = active_bgm[:, :target_samples].copy()
        else:
            repeats = int(math.ceil(target_samples / bgm_samples))
            tiled = np.tile(active_bgm, (1, repeats))
            result = tiled[:, :target_samples].copy()

        # Áp dụng Fade-in ở đầu
        fade_in_samples = min(int(max(0.0, fade_in_sec) * self.sample_rate), target_samples // 4)
        if fade_in_samples > 0:
            fade_in = np.linspace(0.0, 1.0, fade_in_samples, dtype=np.float32)
            result[:, :fade_in_samples] *= fade_in

        # Áp dụng Fade-out ở cuối video
        fade_out_samples = min(int(max(0.0, fade_out_sec) * self.sample_rate), target_samples // 2)
        if fade_out_samples > 0:
            fade_out = np.linspace(1.0, 0.0, fade_out_samples, dtype=np.float32)
            result[:, -fade_out_samples:] *= fade_out

        return result

    def mix_multi_track(
        self,
        speech_arr: np.ndarray,
        bgm_arr: Optional[np.ndarray] = None,
        sfx_arr: Optional[np.ndarray] = None,
        bgm_volume: float = 0.15,
        sfx_volume: float = 0.20,
        enable_ducking: bool = True,
        target_samples: Optional[int] = None,
        bgm_start_offset: float = 0.0,
        bgm_fade_in_sec: float = 0.5,
        bgm_fade_out_sec: float = 2.0,
    ) -> np.ndarray:
        """
        Trộn 3 luồng: Giọng nói (Speech) + BGM (kèm Auto-Ducking, Trimmer & Fade) + SFX bút vẽ.
        Áp dụng Soft-Clipping Limiter chống rè/vỡ tiếng.
        """
        num_samples = target_samples or speech_arr.shape[1]
        if speech_arr.shape[1] < num_samples:
            pad = np.zeros((2, num_samples - speech_arr.shape[1]), dtype=np.float32)
            speech_arr = np.hstack([speech_arr, pad])
        else:
            speech_arr = speech_arr[:, :num_samples]

        master = speech_arr.copy()

        # 1. Trộn SFX bút vẽ nếu có
        if sfx_arr is not None and sfx_arr.shape[1] > 0:
            sfx_fit = sfx_arr[:, :num_samples]
            if sfx_fit.shape[1] < num_samples:
                pad = np.zeros((2, num_samples - sfx_fit.shape[1]), dtype=np.float32)
                sfx_fit = np.hstack([sfx_fit, pad])
            master += sfx_fit * float(sfx_volume)

        # 2. Trộn BGM với Auto-Ducking nếu có
        if bgm_arr is not None and bgm_arr.shape[1] > 0 and bgm_volume > 0.001:
            bgm_fit = self.loop_and_fit_bgm(
                bgm_arr,
                num_samples,
                start_offset_sec=bgm_start_offset,
                fade_in_sec=bgm_fade_in_sec,
                fade_out_sec=bgm_fade_out_sec,
            )
            if enable_ducking:
                duck_env = self.compute_ducking_envelope(speech_arr, duck_ratio=0.35)
                # Nhân envelope vào cả 2 kênh stereo
                bgm_fit = bgm_fit * duck_env * float(bgm_volume)
            else:
                bgm_fit = bgm_fit * float(bgm_volume)
            master += bgm_fit

        # 3. Studio Limiter (Tanh soft clipping để bảo vệ âm thanh tuyệt đối không clipping)
        peak = np.max(np.abs(master))
        if peak > 0.95:
            master = np.tanh(master / 0.95) * 0.95

        return master.astype(np.float32)


def mix_audio_with_bgm(
    speech_path: Path,
    bgm_path: Path,
    output_path: Path,
    bgm_volume: float = 0.15,
    ducking: bool = True,
    fade_out_sec: float = 2.0,
) -> Path:
    """
    Hàm tiện ích độc lập trộn file giọng nói với file nhạc nền BGM.
    """
    mixer = AudioMixer()
    speech_arr, sr = mixer.read_audio(speech_path)
    bgm_arr, _ = mixer.read_audio(bgm_path)

    mixed = mixer.mix_multi_track(
        speech_arr=speech_arr,
        bgm_arr=bgm_arr,
        bgm_volume=bgm_volume,
        enable_ducking=ducking,
    )
    return mixer.write_audio(mixed, output_path)
