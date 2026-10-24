from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import httpx
from pathlib import Path
from typing import Optional

from core.artwork.base import ImageGeneratorProvider
from core.artwork.flux_cloud import FluxCloudArtProvider
from core.artwork.prompt_builder import StructuredIllustrationPrompt

logger = logging.getLogger(__name__)


class FluxLocalArtProvider(ImageGeneratorProvider):
    """
    Nhà cung cấp sinh ảnh FLUX.2 Klein cục bộ qua ComfyUI REST/WebSocket API (port 8188).
    Tuân thủ Quyết định #4 & #6 trong design_decisions.md:
    - Quản lý VRAM tự động qua ComfyUI --lowvram
    - Tự động áp dụng Prompt Quality Gate chuẩn SKILL.md (#F5EBD7, dark ink)
    - Tự động fallback sang Cloud / PollinationsArtProvider nếu ComfyUI offline.
    """
    PROMPT_QUALITY_SUFFIX = (
        "Masterpiece 2D Japanese manga illustration, traditional hand-drawn manga panel art, "
        "bold crisp black ink outlines with variable brush stroke thickness, clean flat cel-shaded coloring with muted earthy watercolor tones, "
        "screentone-style halftone shading on warm vintage cream paper #F5EBD7, strictly 2D flat art, absolutely NO 3D render, NO CGI, NO 3D models, "
        "NO plastic sheen, NO volumetric lighting, 1080p widescreen, no text, no watermark"
    )

    def __init__(
        self,
        base_url: Optional[str] = None,
        fallback_provider: Optional[ImageGeneratorProvider] = None,
    ):
        self.base_url = (base_url or os.getenv("COMFYUI_URL", "http://localhost:8188")).rstrip("/")
        self.fallback_provider = fallback_provider or FluxCloudArtProvider()

    def is_available(self) -> bool:
        """Kiểm tra xem ComfyUI server có đang chạy không."""
        try:
            with httpx.Client(timeout=1.0) as client:
                resp = client.get(f"{self.base_url}/system_stats")
                return resp.status_code == 200
        except Exception:
            return False

    async def generate_artwork(
        self,
        prompt: StructuredIllustrationPrompt,
        output_path: Path,
        width: int = 1920,
        height: int = 1080,
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. Prompt Quality Gate (Decision #6 & #8)
        raw_prompt = getattr(prompt, "full_prompt", "") or getattr(prompt, "scene_context", "") or prompt.subject
        if "#f5ebd7" not in raw_prompt.lower():
            guaranteed_prompt = f"{raw_prompt.rstrip('. ')}, {self.PROMPT_QUALITY_SUFFIX}"
        else:
            guaranteed_prompt = raw_prompt

        # 2. Thử gọi ComfyUI nếu server online
        if self.is_available():
            try:
                loop = asyncio.get_running_loop()
                saved_path = await loop.run_in_executor(
                    None, self._call_comfyui_api, guaranteed_prompt, output_path, width, height
                )
                if saved_path and saved_path.exists():
                    logger.info(f"[FluxLocalArtProvider] Saved artwork to {saved_path} via local ComfyUI FLUX")
                    return saved_path
            except Exception as e:
                logger.warning(f"[FluxLocalArtProvider] ComfyUI local error: {e}. Falling back...")

        # 3. Fallback sang cloud / high-fidelity
        logger.info(f"[FluxLocalArtProvider] Forwarding generation to {type(self.fallback_provider).__name__}")
        return await self.fallback_provider.generate_artwork(
            prompt=prompt,
            output_path=output_path,
            width=width,
            height=height,
        )

    def _call_comfyui_api(self, prompt_text: str, output_path: Path, width: int, height: int) -> Optional[Path]:
        prompt_data = {
            "client_id": "whiteboard_studio",
            "prompt": {
                "3": {
                    "class_type": "KSampler",
                    "inputs": {
                        "cfg": 3.5,
                        "denoise": 1,
                        "latent_image": ["5", 0],
                        "model": ["4", 0],
                        "negative": ["7", 0],
                        "positive": ["6", 0],
                        "sampler_name": "euler",
                        "scheduler": "simple",
                        "seed": 42,
                        "steps": 20
                    }
                },
                "4": {
                    "class_type": "CheckpointLoaderSimple",
                    "inputs": {"ckpt_name": "flux2-klein-4b.safetensors"}
                },
                "5": {
                    "class_type": "EmptyLatentImage",
                    "inputs": {"batch_size": 1, "height": 720, "width": 1280}
                },
                "6": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {"clip": ["4", 1], "text": prompt_text}
                },
                "7": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {"clip": ["4", 1], "text": "blurry, low quality, distorted, bad art"}
                },
                "8": {
                    "class_type": "VAEDecode",
                    "inputs": {"samples": ["3", 0], "vae": ["4", 2]}
                },
                "9": {
                    "class_type": "SaveImage",
                    "inputs": {"filename_prefix": "WhiteboardStudio", "images": ["8", 0]}
                }
            }
        }
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(f"{self.base_url}/prompt", json=prompt_data)
                if resp.status_code != 200:
                    return None
                data = resp.json()
                prompt_id = data.get("prompt_id")
                if not prompt_id:
                    return None

                for _ in range(60):
                    time.sleep(3)
                    hist_resp = client.get(f"{self.base_url}/history/{prompt_id}", timeout=10.0)
                    if hist_resp.status_code == 200:
                        hist_data = hist_resp.json()
                        if prompt_id in hist_data:
                            outputs = hist_data[prompt_id].get("outputs", {})
                            for node_id, node_output in outputs.items():
                                images = node_output.get("images", [])
                                if images:
                                    img_info = images[0]
                                    filename = img_info.get("filename")
                                    view_url = f"{self.base_url}/view?filename={filename}&type=output"
                                    img_resp = client.get(view_url, timeout=20.0)
                                    if img_resp.status_code == 200:
                                        output_path.write_bytes(img_resp.content)
                                        return output_path
        except Exception as e:
            logger.warning(f"[FluxLocalArtProvider] ComfyUI client error: {e}")
            return None
        return None
