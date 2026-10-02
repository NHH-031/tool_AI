from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class MediaCompositor(ABC):
    """Ghép kênh (muxing) hình ảnh video với lời đọc (narration) và nhạc nền (BGM)."""

    @abstractmethod
    def mux_audio_video(
        self,
        video_path: Path,
        audio_path: Path,
        output_path: Path,
        bgm_path: Optional[Path] = None,
        bgm_volume: float = 0.15,
    ) -> Path:
        """Ghép audio vào video MP4, tự động cân bằng âm lượng BGM dưới voiceover."""
        pass
