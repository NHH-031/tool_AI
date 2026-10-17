from __future__ import annotations

import logging
import random
import urllib.parse
from pathlib import Path
from typing import Optional

import cv2
import httpx
import numpy as np
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from core.artwork.base import ImageGeneratorProvider
from core.artwork.high_fidelity import HighFidelityArtProvider
from core.artwork.prompt_builder import StructuredIllustrationPrompt

logger = logging.getLogger(__name__)


class PollinationsArtProvider(ImageGeneratorProvider):
    """
    Nhà cung cấp sinh ảnh Whiteboard Art siêu tốc miễn phí qua Pollinations.ai REST API.
    Sử dụng HTTPX AsyncClient non-blocking kết hợp Tenacity retry logic (exponential backoff).
    100% miễn phí, không cần token/API key, không bị giới hạn ZeroGPU quota.
    Tự động fallback về HighFidelityArtProvider nếu mất mạng hoặc service bận.
    """

    def __init__(self, fallback_provider: Optional[ImageGeneratorProvider] = None):
        self.fallback_provider = fallback_provider or HighFidelityArtProvider()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1.0, min=1.0, max=5.0),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True,
    )
    async def _fetch_pollinations(self, refined_prompt: str) -> bytes:
        encoded_prompt = urllib.parse.quote(refined_prompt[:280])
        seed = random.randint(1000, 999999)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true&seed={seed}&model=turbo"

        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                url_def = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true&seed={seed}"
                resp = await client.get(url_def, headers=headers)
            resp.raise_for_status()
            return resp.content

    async def generate_artwork(
        self,
        prompt: StructuredIllustrationPrompt,
        output_path: Path,
        width: int = 1920,
        height: int = 1080,
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        scene_ctx = getattr(prompt, "scene_context", "").strip()
        full_p = getattr(prompt, "full_prompt", "").strip()
        is_color = getattr(prompt, "has_color", True)

        if not is_color:
            if scene_ctx and any(k in scene_ctx.lower() for k in ["ink line art", "cross-hatching", "comic book"]):
                refined_prompt = scene_ctx
            elif full_p and any(k in full_p.lower() for k in ["ink line art", "cross-hatching", "comic book"]):
                refined_prompt = full_p
            else:
                try:
                    from core.artwork.gemini_director import GeminiScriptDirector
                    if GeminiScriptDirector.is_available() and scene_ctx:
                        refined_prompt = GeminiScriptDirector.create_single_scene_prompt(scene_ctx, has_color=False)
                    else:
                        refined_prompt = (
                            f"Masterpiece comic book ink line art illustration, fine charcoal and dip-pen drawing, crisp expressive dark ink contours, intricate cross-hatching and hatching shading textures. "
                            f"{prompt.subject}. {prompt.action}. Dynamic expressive anatomy, lush detailed environment on vintage warm cream paper #F5EBD7, absolutely NO colors, NO watercolor washes, NO gray smudges, pristine black line art masterpiece, 1080p widescreen, no text"
                        )
                except Exception:
                    refined_prompt = (
                        f"Masterpiece comic book ink line art illustration, fine charcoal and dip-pen drawing, crisp expressive dark ink contours, intricate cross-hatching and hatching shading textures. "
                        f"{prompt.subject}. {prompt.action}. Dynamic expressive anatomy, lush detailed environment on vintage warm cream paper #F5EBD7, absolutely NO colors, NO watercolor washes, NO gray smudges, pristine black line art masterpiece, 1080p widescreen, no text"
                    )
        else:
            if scene_ctx and any(k in scene_ctx.lower() for k in ["storybook", "ghibli", "illustration", "anime", "watercolor"]):
                refined_prompt = scene_ctx
            elif full_p and any(k in full_p.lower() for k in ["storybook", "ghibli", "illustration", "anime", "watercolor"]):
                refined_prompt = full_p
            else:
                try:
                    from core.artwork.gemini_director import GeminiScriptDirector
                    if GeminiScriptDirector.is_available() and scene_ctx:
                        refined_prompt = GeminiScriptDirector.create_single_scene_prompt(scene_ctx, has_color=True)
                    else:
                        refined_prompt = (
                            f"Vibrant Studio Ghibli inspired anime watercolor storybook illustration, clear clean dark ink outlines and rich warm harmonious colors. "
                            f"{prompt.subject}. {prompt.action}. Clear distinct contour lines, rich watercolor and cel-shaded color fills, "
                            f"harmonious soft sunny lighting, high detail, masterpiece, 1080p widescreen"
                        )
                except Exception:
                    refined_prompt = (
                        f"Vibrant Studio Ghibli inspired anime watercolor storybook illustration, clear clean dark ink outlines and rich warm harmonious colors. "
                        f"{prompt.subject}. {prompt.action}. Clear distinct contour lines, rich watercolor and cel-shaded color fills, "
                        f"harmonious soft sunny lighting, high detail, masterpiece, 1080p widescreen"
                    )

        logger.info(f"[PollinationsArtProvider] Requesting image for prompt: '{refined_prompt[:80]}...'")

        try:
            content = await self._fetch_pollinations(refined_prompt)

            # Giải mã ảnh từ memory buffer
            nparr = np.frombuffer(content, np.uint8)
            src = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if src is None:
                raise ValueError("Could not decode image received from Pollinations.ai")

            # 1. Resize về kích thước canvas chuẩn 1920x1080 với Lanczos-4
            resized = cv2.resize(src, (width, height), interpolation=cv2.INTER_LANCZOS4)

            # 2. Tăng cường độ nét viền contour nhưng bảo toàn 100% màu sắc nguyên bản
            gaussian = cv2.GaussianBlur(resized, (0, 0), 2.0)
            enhanced = cv2.addWeighted(resized, 1.2, gaussian, -0.2, 0)

            cv2.imwrite(str(output_path), enhanced)
            logger.info(f"[PollinationsArtProvider] Successfully saved vibrant storybook artwork at {output_path}")
            return output_path

        except Exception as e:
            logger.warning(
                f"[PollinationsArtProvider] Pollinations failed or timed out ({e}). "
                f"Falling back to {type(self.fallback_provider).__name__}..."
            )
            return await self.fallback_provider.generate_artwork(
                prompt=prompt,
                output_path=output_path,
                width=width,
                height=height,
            )
