import asyncio
from core.providers.base import (
    LLMMessage,
    LLMProvider,
    TTSProvider,
    ImageProvider,
    StorageProvider,
)
from core.providers.mock import (
    MockLLMProvider,
    MockTTSProvider,
    MockImageProvider,
    MockStorageProvider,
)


def test_mock_llm_provider():
    async def _test():
        llm = MockLLMProvider()
        assert isinstance(llm, LLMProvider)
        res = await llm.generate_text([LLMMessage(role="user", content="Hello")])
        assert res.content != ""
        assert res.model_name == "mock-llm-v1"
    asyncio.run(_test())


def test_mock_tts_provider():
    async def _test():
        tts = MockTTSProvider()
        assert isinstance(tts, TTSProvider)
        res = await tts.synthesize_speech("Câu thoại kiểm thử.")
        assert len(res.audio_bytes) > 0
        assert res.duration_ms > 0
        assert res.format == "mp3"
    asyncio.run(_test())


def test_mock_image_provider():
    async def _test():
        img_prov = MockImageProvider()
        assert isinstance(img_prov, ImageProvider)
        res = await img_prov.generate_image("A minimalist monkey drawing")
        assert res.width == 1672
        assert res.height == 941
        assert len(res.image_bytes) > 0
        assert res.format == "png"
    asyncio.run(_test())


def test_mock_storage_provider():
    async def _test():
        storage = MockStorageProvider()
        assert isinstance(storage, StorageProvider)
        key = "test/scene.json"
        data = b'{"hello": "world"}'
        saved_uri = await storage.save_asset(key, data, "application/json")
        assert "memory://" in saved_uri
        assert await storage.exists(key) is True
        loaded = await storage.get_asset(key)
        assert loaded == data
    asyncio.run(_test())
