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
        "Masterpiece 2D Japanese manga illustration, traditional hand-drawn manga panel art, "
        "bold crisp black ink outlines with variable brush stroke thickness, "
        "clean flat cel-shaded coloring with muted earthy watercolor tones, "
        "screentone-style halftone shading, expressive manga character design, on warm vintage cream paper #F5EBD7. "
        "{scene_description}. Distinct 2D manga linework, clean flat coloring, dynamic manga composition, "
        "strictly no 3D rendering, no CGI, absolutely no 3D models or plastic sheen, widescreen 16:9, no text, no watermark"
    )

    CANDIDATE_MODELS = [
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-flash-latest",
        "gemini-3.8-flash",
        "gemini-flash-lite-latest",
    ]

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
        target_scenes: Optional[int] = None,
        target_duration_sec: float = 60.0,
        has_color: bool = True,
    ) -> List[StoryboardScene]:
        """
        Phân tích một ý tưởng hoặc câu chuyện thành danh sách các phân cảnh độc lập.
        Tự động tính toán số phân cảnh (target_scenes) và độ dài lời thoại (words_per_scene)
        dựa trên thời lượng mong muốn (ví dụ: 60s = 4 phân cảnh x 15s x ~38-42 từ).
        Mỗi phân cảnh gồm lời thoại thuyết minh tiếng Việt và visual prompt tiếng Anh tương ứng.
        """
        api_key = cls.get_api_key()
        if not api_key:
            logger.warning("[GeminiScriptDirector] GEMINI_API_KEY not found. Returning empty list.")
            return []

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)

            # 1. Tính toán số phân cảnh và số từ lời thoại chuẩn theo thời lượng
            effective_dur = max(10.0, float(target_duration_sec))
            if target_scenes is not None and target_scenes > 0:
                scenes_count = target_scenes
            else:
                if effective_dur >= 100:
                    scenes_count = max(5, int(effective_dur / 18))
                elif effective_dur >= 50:
                    scenes_count = 4  # 60 giây -> 4 cảnh x 15 giây
                elif effective_dur >= 30:
                    scenes_count = 3  # 30-45 giây -> 3 cảnh
                else:
                    scenes_count = 2  # 15-25 giây -> 2 cảnh

            dur_per_scene = effective_dur / scenes_count
            # Tốc độ đọc tiếng Việt tự nhiên là ~2.6 - 2.8 từ/giây
            words_per_scene = max(15, int(dur_per_scene * 2.7))

            style_guide = (
                "video hoạt họa vẽ tay 2D phong cách manga Nhật Bản / truyện tranh truyền thống đỉnh cao "
                "(Masterpiece 2D Japanese Manga Illustration on warm vintage cream paper #F5EBD7).\n"
                "visual_prompt: prompt tiếng Anh mô tả chi tiết tác phẩm tranh vẽ 2D MANGA với NÉT MỰC ĐEN RÕ RÀNG (bold crisp black ink outlines), "
                "ĐÁNH BÓNG SCREENTONE / HALFTONE (screentone-style halftone shading), "
                "và ĐỔ MÀU PHẲNG CEL-SHADING / MÀU NƯỚC MỘC MẠC (clean flat cel-shaded coloring with muted earthy watercolor tones) trên nền giấy kem ấm cổ điển #F5EBD7.\n"
                "TUYỆT ĐỐI KHÔNG 3D, KHÔNG CGI, KHÔNG ĐỔ BÓNG KHỐI NHỰA (strictly NO 3D render, NO CGI, NO 3D models, NO plastic sheen, NO volumetric lighting).\n"
                "Cấu trúc bắt buộc: 'Masterpiece 2D Japanese manga illustration, traditional hand-drawn manga panel art, bold crisp black ink outlines with variable brush stroke thickness, clean flat cel-shaded coloring with muted earthy watercolor tones, screentone-style halftone shading on warm vintage cream paper #F5EBD7. [Mô tả chi tiết nhân vật + TẤT CẢ đồ vật/đạo cụ tương tác + bối cảnh]. Distinct 2D manga linework, clean flat coloring, dynamic manga composition, strictly no 3D effects, 1080p widescreen, no text, no watermark'"
            )

            system_instruction = (
                f"Bạn là đạo diễn kịch bản storyboard chuyên nghiệp cho {style_guide}\n"
                f"YÊU CẦU QUAN TRỌNG: Phân tích ý tưởng hoặc câu chuyện thành CHÍNH XÁC {scenes_count} phân cảnh riêng biệt (từ scene_index 1 đến {scenes_count}).\n"
                f"Tuyệt đối KHÔNG gộp thành 1 cảnh. Phải tạo đủ {scenes_count} cảnh trong mảng JSON.\n"
                f"Tổng thời lượng video đạt khoảng {effective_dur:.0f} giây.\n"
                f"QUY ĐỊNH ĐỘ DÀI LỜI THOẠI (NARRATION):\n"
                f"- Mỗi phân cảnh kéo dài khoảng {dur_per_scene:.0f} giây.\n"
                f"- Lời thuyết minh (narration) tiếng Việt của MỖI phân cảnh BẮT BUỘC DÀI KHOẢNG {words_per_scene} từ "
                f"(dao động từ {max(10, words_per_scene - 5)} đến {words_per_scene + 5} từ) "
                f"để khi người đọc thuyết minh diễn cảm sẽ đạt đúng {dur_per_scene:.0f} giây.\n"
                f"- Tổng lời thuyết minh của toàn bộ {scenes_count} phân cảnh phải đạt khoảng {int(effective_dur * 2.7)} từ.\n\n"
                "QUAN TRỌNG VỀ TÍNH ĂN KHỚP NỘI DUNG VÀ NHÂN VẬT:\n"
                "- Mỗi phân cảnh PHẢI phản ánh chính xác 100% cốt truyện, bối cảnh không gian, nhân vật và hành động trong phân cảnh đó.\n"
                "- TUYỆT ĐỐI KHÔNG tự tiện vẽ thêm các loài động vật (như cá, tôm, chó, gà) trừ phi câu chuyện gốc trực tiếp đề cập đến chúng.\n"
                "- Với câu chuyện đời sống, sinh viên, người lao động, tiệm tạp hóa: Visual prompt PHẢI tập trung vào con người thật, biểu cảm sống động, căn phòng trọ, cửa tiệm tạp hóa, ổ bánh mì, các hành động cụ thể.\n"
                "- Nếu chủ đề về tiểu sử / cuộc đời nhân vật nghệ sĩ (như Trấn Thành, Trường Giang, hoặc người nổi tiếng):\n"
                "  + Kịch bản PHẢI tóm tắt đúng cuộc đời thật của nhân vật qua các cột mốc: "
                "Cảnh 1 (khởi đầu gian khó & đam mê nghệ thuật), Cảnh 2 (bứt phá thành danh MC/hài kịch quốc dân), "
                "Cảnh 3 (đỉnh cao đạo diễn phim trăm tỷ / tác phẩm điện ảnh để đời), Cảnh 4 (biểu tượng cống hiến & triân khán giả).\n"
                "  + Visual prompt: Phải mô tả nhân vật người nghệ sĩ Việt Nam lịch lãm, tài hoa, đang biểu diễn với micro trên sân khấu rực rỡ ánh đèn, "
                "hoặc đứng chỉ đạo sau máy quay điện ảnh chuyên nghiệp, hoặc nhận tràng pháo tay tri ấn của khán giả.\n"
                "- Nếu câu chuyện có con rắn (snake): BẮT BUỘC mô tả là 'an elegant elongated slender serpentine green pit viper snake with coiled scaly body, distinct triangular head, reptilian slit eyes, flicking forked tongue; strictly serpentine reptile anatomy, strictly NO frog, toad, or amphibian limbs or wide amphibian mouth'.\n"
                "- Nếu con rắn săn mồi: mô tả con mồi là 'a small cute field mouse or small rodent hiding cautiously among the grass blades', tuyệt đối KHÔNG mô tả con mồi là ếch để tránh nhầm lẫn hình thể.\n"
                "- Nếu có chuột hoặc mèo: mô tả đúng hành động trong bối cảnh gian phòng/kho hàng.\n"
                "QUY TẮC BẮT BUỘC VỀ ĐẠO CỤ & VẬT THỂ TƯƠNG TÁC (OBJECT FIDELITY MANDATE):\n"
                "- Đọc kỹ lời thuyết minh (narration) của từng phân cảnh.\n"
                "- Liệt kê và đưa vào visual_prompt TẤT CẢ các đồ vật, đạo cụ, vật phẩm xuất hiện hoặc tham gia vào hành động trong narration "
                "(ví dụ: cốc nước, ly trà, ổ bánh mì, cuốn sách, cây gậy, chiếc xe, bó hoa, bức thư, chìa khóa, điện thoại, bát đĩa...).\n"
                "- Visual prompt BẮT BUỘC mô tả TỪNG vật thể một cách riêng biệt và rõ ràng: tên vật thể + trạng thái vật lý (đang rơi vỡ lơ lửng, đang cầm chắc trên tay, đang đặt trên bàn...) + vị trí cụ thể trong khung hình.\n"
                "- Ví dụ ĐÚNG: 'an elderly woman in a worn dark robe, her wrinkled hands accidentally dropping a translucent glass of water which is tumbling mid-air with water droplets splashing out, in an old rustic kitchen'.\n"
                "- Ví dụ SAI: 'an elderly woman in a kitchen' (TUYỆT ĐỐI CẤM vì bỏ sót cốc nước đang rơi - chi tiết cốt lõi của hành động!).\n"
                "- BẮT BUỘC KHÔNG ĐƯỢC bỏ sót bất kỳ vật thể tương tác nào được đề cập trong lời thoại.\n"
                "Mỗi phân cảnh PHẢI có một nội dung hình ảnh riêng biệt, ăn khớp 100% với lời thuyết minh của phân cảnh đó.\n"
                "Yêu cầu xuất ra định dạng JSON mảng các object với các trường:\n"
                "- scene_index: số nguyên thứ tự (1, 2, 3...)\n"
                "- title: tiêu đề súc tích của cảnh (tiếng Việt)\n"
                f"- narration: lời thuyết minh tiếng Việt tự nhiên, truyền cảm (đủ độ dài {words_per_scene} từ để đọc trong {dur_per_scene:.0f} giây)\n"
                "- visual_prompt: prompt tiếng Anh mô tả theo cấu trúc bắt buộc ở trên.\n"
                "Chỉ trả về duy nhất chuỗi JSON hợp lệ, không bọc trong markdown hay thêm lời giải thích."
            )

            prompt_text = f"Ý tưởng / Kịch bản: {idea}"
            raw_text = None
            for model_name in cls.CANDIDATE_MODELS:
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
                est_dur = max(4.0, round(len(narr.split()) / 2.7, 1))
                scene = StoryboardScene(
                    scene_index=item.get("scene_index", len(scenes) + 1),
                    title=item.get("title", f"Cảnh {len(scenes) + 1}"),
                    narration=narr,
                    visual_prompt=item.get("visual_prompt", ""),
                    estimated_duration_sec=est_dur,
                )
                scenes.append(scene)

            logger.info(f"[GeminiScriptDirector] Generated {len(scenes)} storyboard scenes for idea: '{idea[:50]}...' (total ~{sum(s.estimated_duration_sec for s in scenes):.1f}s)")
            return scenes

        except Exception as e:
            logger.error(f"[GeminiScriptDirector] Error creating storyboard: {e}. Returning empty list for smart fallback.")
            return []

    @classmethod
    def create_single_scene_prompt(cls, scene_text: str, has_color: bool = True) -> str:
        """
        Chuyển một câu văn/phân cảnh tiếng Việt đơn lẻ thành visual prompt tiếng Anh chuẩn mực,
        hỗ trợ cả chế độ có đổ màu (Ghibli watercolor) và không đổ màu (Comic ink line art).
        """
        api_key = cls.get_api_key()
        base_style_template = (
            "Masterpiece 2D Japanese manga illustration, traditional hand-drawn manga panel art, "
            "bold crisp black ink outlines with variable brush stroke thickness, "
            "clean flat cel-shaded coloring with muted earthy watercolor tones, screentone-style halftone shading on warm vintage cream paper #F5EBD7. "
            "{content}. Distinct 2D manga linework, clean flat coloring, strictly 2D flat art, strictly no 3D rendering, no CGI, absolutely no 3D models or plastic gloss, 1080p widescreen, no text, no watermark"
        )
        if not api_key:
            return base_style_template.format(content=scene_text)

        try:
            from google import genai

            client = genai.Client(api_key=api_key)
            prompt = (
                "Bạn là đạo diễn hình ảnh storyboard manga chuyên nghiệp. "
                "Nhiệm vụ: Chuyển câu văn sau thành 1 mô tả trực quan chi tiết sinh động bằng tiếng Anh cho tác phẩm tranh vẽ 2D manga: "
                "QUY TẮC QUAN TRỌNG: "
                "1. Xác định rõ TẤT CẢ thực thể (nhân vật + TẤT CẢ đồ vật/đạo cụ tương tác dù lớn hay nhỏ). "
                "2. Mỗi đồ vật PHẢI được mô tả riêng biệt kèm trạng thái vật lý cụ thể (đang rơi, đang cầm, đang vỡ, đang nằm trên bàn, đang bay...). "
                "3. TUYỆT ĐỐI KHÔNG bỏ sót bất kỳ đồ vật hay chi tiết hành động nào được nhắc đến trong câu văn (ví dụ: làm rơi cốc nước thì BẮT BUỘC phải mô tả rõ cái cốc nước đang rơi lơ lửng kèm giọt nước bắn ra). "
                "4. Nếu có con rắn (snake): BẮT BUỘC mô tả là 'an elegant elongated slender serpentine green pit viper snake with coiled scaly body, distinct triangular head, reptilian slit eyes, flicking forked tongue; strictly serpentine reptile anatomy, strictly NO frog or amphibian limbs or wide mouth'. "
                "5. Nếu con rắn săn mồi: mô tả con mồi là 'a small cute field mouse or small rodent hiding cautiously among the grass blades', KHÔNG dùng từ frog. "
                "6. Bối cảnh môi trường chi tiết (cây cối, đất đá, cỏ lau, ánh sáng) và phong cách 2D manga phẳng. "
                "Không có chữ trong tranh, không thêm lời dẫn giải, chỉ trả về duy nhất nội dung tiếng Anh mô tả bối cảnh và hành động.\n"
                f"Câu văn: {scene_text}"
            )
            for m in cls.CANDIDATE_MODELS:
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
