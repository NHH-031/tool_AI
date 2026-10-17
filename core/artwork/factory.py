from __future__ import annotations

import logging
import os

from core.artwork.base import ImageGeneratorProvider
from core.artwork.flux_cloud import FluxCloudArtProvider
from core.artwork.flux_local import FluxLocalArtProvider
from core.artwork.gemini_imagen import GeminiImagenGenerator
from core.artwork.high_fidelity import HighFidelityArtProvider
from core.artwork.hybrid_flux import HybridFluxArtProvider
from core.artwork.openai_dalle import OpenAIImageGenerator
from core.artwork.pollinations import PollinationsArtProvider

logger = logging.getLogger(__name__)


class ArtworkGeneratorFactory:
    """Factory tự động lựa chọn Provider tối ưu theo biến môi trường."""

    @classmethod
    def create(cls) -> ImageGeneratorProvider:
        provider_type = os.getenv("IMAGE_GENERATOR_PROVIDER", "").strip().lower()
        gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        openai_key = os.getenv("OPENAI_API_KEY", "").strip()

        # 1. Nếu chỉ định rõ hybrid_flux
        if provider_type in ["hybrid_flux", "hybrid", "flux_hybrid"]:
            logger.info("[ArtworkGeneratorFactory] Using HybridFluxArtProvider (Local 4B + Cloud HF_TOKEN)")
            return HybridFluxArtProvider()

        # 2. Nếu chỉ định rõ local FLUX hoặc ComfyUI
        if provider_type in ["flux_local", "local_flux", "comfyui"]:
            logger.info("[ArtworkGeneratorFactory] Using FluxLocalArtProvider (ComfyUI FLUX.2 Klein)")
            return FluxLocalArtProvider()

        # 3. Nếu người dùng chỉ định rõ kho kiệt tác cục bộ
        if provider_type in ["high_fidelity", "masterpiece", "curated", "local"]:
            logger.info("[ArtworkGeneratorFactory] Using HighFidelityArtProvider (Curated Masterpieces)")
            return HighFidelityArtProvider()

        # 4. Nếu chỉ định rõ Pollinations (miễn phí, nhanh)
        if provider_type in ["pollinations", "turbo"]:
            logger.info("[ArtworkGeneratorFactory] Using PollinationsArtProvider")
            return PollinationsArtProvider()

        # 5. Nếu chỉ định rõ Cloud FLUX thuần
        if provider_type in ["flux_cloud"]:
            logger.info("[ArtworkGeneratorFactory] Using FluxCloudArtProvider")
            return FluxCloudArtProvider()

        # 6. Tự động kiểm tra xem ComfyUI có online không
        flux_local = FluxLocalArtProvider()
        if flux_local.is_available():
            logger.info("[ArtworkGeneratorFactory] Detected active ComfyUI service on localhost:8188. Using FluxLocalArtProvider.")
            return flux_local

        if gemini_key and provider_type == "gemini":
            logger.info("[ArtworkGeneratorFactory] Using GeminiImagenGenerator")
            return GeminiImagenGenerator(api_key=gemini_key)
        elif openai_key and provider_type == "openai":
            logger.info("[ArtworkGeneratorFactory] Using OpenAIImageGenerator")
            return OpenAIImageGenerator(api_key=openai_key)
        elif provider_type in ["flux", "hyper_flux"]:
            logger.info("[ArtworkGeneratorFactory] Using HybridFluxArtProvider (Cloud with Local Fallback)")
            return HybridFluxArtProvider()
        else:
            # Mặc định sử dụng Hybrid FLUX (vừa local vừa cloud có HF_TOKEN)
            logger.info("[ArtworkGeneratorFactory] Using HybridFluxArtProvider (Default)")
            return HybridFluxArtProvider()
