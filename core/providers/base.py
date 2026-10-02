from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMMessage(BaseModel):
    role: str  # "system", "user", "assistant"
    content: str


class LLMResponse(BaseModel):
    content: str
    token_usage: Dict[str, int] = {}
    model_name: str = ""


class AudioSynthesisResult(BaseModel):
    audio_bytes: bytes
    format: str = "mp3"
    duration_ms: int
    sample_rate: int = 24000


class ImageGenerationResult(BaseModel):
    image_bytes: bytes
    format: str = "png"
    width: int
    height: int


class LLMProvider(ABC):
    """Giao diện trừu tượng cho Large Language Model (không phụ thuộc trực tiếp Gemini hay OpenAI)."""

    @abstractmethod
    async def generate_text(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Sinh văn bản tự do từ danh sách tin nhắn."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        messages: List[LLMMessage],
        response_schema: Type[T],
        temperature: float = 0.2,
    ) -> T:
        """Sinh dữ liệu có cấu trúc tuân thủ Pydantic Schema."""
        pass


class TTSProvider(ABC):
    """Giao diện trừu tượng cho Text-to-Speech synthesis."""

    @abstractmethod
    async def synthesize_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        language: str = "vi-VN",
        speed: float = 1.0,
    ) -> AudioSynthesisResult:
        """Chuyển đổi văn bản thành dữ liệu âm thanh kèm đo lường thời lượng."""
        pass


class ImageProvider(ABC):
    """Giao diện trừu tượng cho Image Generation (Line art / Illustration)."""

    @abstractmethod
    async def generate_image(
        self,
        prompt: str,
        style_preset: str = "minimal_lineart",
        width: int = 1672,
        height: int = 941,
    ) -> ImageGenerationResult:
        """Sinh hình ảnh phác thảo theo phong cách mỹ thuật quy định."""
        pass


class StorageProvider(ABC):
    """Giao diện trừu tượng cho lưu trữ asset (Local disk, S3, GCS, etc.)."""

    @abstractmethod
    async def save_asset(self, path: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Lưu trữ dữ liệu nhị phân và trả về URI truy cập."""
        pass

    @abstractmethod
    async def get_asset(self, path: str) -> bytes:
        """Đọc dữ liệu nhị phân của asset."""
        pass

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """Kiểm tra sự tồn tại của asset."""
        pass

    @abstractmethod
    def get_public_url(self, path: str) -> str:
        """Lấy URL xem trước công khai hoặc đường dẫn file cục bộ."""
        pass
