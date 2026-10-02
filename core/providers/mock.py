from __future__ import annotations

import io
from pathlib import Path
from typing import Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel

from .base import (
    AudioSynthesisResult,
    ImageGenerationResult,
    ImageProvider,
    LLMMessage,
    LLMProvider,
    LLMResponse,
    StorageProvider,
    TTSProvider,
)

T = TypeVar("T", bound=BaseModel)


class MockLLMProvider(LLMProvider):
    """Mock LLM Provider phục vụ unit test và phát triển cục bộ."""

    def __init__(self, predefined_responses: Optional[Dict[str, str]] = None):
        self.predefined_responses = predefined_responses or {}
        self.call_history: List[List[LLMMessage]] = []

    async def generate_text(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        self.call_history.append(messages)
        last_message = messages[-1].content if messages else ""
        content = self.predefined_responses.get(
            last_message,
            "Mock LLM: Phân tích kịch bản hoàn tất cho video whiteboard."
        )
        return LLMResponse(
            content=content,
            token_usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            model_name="mock-llm-v1",
        )

    async def generate_structured(
        self,
        messages: List[LLMMessage],
        response_schema: Type[T],
        temperature: float = 0.2,
    ) -> T:
        self.call_history.append(messages)
        # Sinh một instance tối thiểu mặc định của schema
        return response_schema.model_validate(
            response_schema.model_construct()
        )


class MockTTSProvider(TTSProvider):
    """Mock TTS Provider sinh dữ liệu âm thanh giả lập."""

    def __init__(self, char_per_sec: float = 15.0):
        self.char_per_sec = char_per_sec

    async def synthesize_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        language: str = "vi-VN",
        speed: float = 1.0,
    ) -> AudioSynthesisResult:
        # Giả lập thời lượng dựa trên số lượng ký tự
        dur_sec = max(0.5, len(text) / (self.char_per_sec * speed))
        duration_ms = int(dur_sec * 1000)
        # Giả lập 100 bytes audio header
        dummy_audio = b"MOCK_MP3_AUDIO_HEADER" + (b"\x00" * 128)
        return AudioSynthesisResult(
            audio_bytes=dummy_audio,
            format="mp3",
            duration_ms=duration_ms,
            sample_rate=24000,
        )


class MockImageProvider(ImageProvider):
    """Mock Image Provider sinh file ảnh PNG tối giản có kích thước chuẩn."""

    async def generate_image(
        self,
        prompt: str,
        style_preset: str = "minimal_lineart",
        width: int = 1672,
        height: int = 941,
    ) -> ImageGenerationResult:
        from PIL import Image
        # Tạo ảnh nền màu giấy ngà #F6F1E3
        img = Image.new("RGB", (width, height), color=(246, 241, 227))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        raw_bytes = buf.getvalue()
        return ImageGenerationResult(
            image_bytes=raw_bytes,
            format="png",
            width=width,
            height=height,
        )


class MockStorageProvider(StorageProvider):
    """Mock Storage Provider lưu trữ asset trên in-memory dict hoặc local scratch."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir
        self.memory_store: Dict[str, bytes] = {}

    async def save_asset(self, path: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        clean_path = path.replace("\\", "/").lstrip("/")
        if self.base_dir:
            target = self.base_dir / clean_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            return str(target)
        self.memory_store[clean_path] = data
        return f"memory://{clean_path}"

    async def get_asset(self, path: str) -> bytes:
        clean_path = path.replace("\\", "/").lstrip("/")
        if self.base_dir:
            target = self.base_dir / clean_path
            if target.exists():
                return target.read_bytes()
        if clean_path in self.memory_store:
            return self.memory_store[clean_path]
        raise FileNotFoundError(f"Asset not found: {path}")

    async def exists(self, path: str) -> bool:
        clean_path = path.replace("\\", "/").lstrip("/")
        if self.base_dir and (self.base_dir / clean_path).exists():
            return True
        return clean_path in self.memory_store

    def get_public_url(self, path: str) -> str:
        clean_path = path.replace("\\", "/").lstrip("/")
        if self.base_dir:
            return f"file:///{self.base_dir.resolve()}/{clean_path}"
        return f"http://localhost:8000/assets/{clean_path}"
