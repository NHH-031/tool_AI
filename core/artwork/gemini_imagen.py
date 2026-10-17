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


class GeminiImagenGenerator(ImageGeneratorProvider):
    """
    Nhà cung cấp sinh ảnh thông qua Google Imagen 3 API.
    Sử dụng HTTPX AsyncClient non-blocking với cơ chế thử lại Tenacity retry logic.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "").strip()

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1.0, min=1.0, max=4.0),
        retry=retry_if_exception_type(httpx.RequestError),
        reraise=True,
    )
    async def _post_json(self, client: httpx.AsyncClient, url: str, payload: dict) -> httpx.Response:
        return await client.post(url, json=payload, headers={"Content-Type": "application/json"})

    async def generate_artwork(
        self,
        prompt: StructuredIllustrationPrompt,
        output_path: Path,
        width: int = 1920,
        height: int = 1080,
    ) -> Path:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured for GeminiImagenGenerator.")

        async with httpx.AsyncClient(timeout=60.0) as client:
            # 1. Try multimodal generateContent image models
            gen_content_models = [
                "gemini-2.5-flash-image",
                "gemini-3.1-flash-image",
                "gemini-3-pro-image",
                "gemini-3.1-flash-lite-image",
            ]
            last_error = None
            for model in gen_content_models:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
                payload = {
                    "contents": [
                        {"parts": [{"text": prompt.full_prompt}]}
                    ],
                    "generationConfig": {
                        "responseModalities": ["IMAGE"]
                    }
                }
                try:
                    resp = await self._post_json(client, url, payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            for p in parts:
                                if "inlineData" in p and "data" in p["inlineData"]:
                                    img_bytes = base64.b64decode(p["inlineData"]["data"])
                                    output_path.parent.mkdir(parents=True, exist_ok=True)
                                    output_path.write_bytes(img_bytes)
                                    logger.info(f"[GeminiImagenGenerator] Saved generated artwork to {output_path} using {model}")
                                    return output_path
                    else:
                        last_error = f"HTTP {resp.status_code}: {resp.text}"
                        logger.warning(f"[GeminiImagenGenerator] {model} returned {last_error}")
                except Exception as e:
                    last_error = str(e)
                    logger.warning(f"[GeminiImagenGenerator] Error on {model}: {e}")
                    continue

            # 2. Try Imagen 3 predictImages models
            model_candidates = [
                "imagen-3.0-generate-002",
                "imagen-3.0-fast-generate-001",
            ]
            for model in model_candidates:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:predictImages?key={self.api_key}"
                payload = {
                    "instances": [{"prompt": prompt.full_prompt}],
                    "parameters": {
                        "sampleCount": 1,
                        "aspectRatio": "16:9",
                        "outputOptions": {"mimeType": "image/png"},
                    },
                }

                try:
                    resp = await self._post_json(client, url, payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        predictions = data.get("predictions", [])
                        if not predictions:
                            raise RuntimeError(f"No image predictions returned by {model}.")
                        img_b64 = predictions[0].get("bytesBase64Encoded")
                        img_bytes = base64.b64decode(img_b64)
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        output_path.write_bytes(img_bytes)
                        logger.info(f"[GeminiImagenGenerator] Saved generated artwork to {output_path} using {model}")
                        return output_path
                    else:
                        last_error = f"HTTP {resp.status_code}: {resp.text}"
                        logger.warning(f"[GeminiImagenGenerator] {model} returned {last_error}")
                except Exception as e:
                    last_error = str(e)
                    logger.warning(f"[GeminiImagenGenerator] Error on {model}: {e}")
                    continue

        raise RuntimeError(f"Gemini/Imagen Image API failed across models: {last_error}")
