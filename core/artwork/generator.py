"""Module AI Artwork Generator (Modular Facade).

Tất cả các provider đã được tách thành các module chuyên biệt:
- base.py: ImageGeneratorProvider
- gemini_imagen.py: GeminiImagenGenerator
- openai_dalle.py: OpenAIImageGenerator
- high_fidelity.py: HighFidelityArtProvider
- flux_cloud.py: FluxCloudArtProvider
- pollinations.py: PollinationsArtProvider
- flux_local.py: FluxLocalArtProvider
- hybrid_flux.py: HybridFluxArtProvider
- factory.py: ArtworkGeneratorFactory
- translations/vi_to_en.json: Bộ từ điển ánh xạ ngữ nghĩa VN -> EN

Module này re-export toàn bộ để đảm bảo 100% backward compatibility cho codebase hiện hữu.
"""
from __future__ import annotations

from core.artwork.base import ImageGeneratorProvider
from core.artwork.factory import ArtworkGeneratorFactory
from core.artwork.flux_cloud import FluxCloudArtProvider
from core.artwork.flux_local import FluxLocalArtProvider
from core.artwork.gemini_imagen import GeminiImagenGenerator
from core.artwork.high_fidelity import HighFidelityArtProvider
from core.artwork.hybrid_flux import HybridFluxArtProvider
from core.artwork.openai_dalle import OpenAIImageGenerator
from core.artwork.pollinations import PollinationsArtProvider
from core.artwork.prompt_builder import StructuredIllustrationPrompt

__all__ = [
    "ImageGeneratorProvider",
    "GeminiImagenGenerator",
    "OpenAIImageGenerator",
    "HighFidelityArtProvider",
    "FluxCloudArtProvider",
    "PollinationsArtProvider",
    "FluxLocalArtProvider",
    "HybridFluxArtProvider",
    "ArtworkGeneratorFactory",
    "StructuredIllustrationPrompt",
]
