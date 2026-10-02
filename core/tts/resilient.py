from __future__ import annotations

import asyncio
import logging
from typing import List, Optional
from core.schemas.tts import NarrationTiming, TTSAudioResult, VoiceConfig
from .base import InvalidVoiceError, TTSConnectionError, TTSProvider, TTSSynthesisError

logger = logging.getLogger(__name__)


class ResilientTTSProvider(TTSProvider):
    """
    Wrapper bảo vệ dịch vụ TTS với cơ chế tự động thử lại (retry) và chuyển hướng dự phòng (fallback).
    Khi provider chính gặp lỗi kết nối hoặc lỗi xử lý, hệ thống tự động:
    1. Thử lại tối đa max_retries lần với độ trễ lũy tiến.
    2. Nếu vẫn thất bại, chuyển hướng sang fallback_provider nếu có.
    """

    def __init__(
        self,
        primary_provider: TTSProvider,
        fallback_provider: Optional[TTSProvider] = None,
        max_retries: int = 2,
        initial_delay: float = 0.05,
    ):
        self.primary_provider = primary_provider
        self.fallback_provider = fallback_provider
        self.max_retries = max_retries
        self.initial_delay = initial_delay

    def get_supported_voices(self) -> List[str]:
        voices = set(self.primary_provider.get_supported_voices())
        if self.fallback_provider:
            voices.update(self.fallback_provider.get_supported_voices())
        return list(voices)

    async def _execute_with_resilience(self, func_name: str, *args, **kwargs):
        last_error: Optional[Exception] = None
        delay = self.initial_delay

        # 1. Thử gọi provider chính kèm retry
        for attempt in range(self.max_retries + 1):
            try:
                fn = getattr(self.primary_provider, func_name)
                return await fn(*args, **kwargs)
            except InvalidVoiceError:
                # Lỗi giọng đọc không hợp lệ thì không retry
                raise
            except (TTSConnectionError, TTSSynthesisError, Exception) as exc:
                last_error = exc
                if attempt < self.max_retries:
                    await asyncio.sleep(delay)
                    delay *= 2
                else:
                    logger.warning(
                        f"Provider chính {self.primary_provider.__class__.__name__} đã thất bại "
                        f"sau {self.max_retries + 1} lần thử. Lỗi: {str(exc)}"
                    )

        # 2. Nếu có fallback provider, kích hoạt dự phòng
        if self.fallback_provider is not None:
            logger.info(
                f"Kích hoạt provider dự phòng: {self.fallback_provider.__class__.__name__}"
            )
            fn = getattr(self.fallback_provider, func_name)
            res = await fn(*args, **kwargs)
            if isinstance(res, TTSAudioResult):
                res.metadata["resilient_fallback_active"] = True
                res.metadata["primary_failure_error"] = str(last_error)
            return res

        # 3. Không có fallback -> ném lỗi gốc
        raise last_error or TTSSynthesisError("TTS operation failed with unknown error.")

    async def generate(
        self,
        text: str,
        voice_config: Optional[VoiceConfig] = None,
    ) -> TTSAudioResult:
        return await self._execute_with_resilience("generate", text, voice_config)

    async def get_duration(
        self,
        text: str,
        voice_config: Optional[VoiceConfig] = None,
    ) -> float:
        return await self._execute_with_resilience("get_duration", text, voice_config)

    async def get_timing(
        self,
        text: str,
        voice_config: Optional[VoiceConfig] = None,
    ) -> NarrationTiming:
        return await self._execute_with_resilience("get_timing", text, voice_config)

    async def preview(
        self,
        text: str,
        voice_config: Optional[VoiceConfig] = None,
    ) -> TTSAudioResult:
        return await self._execute_with_resilience("preview", text, voice_config)
