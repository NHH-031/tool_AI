from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class AudioProcessor(ABC):
    """Xử lý hậu kỳ âm thanh (cân bằng âm lượng, đo duration, pad silence)."""

    @abstractmethod
    def get_duration_ms(self, audio_path: Path) -> int:
        """Đo thời lượng file audio chính xác theo milliseconds."""
        pass

    @abstractmethod
    def add_silence_padding(self, audio_path: Path, output_path: Path, leading_ms: int = 200, trailing_ms: int = 500) -> Path:
        """Thêm khoảng lặng đầu và cuối câu thoại để nhịp điệu tự nhiên."""
        pass
