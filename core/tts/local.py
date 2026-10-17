from __future__ import annotations

import asyncio
import io
import json
import logging
import os
import wave
from typing import List, Optional
import urllib.request
import urllib.error

from core.schemas.tts import NarrationTiming, TTSAudioResult, VoiceConfig
from .base import TTSProvider, TTSSynthesisError
from .edge import EdgeTTSProvider
from .timing import TimingEstimator

logger = logging.getLogger(__name__)


class LocalTTSProvider(TTSProvider):
    """
    Nhà cung cấp giọng đọc Text-to-Speech cục bộ (VieNeu / VoiceStudio).
    Kết nối qua REST API HTTP cục bộ, tự động fallback sang EdgeTTS nếu offline.
    Tuân thủ Quyết định #3 (design_decisions.md).
    """

    SUPPORTED_VOICES = [
        "vieneu-local-1",
        "voicestudio-local-1",
        "vi-VN-HoaiMyNeural",
        "vi-VN-NamMinhNeural",
    ]

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        fallback_provider: Optional[TTSProvider] = None,
    ):
        self.endpoint_url = endpoint_url or os.getenv(
            "LOCAL_TTS_URL", "http://localhost:5000/synthesize"
        )
        self.fallback_provider = fallback_provider or EdgeTTSProvider()

    def get_supported_voices(self) -> List[str]:
        return list(self.SUPPORTED_VOICES)

    def is_local_alive(self) -> bool:
        """Kiểm tra nhanh xem local TTS server có đang chạy không."""
        try:
            req = urllib.request.Request(
                self.endpoint_url,
                method="HEAD",
            )
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                return resp.status < 500
        except Exception:
            # Nhiều server TTS local không hỗ trợ HEAD mà trả 405 hoặc 404, vẫn coi là alive
            try:
                base_url = self.endpoint_url.rsplit("/", 1)[0]
                with urllib.request.urlopen(base_url, timeout=1.0) as resp:
                    return True
            except Exception:
                return False

    async def generate(
        self,
        text: str,
        voice_config: Optional[VoiceConfig] = None,
    ) -> TTSAudioResult:
        cfg = voice_config or VoiceConfig(voice_id="vi-VN-HoaiMyNeural", language="vi-VN", speed=1.0)

        # 1. Thử gọi Local TTS API nếu có URL và không bắt buộc dùng Edge
        if self.endpoint_url and not cfg.voice_id.endswith("Neural"):
            try:
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(None, self._call_local_api, text, cfg)
                if result:
                    logger.info(f"[LocalTTSProvider] Successfully synthesized {len(result.audio_bytes)} bytes via local TTS ({self.endpoint_url})")
                    return result
            except Exception as e:
                logger.warning(
                    f"[LocalTTSProvider] Local server at {self.endpoint_url} unreachable ({e}). "
                    f"Auto-falling back to EdgeTTS..."
                )

        # 2. Fallback sang EdgeTTS chất lượng cao
        logger.info("[LocalTTSProvider] Forwarding synthesis to EdgeTTS provider.")
        return await self.fallback_provider.generate(text, cfg)

    def _call_local_api(self, text: str, cfg: VoiceConfig) -> Optional[TTSAudioResult]:
        payload = {
            "text": text,
            "voice": cfg.voice_id,
            "speed": cfg.speed,
            "language": "vi",
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=15.0) as resp:
            audio_bytes = resp.read()

        # Parse duration from WAV header if WAV format
        duration = 0.0
        try:
            with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                duration = frames / float(rate)
        except Exception:
            # Fallback tính duration dựa trên tốc độ đọc tiếng Việt
            words = text.split()
            duration = max(1.0, round(len(words) / (2.7 * cfg.speed), 3))

        timing = TimingEstimator.estimate(text=text, total_duration=duration)

        return TTSAudioResult(
            audio_bytes=audio_bytes,
            duration=duration,
            format="wav",
            sample_rate=24000,
            timing=timing,
            voice_config=cfg,
        )

    async def get_duration(
        self,
        text: str,
        voice_config: Optional[VoiceConfig] = None,
    ) -> float:
        cfg = voice_config or VoiceConfig(voice_id="vi-VN-HoaiMyNeural", language="vi-VN", speed=1.0)
        words = text.split()
        return max(1.0, round(len(words) / (2.7 * cfg.speed), 3))

    async def get_timing(
        self,
        text: str,
        voice_config: Optional[VoiceConfig] = None,
    ) -> NarrationTiming:
        """Lấy thông tin timing phân đoạn từ Fallback Provider (EdgeTTS) hoặc TimingEstimator."""
        cfg = voice_config or VoiceConfig(voice_id="vi-VN-HoaiMyNeural", language="vi-VN", speed=1.0)
        if self.fallback_provider:
            try:
                return await self.fallback_provider.get_timing(text, cfg)
            except Exception as e:
                logger.warning(f"[LocalTTSProvider] get_timing fallback error: {e}")
        duration = await self.get_duration(text, cfg)
        return TimingEstimator.estimate(text=text, total_duration=duration)

    async def preview(
        self,
        text: str,
        voice_config: Optional[VoiceConfig] = None,
    ) -> TTSAudioResult:
        """Sinh đoạn âm thanh nghe thử ngắn (câu đầu tiên hoặc tối đa 3 giây)."""
        cfg = voice_config or VoiceConfig(voice_id="vi-VN-HoaiMyNeural", language="vi-VN", speed=1.0)
        if self.fallback_provider:
            try:
                return await self.fallback_provider.preview(text, cfg)
            except Exception as e:
                logger.warning(f"[LocalTTSProvider] preview fallback error: {e}")
        return await self.generate(text, cfg)
