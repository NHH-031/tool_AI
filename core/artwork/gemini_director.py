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
        "Vibrant storybook comic illustration with clear clean ink outlines and beautiful harmonious colors. "
        "{scene_description}. Clear distinct contour lines, rich watercolor and cel-shaded color fills, "
        "harmonious lighting, high detail, masterpiece, 1080p"
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
        has_color: bool = True,
    ) -> List[StoryboardScene]:
        """
        Phân tích một ý tưởng hoặc câu chuyện dài thành danh sách các phân cảnh độc lập.
        Mỗi phân cảnh gồm lời thoại thuyết minh tiếng Việt và visual prompt tiếng Anh tương ứng.
        Hỗ trợ cả chế độ có đổ màu (Ghibli watercolor) và không đổ màu (Comic ink line art).
        """
        api_key = cls.get_api_key()
        if not api_key:
            logger.warning("[GeminiScriptDirector] GEMINI_API_KEY not found. Using fallback single-scene.")
            return [
                StoryboardScene(
                    scene_index=1,
                    title="Phân cảnh tổng quan",
                    narration=idea,
                    visual_prompt=cls.create_single_scene_prompt(idea, has_color=has_color),
                    estimated_duration_sec=max(5.0, round(len(idea.split()) / 2.8, 1)),
                )
            ]

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            style_guide = (
                "video vẽ hoạt họa minh họa đỉnh cao (Masterpiece Whiteboard Storybook Watercolor & Ink Animation).\n"
                "visual_prompt: prompt tiếng Anh mô tả chi tiết tác phẩm mỹ thuật với NÉT MỰC ĐEN RÕ RÀNG (crisp dark ink contours) "
                "và MÀU SẮC NƯỚC RỰC RỠ HÀI HÒA (rich vibrant watercolor color fills) trên nền giấy kem ấm cổ điển #F5EBD7.\n"
                "Cấu trúc bắt buộc: 'Masterpiece storybook watercolor and ink illustration, crisp expressive dark ink contours and rich vibrant harmonious colors on warm vintage cream paper #F5EBD7. [Mô tả chi tiết nhân vật/sinh vật, con mồi nếu có hành động săn mồi, bối cảnh tự nhiên và ánh sáng]. Clear distinct contour lines, smooth connected ink outlines, rich watercolor fills, high detail, 1080p widescreen, no text'"
            )

            system_instruction = (
                f"Bạn là đạo diễn kịch bản storyboard chuyên nghiệp cho {style_guide}\n"
                f"Nhiệm vụ: Phân tích ý tưởng hoặc câu chuyện thành chính xác {target_scenes} phân cảnh liền mạch, "
                f"tổng thời lượng khoảng {target_duration_sec} giây.\n"
                "QUAN TRỌNG VỀ TÍNH ĂN KHỚP NỘI DUNG VÀ GIẢI PHẪU CHÍNH XÁC:\n"
                "- Nếu câu chuyện có con rắn (snake): BẮT BUỘC mô tả là 'an elegant elongated slender serpentine green pit viper snake with coiled scaly body, distinct triangular head, reptilian slit eyes, flicking forked tongue; strictly serpentine reptile anatomy, strictly NO frog, toad, or amphibian limbs or wide amphibian mouth'.\n"
                "- Nếu con rắn săn mồi: mô tả con mồi là 'a small cute field mouse or small rodent hiding cautiously among the grass blades', tuyệt đối KHÔNG mô tả con mồi là ếch để tránh nhầm lẫn hình thể.\n"
                "- Nếu có hổ/thỏ hoặc các loài khác: mô tả chính xác tương tác đối kháng kịch tính.\n"
                "Mỗi phân cảnh PHẢI có một nội dung hình ảnh riêng biệt, ăn khớp 100% với lời thuyết minh của phân cảnh đó.\n"
                "Yêu cầu xuất ra định dạng JSON mảng các object với các trường:\n"
                "- scene_index: số nguyên thứ tự (1, 2, 3...)\n"
                "- title: tiêu đề súc tích của cảnh (tiếng Việt)\n"
                "- narration: lời thuyết minh tiếng Việt tự nhiên, truyền cảm, hào hùng hoặc sâu lắng (1-2 câu vừa đủ đọc trong 4-6 giây)\n"
                "- visual_prompt: prompt tiếng Anh mô tả theo cấu trúc bắt buộc ở trên.\n"
                "Chỉ trả về duy nhất chuỗi JSON hợp lệ, không bọc trong markdown hay thêm lời giải thích."
            )

            prompt_text = f"Ý tưởng / Kịch bản: {idea}"
            candidate_models = [
                "gemini-3.5-flash-lite",
                "gemini-3.6-flash",
                "gemini-3.7-flash",
                "gemini-3-flash-preview",
                "gemini-flash-lite-latest",
                "gemini-3.5-flash",
            ]
            
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
                    visual_prompt=cls.create_single_scene_prompt(idea, has_color=has_color),
                    estimated_duration_sec=max(5.0, round(len(idea.split()) / 2.8, 1)),
                )
            ]

    @classmethod
    def create_single_scene_prompt(cls, scene_text: str, has_color: bool = True) -> str:
        """
        Chuyển một câu văn/phân cảnh tiếng Việt đơn lẻ thành visual prompt tiếng Anh chuẩn mực,
        hỗ trợ cả chế độ có đổ màu (Ghibli watercolor) và không đổ màu (Comic ink line art).
        """
        api_key = cls.get_api_key()
        base_style_template = (
            "Masterpiece storybook watercolor and ink illustration, crisp expressive dark ink contours and rich vibrant harmonious colors on warm vintage cream paper #F5EBD7. "
            "{content}. Clear distinct contour lines, smooth connected outlines, rich watercolor fills, harmonious lighting, high detail, 1080p widescreen, no text"
        )
        if not api_key:
            return base_style_template.format(content=scene_text)

        try:
            from google import genai

            client = genai.Client(api_key=api_key)
            prompt = (
                "Bạn là đạo diễn hình ảnh storyboard chuyên nghiệp. "
                "Nhiệm vụ: Chuyển câu văn sau thành 1 mô tả trực quan chi tiết sinh động bằng tiếng Anh cho tác phẩm tranh vẽ minh họa: "
                "- Xác định rõ tất cả các thực thể chủ chốt và hành động tương tác. "
                "- Nếu có con rắn (snake): BẮT BUỘC mô tả là 'an elegant elongated slender serpentine green pit viper snake with coiled scaly body, distinct triangular head, reptilian slit eyes, flicking forked tongue; strictly serpentine reptile anatomy, strictly NO frog or amphibian limbs or wide mouth'. "
                "- Nếu con rắn săn mồi: mô tả con mồi là 'a small cute field mouse or small rodent hiding cautiously among the grass blades', KHÔNG dùng từ frog. "
                "- Bối cảnh môi trường chi tiết (cây cối, đất đá, cỏ lau, ánh sáng). "
                "Không có chữ trong tranh, không thêm lời dẫn giải, chỉ trả về nội dung tiếng Anh mô tả bối cảnh và hành động.\n"
                f"Câu văn: {scene_text}"
            )
            for m in ["gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-3.7-flash", "gemini-3-flash-preview", "gemini-flash-lite-latest", "gemini-3.5-flash"]:
                try:
                    resp = client.models.generate_content(model=m, contents=prompt)
                    desc_en = resp.text.strip().replace("\n", " ")
                    return base_style_template.format(content=desc_en)
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"[GeminiScriptDirector] Single scene prompt error: {e}")

        # Fallback an toàn
        return base_style_template.format(content=scene_text)
