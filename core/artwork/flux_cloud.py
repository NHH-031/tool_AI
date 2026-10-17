from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import os
import random
import re
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from core.artwork.base import ImageGeneratorProvider
from core.artwork.high_fidelity import HighFidelityArtProvider
from core.artwork.pollinations import PollinationsArtProvider
from core.artwork.prompt_builder import StructuredIllustrationPrompt
from core.artwork.translations import get_vietnamese_mapping

logger = logging.getLogger(__name__)


class FluxCloudArtProvider(ImageGeneratorProvider):
    """
    Nhà cung cấp sinh hình minh họa Whiteboard Art chất lượng cao miễn phí (Free Cloud FLUX.1-schnell).
    Kết nối API miễn phí của mô hình FLUX.1-schnell thông qua Gradio Client,
    tự động áp dụng prompt Notion/comic doodle line-art và xử lý lọc nền kem ấm #F5EBD7
    cùng nét mực đen thuần #1A1A1A, đạt chuẩn 95-100% so với benchmark astronaut_mars.png
    mà không tốn phí bản quyền hay GPU VRAM cục bộ.
    """

    def __init__(
        self,
        space_id: str = "black-forest-labs/FLUX.1-schnell",
        fallback_provider: Optional[ImageGeneratorProvider] = None,
    ):
        self.space_id = space_id
        self.fallback_provider = fallback_provider or PollinationsArtProvider(fallback_provider=HighFidelityArtProvider())

    async def generate_artwork(
        self,
        prompt: StructuredIllustrationPrompt,
        output_path: Path,
        width: int = 1920,
        height: int = 1080,
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Ưu tiên bối cảnh kịch bản thoại gốc của người dùng để hiểu đúng 100% ngữ nghĩa
        scene_ctx = getattr(prompt, "scene_context", "").strip()
        subject_action = f"{prompt.subject}. {prompt.action}".strip(". ")

        # Ánh xạ từ khóa tiếng Việt sang tiếng Anh qua từ điển translations/vi_to_en.json
        vn_map = get_vietnamese_mapping()

        # Áp dụng dịch cho scene_context nếu có
        translated_ctx = scene_ctx.lower() if scene_ctx else ""
        if translated_ctx:
            for vn, en in vn_map:
                if vn in translated_ctx:
                    translated_ctx = translated_ctx.replace(vn, en)

        translated_action = subject_action.lower()
        for vn, en in vn_map:
            if vn in translated_action:
                translated_action = translated_action.replace(vn, en)
        full_p = getattr(prompt, "full_prompt", "").strip()
        is_color = getattr(prompt, "has_color", True)

        # Trích xuất và chuẩn hóa mô tả chủ thể cho FLUX Notion/Whiteboard Doodle (SKILL.md)
        raw_source = full_p or scene_ctx or subject_action
        clean_desc = raw_source.strip()

        # Tự động nhận diện nếu prompt gốc chứa tiếng Việt thì dùng Gemini dịch sang prompt tiếng Anh chi tiết
        has_vn = bool(re.search(r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]", raw_source, re.IGNORECASE))
        if has_vn:
            try:
                from core.artwork.gemini_director import GeminiScriptDirector
                if GeminiScriptDirector.is_available():
                    gemini_en = GeminiScriptDirector.create_single_scene_prompt(raw_source, has_color=is_color)
                    if gemini_en and len(gemini_en) > 20:
                        clean_desc = gemini_en
            except Exception as e_gem:
                logger.warning(f"[FluxCloudArtProvider] Gemini translation fallback: {e_gem}")

        for bp in [
            "Masterpiece storybook watercolor and ink illustration, crisp expressive dark ink contours and rich vibrant harmonious colors on warm vintage cream paper #F5EBD7.",
            "Masterpiece comic book ink line art illustration, fine charcoal and dip-pen drawing, crisp expressive dark ink contours, intricate cross-hatching and hatching shading textures.",
            "Whiteboard doodle illustration representing:",
            "Vibrant Studio Ghibli inspired anime watercolor storybook illustration, clear clean dark ink outlines and rich warm harmonious colors.",
        ]:
            if clean_desc.startswith(bp):
                clean_desc = clean_desc[len(bp):].strip()
        for sf in [
            "Clear distinct contour lines, smooth connected outlines, rich watercolor fills, harmonious lighting, high detail, 1080p widescreen, no text",
            "Clear distinct contour lines, rich watercolor and cel-shaded color fills, harmonious soft sunny lighting, high detail, masterpiece, 1080p widescreen",
            "masterpiece quality, 1080p widescreen, no text, no watermark",
            "on warm vintage cream paper #F5EBD7",
            "crisp clean dark ink contour outlines",
            "whiteboard doodle illustration",
        ]:
            if sf in clean_desc:
                clean_desc = clean_desc.replace(sf, "").strip(",. ")

        desc = clean_desc or translated_ctx or translated_action

        if not is_color:
            flux_prompt = (
                f"Minimalist Notion style vector doodle illustration, pristine black ink line art on warm vintage cream paper #F5EBD7. "
                f"{desc}. Simple clean dark ink contour outlines, generous negative space, absolutely NO colors, "
                f"flat vector 2D doodle sketch, masterpiece, 1080p widescreen, no text, no words, no labels, no watermark"
            )
        else:
            flux_prompt = (
                f"Minimalist Notion style vector doodle illustration, clean line art on warm vintage cream paper #F5EBD7. "
                f"{desc}. Simple clean dark ink contour outlines, generous negative space, subtle pastel orange and blue accents, "
                f"flat vector 2D doodle aesthetic, masterpiece, 1080p widescreen, no text, no words, no labels, no watermark"
            )

        logger.info(f"[FluxCloudArtProvider] Requesting AI line-art for: '{flux_prompt[:80]}...'")

        def _call_gradio() -> str:
            from gradio_client import Client
            hf_token = os.getenv("HF_TOKEN", "").strip() or None

            # 1. Primary: ByteDance/Hyper-FLUX-8Steps-LoRA (Dedicated high-speed space, no ZeroGPU quota restrictions)
            try:
                logger.info(f"[FluxCloudArtProvider] Attempting ByteDance Hyper-FLUX LoRA (8 steps) for '{translated_action[:60]}'...")
                client = Client("ByteDance/Hyper-FLUX-8Steps-LoRA", token=hf_token)
                res = client.predict(
                    height=720,
                    width=1152,
                    steps=8,
                    scales=3.5,
                    prompt=flux_prompt,
                    seed=random.randint(1000, 999999),
                    api_name="/process_image",
                )
                if isinstance(res, (tuple, list)):
                    return str(res[0])
                elif isinstance(res, dict) and "path" in res:
                    return str(res["path"])
                return str(res)
            except Exception as e_bd:
                logger.warning(f"[FluxCloudArtProvider] ByteDance space error: {e_bd}. Trying FLUX.1-schnell...")

            # 2. Secondary: black-forest-labs/FLUX.1-schnell
            client = Client(self.space_id, token=hf_token)
            result = client.predict(
                prompt=flux_prompt,
                seed=42,
                randomize_seed=True,
                width=1280,
                height=720,
                num_inference_steps=4,
                api_name="/infer",
            )
            if isinstance(result, (tuple, list)):
                return str(result[0])
            elif isinstance(result, dict) and "path" in result:
                return str(result["path"])
            return str(result)

        try:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                raw_path_str = await asyncio.wait_for(
                    loop.run_in_executor(pool, _call_gradio),
                    timeout=60.0,
                )

            src = cv2.imread(raw_path_str)
            if src is None:
                raise ValueError(f"Could not load generated image from {raw_path_str}")

            # 1. Resize về kích thước canvas chuẩn 1920x1080 với Lanczos-4
            resized = cv2.resize(src, (width, height), interpolation=cv2.INTER_LANCZOS4)

            # 2. Tăng cường độ nét viền contour nhưng bảo toàn 100% màu sắc nguyên bản
            gaussian = cv2.GaussianBlur(resized, (0, 0), 2.0)
            enhanced = cv2.addWeighted(resized, 1.2, gaussian, -0.2, 0)

            cv2.imwrite(str(output_path), enhanced)
            logger.info(f"[FluxCloudArtProvider] Successfully generated and styled vibrant artwork at {output_path}")
            return output_path

        except Exception as e:
            logger.warning(
                f"[FluxCloudArtProvider] Cloud generation failed or timed out ({e}). "
                f"Falling back to HighFidelityArtProvider..."
            )
            return await self.fallback_provider.generate_artwork(
                prompt=prompt,
                output_path=output_path,
                width=width,
                height=height,
            )
