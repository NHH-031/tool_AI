"""Tests for Option A High-Fidelity Artwork Generation & Provider Pipeline.
"""
from pathlib import Path
import pytest
from PIL import Image

from core.artwork.generator import (
    ArtworkGeneratorFactory,
    FluxCloudArtProvider,
    HighFidelityArtProvider,
    ImageGeneratorProvider,
)
from core.artwork.prompt_builder import StructuredIllustrationPrompt


@pytest.mark.asyncio
async def test_high_fidelity_art_provider_resolution(tmp_path):
    """Verify HighFidelityArtProvider resolves known prompts to 1080p artwork."""
    provider = HighFidelityArtProvider()
    
    # 1. Cat climbing areca palm
    prompt_cat = StructuredIllustrationPrompt(
        subject="cat",
        action="climbing",
        relationship="gripping palm tree",
        composition="16:9",
        pose="climbing",
        line_style="charcoal sketch",
        whiteboard_style="Notion doodle",
        background="#F5EBD7",
        negative_constraints="no text",
        full_prompt="Con mèo leo cây cau"
    )
    cat_out = tmp_path / "cat_test.png"
    result = await provider.generate_artwork(prompt_cat, cat_out)
    assert result.exists()
    with Image.open(result) as img:
        assert img.size == (1920, 1080)
        
    # 2. Dog running after ball
    prompt_dog = StructuredIllustrationPrompt(
        subject="dog",
        action="running",
        relationship="chasing ball",
        composition="16:9",
        pose="running",
        line_style="charcoal sketch",
        whiteboard_style="Notion doodle",
        background="#F5EBD7",
        negative_constraints="no text",
        full_prompt="Chú chó chạy theo quả bóng"
    )
    dog_out = tmp_path / "dog_test.png"
    result_dog = await provider.generate_artwork(prompt_dog, dog_out)
    assert result_dog.exists()
    with Image.open(result_dog) as img:
        assert img.size == (1920, 1080)

    # 3. Astronaut on Mars
    prompt_astro = StructuredIllustrationPrompt(
        subject="astronaut",
        action="stepping down",
        relationship="stepping off ladder onto mars",
        composition="16:9",
        pose="walking",
        line_style="charcoal sketch",
        whiteboard_style="Notion doodle",
        background="#F5EBD7",
        negative_constraints="no text",
        full_prompt="Phi hành gia đặt chân lên Sao Hỏa"
    )
    astro_out = tmp_path / "astro_test.png"
    result_astro = await provider.generate_artwork(prompt_astro, astro_out)
    assert result_astro.exists()
    with Image.open(result_astro) as img:
        assert img.size == (1920, 1080)


def test_artwork_generator_factory(monkeypatch):
    """Verify ArtworkGeneratorFactory creates appropriate provider instances."""
    monkeypatch.setenv("IMAGE_GENERATOR_PROVIDER", "high_fidelity")
    provider_curated = ArtworkGeneratorFactory.create()
    assert isinstance(provider_curated, ImageGeneratorProvider)
    assert isinstance(provider_curated, HighFidelityArtProvider)

    monkeypatch.setenv("IMAGE_GENERATOR_PROVIDER", "flux")
    provider_flux = ArtworkGeneratorFactory.create()
    assert isinstance(provider_flux, ImageGeneratorProvider)
    assert isinstance(provider_flux, FluxCloudArtProvider)


@pytest.mark.asyncio
async def test_flux_cloud_art_provider_fallback(tmp_path):
    """Verify FluxCloudArtProvider falls back gracefully to HighFidelityArtProvider when offline."""
    fallback = HighFidelityArtProvider()
    provider = FluxCloudArtProvider(space_id="invalid/space_id", fallback_provider=fallback)

    prompt = StructuredIllustrationPrompt(
        subject="astronaut",
        action="walking on mars",
        relationship="",
        composition="16:9",
        pose="walking",
        line_style="clean line art",
        whiteboard_style="Notion doodle",
        background="#F5EBD7",
        negative_constraints="no text",
        full_prompt="Phi hành gia thám hiểm Sao Hỏa",
    )
    out_file = tmp_path / "flux_fallback_test.png"
    res = await provider.generate_artwork(prompt, out_file)
    assert res.exists()
    with Image.open(res) as img:
        assert img.size == (1920, 1080)

