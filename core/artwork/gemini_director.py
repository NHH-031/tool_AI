from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class StoryboardScene(BaseModel):
    """Một phân cảnh trong kịch bản phân đoạn đa cảnh."""
    scene_index: int = Field(description="Số thứ tự phân cảnh (1, 2, 3...)")
    title: str = Field(description="Tiêu đề phân cảnh")
    narration: str = Field(description="Lời thuyết minh tiếng Việt truyền cảm")
    visual_prompt: str = Field(description="Prompt tiếng Anh chuẩn Notion doodle")
    estimated_duration_sec: float = Field(default=12.0, description="Thời lượng ước tính (giây)")


class GeminiScriptDirector:
    """
    Đạo diễn kịch bản & phân cảnh thông minh sử dụng Google Gemini.
    Tự động đọc hiểu mọi ý tưởng/câu chuyện tiếng Việt phức tạp,
    chia thành các phân cảnh liền mạch và tạo prompt hình ảnh chuẩn Notion Whiteboard Doodle.
    """

    DEFAULT_STYLE_SUFFIX = (
        "Minimalist comic doodle line art in the Notion vector illustration style. "
        "{scene_description}. Bold clean black ink outline, solid line-art, pure white background, "
        "high contrast, zero colors, zero gradients, no shading, storybook coloring page style, masterpiece, 1080p"
    )

    @classmethod
    def get_api_key(cls) -> Optional[str]:
        key = os.getenv("GEMINI_API_KEY", "").strip()
        if not key:
            try:
                from dotenv import load_dotenv
                load_dotenv()
                key = os.getenv("GEMINI_API_KEY", "").strip()
            except Exception:
                pass
        return key or None

    @classmethod
    def is_available(cls) -> bool:
        return bool(cls.get_api_key())

    @classmethod
    def create_storyboard(
        cls,
        idea: str,
        target_scenes: int = 3,
        target_duration_sec: float = 60.0,
    ) -> List[StoryboardScene]:
        """
        Phân tích một ý tưởng hoặc câu chuyện dài thành danh sách các phân cảnh độc lập.
        Mỗi phân cảnh gồm lời thoại thuyết minh tiếng Việt và visual prompt tiếng Anh tương ứng.
        """
        api_key = cls.get_api_key()
        if not api_key:
            logger.warning("[GeminiScriptDirector] GEMINI_API_KEY not found. Using fallback single-scene.")
            return [
                StoryboardScene(
                    scene_index=1,
                    title="Phân cảnh tổng quan",
                    narration=idea,
                    visual_prompt=cls.create_single_scene_prompt(idea),
                    estimated_duration_sec=max(5.0, round(len(idea.split()) / 2.8, 1)),
                )
            ]

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            system_instruction = (
                "Bạn là đạo diễn kịch bản storyboard chuyên nghiệp cho video vẽ bảng trắng (Whiteboard Animation).\n"
                f"Nhiệm vụ: Phân tích ý tưởng hoặc câu chuyện thành chính xác {target_scenes} phân cảnh liền mạch, "
                f"tổng thời lượng khoảng {target_duration_sec} giây.\n"
                "Mỗi phân cảnh PHẢI có một nội dung hình ảnh riêng biệt, ăn khớp 100% với lời thuyết minh của phân cảnh đó.\n"
                "Yêu cầu xuất ra định dạng JSON mảng các object với các trường:\n"
                "- scene_index: số nguyên thứ tự (1, 2, 3...)\n"
                "- title: tiêu đề súc tích của cảnh (tiếng Việt)\n"
                "- narration: lời thuyết minh tiếng Việt truyền cảm, hào hùng hoặc sâu lắng (khoảng 2-3 câu vừa đủ đọc)\n"
                "- visual_prompt: prompt tiếng Anh mô tả chi tiết cảnh vẽ chì Notion doodle cho bộ sinh ảnh. "
                "Cấu trúc bắt buộc: 'Minimalist comic doodle line art in the Notion vector illustration style. [Mô tả chi tiết nhân vật, bối cảnh, hành động]. Bold clean black ink outline, solid line-art, pure white background, high contrast, zero colors, zero gradients, no shading, storybook coloring page style, masterpiece, 1080p'\n"
                "Chỉ trả về duy nhất chuỗi JSON hợp lệ, không bọc trong markdown hay thêm lời giải thích."
            )

            prompt_text = f"Ý tưởng / Kịch bản: {idea}"
            candidate_models = ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-3.8-flash", "gemini-flash-latest"]
            
            raw_text = None
            for model_name in candidate_models:
                try:
                    resp = client.models.generate_content(
                        model=model_name,
                        contents=f"{system_instruction}\n\n{prompt_text}",
                        config=types.GenerateContentConfig(response_mime_type="application/json"),
                    )
                    raw_text = resp.text
                    if raw_text:
                        break
                except Exception as e_model:
                    logger.warning(f"[GeminiScriptDirector] Model {model_name} failed: {e_model}. Trying next...")

            if not raw_text:
                raise RuntimeError("All Gemini candidate models failed to respond.")

            data = json.loads(raw_text)
            scenes: List[StoryboardScene] = []
            for item in data:
                narr = item.get("narration", "").strip()
                est_dur = max(4.0, round(len(narr.split()) / 2.8, 1))
                scene = StoryboardScene(
                    scene_index=item.get("scene_index", len(scenes) + 1),
                    title=item.get("title", f"Cảnh {len(scenes) + 1}"),
                    narration=narr,
                    visual_prompt=item.get("visual_prompt", ""),
                    estimated_duration_sec=est_dur,
                )
                scenes.append(scene)

            logger.info(f"[GeminiScriptDirector] Generated {len(scenes)} storyboard scenes for idea: '{idea[:50]}...'")
            return scenes

        except Exception as e:
            logger.error(f"[GeminiScriptDirector] Error creating storyboard: {e}. Falling back to single scene.")
            return [
                StoryboardScene(
                    scene_index=1,
                    title="Phân cảnh tổng quan",
                    narration=idea,
                    visual_prompt=cls.create_single_scene_prompt(idea),
                    estimated_duration_sec=max(5.0, round(len(idea.split()) / 2.8, 1)),
                )
            ]

    @classmethod
    def create_single_scene_prompt(cls, scene_text: str) -> str:
        """
        Chuyển một câu văn/phân cảnh tiếng Việt đơn lẻ thành prompt Notion doodle tiếng Anh chuẩn mực.
        """
        api_key = cls.get_api_key()
        if not api_key:
            return (
                f"Minimalist comic doodle line art in the Notion vector illustration style. "
                f"{scene_text}. Bold clean black ink outline, solid line-art, pure white background, "
                f"high contrast, zero colors, zero gradients, no shading, storybook coloring page style, masterpiece, 1080p"
            )

        try:
            from google import genai

            client = genai.Client(api_key=api_key)
            prompt = (
                "Bạn là đạo diễn hình ảnh storyboard chuyên nghiệp. "
                "Nhiệm vụ: Chuyển câu văn sau thành 1 mô tả hành động trực quan ngắn gọn bằng tiếng Anh (chủ thể + hành động + bối cảnh). "
                "Không có chữ trong tranh, không thêm lời dẫn giải, chỉ trả về nội dung tiếng Anh.\n"
                f"Câu văn: {scene_text}"
            )
            for m in ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-3.8-flash", "gemini-flash-latest"]:
                try:
                    resp = client.models.generate_content(model=m, contents=prompt)
                    desc_en = resp.text.strip().replace("\n", " ")
                    return (
                        f"Minimalist comic doodle line art in the Notion vector illustration style. "
                        f"{desc_en}. Bold clean black ink outline, solid line-art, pure white background, "
                        f"high contrast, zero colors, zero gradients, no shading, storybook coloring page style, masterpiece, 1080p"
                    )
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"[GeminiScriptDirector] Single scene prompt error: {e}")

        return (
            f"Minimalist comic doodle line art in the Notion vector illustration style. "
            f"{scene_text}. Bold clean black ink outline, solid line-art, pure white background, "
            f"high contrast, zero colors, zero gradients, no shading, storybook coloring page style, masterpiece, 1080p"
        )
