from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from core.artwork.base import ImageGeneratorProvider
from core.artwork.flux_cloud import FluxCloudArtProvider
from core.artwork.flux_local import FluxLocalArtProvider
from core.artwork.high_fidelity import HighFidelityArtProvider
from core.artwork.pollinations import PollinationsArtProvider
from core.artwork.prompt_builder import StructuredIllustrationPrompt

logger = logging.getLogger(__name__)


class HybridFluxArtProvider(ImageGeneratorProvider):
    """
    Nhà cung cấp sinh ảnh Whiteboard Hybrid đa tầng:
    - Tier 1: Kiểm tra ComfyUI Local (port 8188) với FLUX.2 Klein 4B trên GPU RTX 3050.
    - Tier 2: Gọi Cloud FLUX Space (ByteDance Hyper-FLUX / FLUX.1-schnell) kèm HF_TOKEN để hưởng ZeroGPU quota cao.
    - Tier 3: Fallback an toàn về HighFidelityArtProvider nếu mất mạng hoàn toàn.
    """

    def __init__(
        self,
        local_provider: Optional[FluxLocalArtProvider] = None,
        cloud_provider: Optional[FluxCloudArtProvider] = None,
    ):
        self.pollinations_provider = PollinationsArtProvider(
            fallback_provider=HighFidelityArtProvider()
        )
        self.cloud_provider = cloud_provider or FluxCloudArtProvider(
            fallback_provider=self.pollinations_provider
        )
        self.local_provider = local_provider or FluxLocalArtProvider(
            fallback_provider=self.cloud_provider
        )

    async def generate_artwork(
        self,
        prompt: StructuredIllustrationPrompt,
        output_path: Path,
        width: int = 1920,
        height: int = 1080,
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # 1. Thử local nếu ComfyUI đang online
        if self.local_provider.is_available():
            logger.info("[HybridFluxArtProvider] ComfyUI local server is ONLINE. Generating via Local FLUX...")
            try:
                return await self.local_provider.generate_artwork(
                    prompt=prompt,
                    output_path=output_path,
                    width=width,
                    height=height,
                )
            except Exception as e:
                logger.warning(f"[HybridFluxArtProvider] Local generation error: {e}. Switching to Cloud FLUX...")

        # 2. Chạy Cloud FLUX với HF_TOKEN
        hf_token = os.getenv("HF_TOKEN", "").strip()
        logger.info(
            f"[HybridFluxArtProvider] Routing to Cloud FLUX Space "
            f"(HF_TOKEN: {'Đã cấu hình' if hf_token else 'Chưa có'})..."
        )
        return await self.cloud_provider.generate_artwork(
            prompt=prompt,
            output_path=output_path,
            width=width,
            height=height,
        )
