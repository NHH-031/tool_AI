from __future__ import annotations

import json
import logging
import os
import re
from typing import List, Optional
from pydantic import BaseModel, Field

from core.artwork.gemini_director import StoryboardScene
from core.providers.base import LLMMessage
from core.providers.ollama import OllamaProvider

logger = logging.getLogger(__name__)


class OllamaDirectorOutput(BaseModel):
    scenes: List[StoryboardScene] = Field(description="Danh sách phân cảnh được phân bổ")


class OllamaDirector:
    """
    Đạo diễn kịch bản & phân cảnh sử dụng mô hình mã nguồn mở cục bộ Qwen 3.6:35B-A3B qua Ollama.
    Tuân thủ 100% quy chuẩn SKILL.md (Decision #8) và visual gate nét vẽ trên giấy kem #F5EBD7.
    """

    DEFAULT_STYLE_SUFFIX = (
        "crisp clean dark ink contour outlines on warm vintage cream paper #F5EBD7, "
        "whiteboard doodle illustration, high detail, masterpiece quality, 1080p widescreen, no text, no watermark"
    )

    @classmethod
    def is_available(cls) -> bool:
        provider = OllamaProvider()
        return provider.is_available()

    @classmethod
    def create_storyboard(
        cls,
        idea: str,
        target_scenes: Optional[int] = None,
        target_duration_sec: float = 60.0,
        has_color: bool = True,
    ) -> List[StoryboardScene]:
        """
        Sử dụng Qwen qua Ollama để phân tích ý tưởng/câu chuyện thành các phân cảnh độc lập.
        """
        provider = OllamaProvider()
        if not provider.is_available():
            logger.warning("[OllamaDirector] Ollama is not running on localhost:11434. Falling back.")
            return []

        # 1. Tính toán số phân cảnh
        effective_dur = max(10.0, float(target_duration_sec))
        if target_scenes and target_scenes > 0:
            scenes_count = target_scenes
        else:
            if effective_dur >= 100:
                scenes_count = max(5, int(effective_dur / 18))
            elif effective_dur >= 50:
                scenes_count = 4
            elif effective_dur >= 30:
                scenes_count = 3
            else:
                scenes_count = 2

        dur_per_scene = effective_dur / scenes_count
        words_per_scene = max(15, int(dur_per_scene * 2.7))

        system_prompt = (
            f"Bạn là đạo diễn kịch bản kiêm họa sĩ chuyên nghiệp cho AI Whiteboard Video Studio theo chuẩn SKILL.md.\n"
            f"Nhiệm vụ của bạn là phân tích nội dung được cung cấp thành ĐÚNG {scenes_count} phân cảnh (scenes).\n\n"
            f"Quy chuẩn phân cảnh:\n"
            f"1. 'scene_index': Thứ tự từ 1 đến {scenes_count}.\n"
            f"2. 'title': Tiêu đề ngắn gọn của cảnh (tiếng Việt).\n"
            f"3. 'narration': Lời thoại thuyết minh tiếng Việt tự nhiên, ấm áp, khoảng {words_per_scene} từ/cảnh.\n"
            f"4. 'visual_prompt': Prompt tiếng Anh chi tiết miêu tả hình vẽ, BẮT BUỘC kết thúc bằng:\n"
            f"   '{cls.DEFAULT_STYLE_SUFFIX}'\n"
            f"5. 'estimated_duration_sec': Thời lượng ước tính ({dur_per_scene:.1f} giây).\n\n"
            f"Trả về kết quả bằng định dạng JSON thuần túy có key 'scenes'."
        )

        user_prompt = f"Ý tưởng / Kịch bản gốc:\n{idea}"

        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt),
        ]

        try:
            import asyncio
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                # If running inside existing event loop
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        provider.generate_structured(messages, OllamaDirectorOutput, temperature=0.3)
                    )
                    out = future.result(timeout=60)
            else:
                out = asyncio.run(provider.generate_structured(messages, OllamaDirectorOutput, temperature=0.3))

            if out and out.scenes:
                return out.scenes
        except Exception as e:
            logger.error(f"[OllamaDirector] Structured generation failed: {e}")

        return []
