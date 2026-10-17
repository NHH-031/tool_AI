from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from core.artwork.prompt_builder import StructuredIllustrationPrompt


class ImageGeneratorProvider(ABC):
    """Giao diện nhà cung cấp tạo hình minh họa nghệ thuật (AI Artwork Generator)."""

    @abstractmethod
    async def generate_artwork(
        self,
        prompt: StructuredIllustrationPrompt,
        output_path: Path,
        width: int = 1920,
        height: int = 1080,
    ) -> Path:
        """Sinh hình minh họa 16:9 chất lượng cao và lưu vào output_path."""
        pass
