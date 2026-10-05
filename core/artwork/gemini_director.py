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
            if has_color:
                style_guide = (
                    "video vẽ hoạt họa minh họa màu sắc sống động (Studio Ghibli Anime Watercolor Storybook Animation).\n"
                    "visual_prompt: prompt tiếng Anh mô tả chi tiết cảnh vẽ tranh anime watercolor sinh động CÓ MÀU SẮC ĐẦY ĐỦ. "
                    "Cấu trúc bắt buộc: 'Vibrant Studio Ghibli inspired anime watercolor storybook illustration, clear clean dark ink outlines and rich warm harmonious colors. [Mô tả chi tiết nhân vật/sinh vật, con mồi nếu có hành động săn mồi, bối cảnh, hành động và BẢNG MÀU PHÙ HỢP]. Clear distinct contour lines, rich watercolor and cel-shaded color fills, harmonious soft sunny lighting, high detail, masterpiece, 1080p widescreen, no text'"
                )
            else:
                style_guide = (
                    "video vẽ hoạt họa tranh truyện mực đen kinh điển đỉnh cao (Masterpiece Comic Ink Illustration / Manga / Graphic Novel Line Art giống phong cách hổ đuổi thỏ trong rừng).\n"
                    "visual_prompt: prompt tiếng Anh mô tả chi tiết tranh vẽ tay mực đen (Line Art / Ink Hatching), KHÔNG CÓ MÀU SẮC. "
                    "Cấu trúc bắt buộc: 'Masterpiece comic book ink line art illustration, fine charcoal and dip-pen drawing, crisp expressive dark ink contours, intricate cross-hatching and hatching shading textures. [Mô tả chi tiết nhân vật/sinh vật, con mồi nếu có hành động săn mồi, bối cảnh cây cối và hành động kịch tính]. Dynamic anatomy, lush detailed environment on vintage warm cream paper #F5EBD7, absolutely NO colors, NO watercolor washes, NO gray smudges, pristine black line art masterpiece, 1080p widescreen, no text'"
                )

            system_instruction = (
                f"Bạn là đạo diễn kịch bản storyboard chuyên nghiệp cho {style_guide}\n"
                f"Nhiệm vụ: Phân tích ý tưởng hoặc câu chuyện thành chính xác {target_scenes} phân cảnh liền mạch, "
                f"tổng thời lượng khoảng {target_duration_sec} giây.\n"
                "QUAN TRỌNG VỀ TÍNH ĂN KHỚP NỘI DUNG: Nếu câu chuyện có yếu tố săn mồi, rình rập, đối kháng (ví dụ: 'con rắn đang rình con mồi', 'hổ đuổi thỏ'), "
                "bắt buộc PHẢI mô tả cả 2 bên (kẻ săn mồi và con mồi như chú ếch/chuột đang ẩn nấp) cùng bối cảnh môi trường kịch tính.\n"
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
        if not api_key:
            if has_color:
                return (
                    f"Vibrant Studio Ghibli inspired anime watercolor storybook illustration, clear clean dark ink outlines and rich warm harmonious colors. "
                    f"{scene_text}. Clear distinct contour lines, rich watercolor and cel-shaded color fills, harmonious soft sunny lighting, high detail, masterpiece, 1080p widescreen, no text"
                )
            else:
                return (
                    f"Masterpiece comic book ink line art illustration, fine charcoal and dip-pen drawing, crisp expressive dark ink contours, intricate cross-hatching and hatching shading textures. "
                    f"{scene_text}. Dynamic anatomy, lush detailed environment on vintage warm cream paper #F5EBD7, absolutely NO colors, NO watercolor washes, NO gray smudges, pristine black line art masterpiece, 1080p widescreen, no text"
                )

        try:
            from google import genai

            client = genai.Client(api_key=api_key)
            prompt = (
                "Bạn là đạo diễn hình ảnh storyboard chuyên nghiệp. "
                "Nhiệm vụ: Chuyển câu văn sau thành 1 mô tả trực quan chi tiết sinh động bằng tiếng Anh: "
                "- Xác định rõ tất cả các thực thể chủ chốt và hành động tương tác (Ví dụ: 'con rắn đang rình con mồi' thì PHẢI mô tả cả con rắn ngóc đầu trườn trong bụi cỏ và con mồi như chú chuột đồng hoặc chú ếch đang núp gần đó trong tư thế kịch tính; 'hổ đuổi thỏ' thì phải mô tả cả hổ đang phóng tới và thỏ chạy trốn). "
                "- Bối cảnh môi trường chi tiết (cây cối, đất đá, cỏ lau, ánh sáng). "
                "Không có chữ trong tranh, không thêm lời dẫn giải, chỉ trả về nội dung tiếng Anh mô tả bối cảnh và hành động.\n"
                f"Câu văn: {scene_text}"
            )
            for m in ["gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-3.7-flash", "gemini-3-flash-preview", "gemini-flash-lite-latest", "gemini-3.5-flash"]:
                try:
                    resp = client.models.generate_content(model=m, contents=prompt)
                    desc_en = resp.text.strip().replace("\n", " ")
                    if has_color:
                        return (
                            f"Vibrant Studio Ghibli inspired anime watercolor storybook illustration, clear clean dark ink outlines and rich warm harmonious colors. "
                            f"{desc_en}. Clear distinct contour lines, rich watercolor and cel-shaded color fills, harmonious soft sunny lighting, high detail, masterpiece, 1080p widescreen, no text"
                        )
                    else:
                        return (
                            f"Masterpiece comic book ink line art illustration, fine charcoal and dip-pen drawing, crisp expressive dark ink contours, intricate cross-hatching and hatching shading textures. "
                            f"{desc_en}. Dynamic expressive anatomy, lush detailed environment on vintage warm cream paper #F5EBD7, absolutely NO colors, NO watercolor washes, NO gray smudges, pristine black line art masterpiece, 1080p widescreen, no text"
                        )
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"[GeminiScriptDirector] Single scene prompt error: {e}")

        # Fallback an toàn
        if has_color:
            return (
                f"Vibrant Studio Ghibli inspired anime watercolor storybook illustration, clear clean dark ink outlines and rich warm harmonious colors. "
                f"{scene_text}. Clear distinct contour lines, rich watercolor and cel-shaded color fills, harmonious soft sunny lighting, high detail, masterpiece, 1080p widescreen, no text"
            )
        else:
            return (
                f"Masterpiece comic book ink line art illustration, fine charcoal and dip-pen drawing, crisp expressive dark ink contours, intricate cross-hatching and hatching shading textures. "
                f"{scene_text}. Dynamic anatomy, lush detailed environment on vintage warm cream paper #F5EBD7, absolutely NO colors, NO watercolor washes, NO gray smudges, pristine black line art masterpiece, 1080p widescreen, no text"
            )
