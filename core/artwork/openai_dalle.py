from __future__ import annotations

import base64
import logging
import os
from pathlib import Path
from typing import Optional

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from core.artwork.base import ImageGeneratorProvider
from core.artwork.prompt_builder import StructuredIllustrationPrompt

logger = logging.getLogger(__name__)


class OpenAIImageGenerator(ImageGeneratorProvider):
    """
    Nhà cung cấp sinh ảnh qua OpenAI DALL-E 3 API.
    Sử dụng HTTPX AsyncClient non-blocking kết hợp Tenacity retry logic.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "").strip()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1.0, min=2.0, max=10.0),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True,
    )
    async def _call_dalle_api(self, payload: dict) -> bytes:
        url = "https://api.openai.com/v1/images/generations"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            b64 = data["data"][0]["b64_json"]
            return base64.b64decode(b64)

    async def generate_artwork(
        self,
        prompt: StructuredIllustrationPrompt,
        output_path: Path,
        width: int = 1920,
        height: int = 1080,
    ) -> Path:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured for OpenAIImageGenerator.")

        payload = {
            "model": "dall-e-3",
            "prompt": prompt.full_prompt,
            "n": 1,
            "size": "1792x1024",
            "quality": "standard",
            "style": "natural",
            "response_format": "b64_json",
        }

        try:
            img_bytes = await self._call_dalle_api(payload)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(img_bytes)
            logger.info(f"[OpenAIImageGenerator] Saved generated artwork to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"[OpenAIImageGenerator] Error: {e}")
            raise
