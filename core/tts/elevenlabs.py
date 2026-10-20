from __future__ import annotations

import asyncio
import io
import logging
import os
from typing import Dict, List, Optional
import httpx

from core.schemas.tts import NarrationTiming, TTSAudioResult, VoiceConfig
from .base import TTSProvider, TTSSynthesisError
from .timing import TimingEstimator

logger = logging.getLogger(__name__)

# Ánh xạ các định danh giọng đọc biểu cảm của ElevenLabs sang Voice ID chính thức
ELEVENLABS_VOICE_MAP: Dict[str, str] = {
    "eleven-adam": "pNInz6obpgDQGcFmaJgB",      # Adam - Trầm ấm, dẫn chuyện cuốn hút
    "eleven-rachel": "21m00Tcm4TlvDq8ikWAM",    # Rachel - Giọng nữ dịu dàng, tự nhiên
    "eleven-antoni": "ErXwobaYiN019PkySvjV",    # Antoni - Nam chững chạc, chuyên nghiệp
    "eleven-bella": "EXAVITQu4vr4xnSDxMaL",     # Bella - Nữ trẻ trung, sinh động
    "eleven-josh": "TxGEqnHWrfWFTfGW9XjX",      # Josh - Nam tự nhiên, phong thái chia sẻ
    "eleven-sam": "yoZ06aMxZJJ28mfd3POQ",       # Sam - Nam sôi động, thuyết phục
}


class ElevenLabsTTSProvider(TTSProvider):
    """
    Nhà cung cấp giọng đọc biểu cảm cao cấp ElevenLabs (Task 8.4).
    Hỗ trợ mô hình eleven_multilingual_v2 với độ chân thực và cảm xúc cao nhất hiện nay.
    Tự động chuyển tiếp (fallback) sang Local/EdgeTTS nếu không có API key hoặc lỗi mạng.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_id: str = "eleven_multilingual_v2",
        fallback_provider: Optional[TTSProvider] = None,
    ):
        self.api_key = api_key if api_key is not None else os.getenv("ELEVENLABS_API_KEY", "").strip()
        self.model_id = model_id
        self._fallback_provider = fallback_provider
        self.base_url = "https://api.elevenlabs.io/v1"


    @property
    def fallback_provider(self) -> TTSProvider:
        if self._fallback_provider is None:
            from core.tts.local import LocalTTSProvider
            self._fallback_provider = LocalTTSProvider()
        return self._fallback_provider

    def get_supported_voices(self) -> List[str]:
        return list(ELEVENLABS_VOICE_MAP.keys())

    def _resolve_voice_id(self, voice_id: str) -> str:
        """Chuyển đổi id nội bộ hoặc alias sang ElevenLabs voice ID."""
        return ELEVENLABS_VOICE_MAP.get(voice_id, voice_id)

    async def generate(
        self,
        text: str,
        voice_config: Optional[VoiceConfig] = None,
    ) -> TTSAudioResult:
        cfg = voice_config or VoiceConfig(voice_id="eleven-rachel", language="vi-VN", speed=1.0)
        
        # Nếu chưa cấu hình API key, tự động fallback an toàn
        if not self.api_key:
            logger.info(
                f"[ElevenLabsTTSProvider] ELEVENLABS_API_KEY chưa được thiết lập. "
                f"Tự động chuyển tiếp sang {type(self.fallback_provider).__name__}."
            )
            return await self.fallback_provider.generate(text, cfg)

        eleven_voice_id = self._resolve_voice_id(cfg.voice_id)
        url = f"{self.base_url}/text-to-speech/{eleven_voice_id}"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key,
        }

        # Cấu hình kiểm soát cảm xúc và độ ổn định giọng nói
        payload = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": 0.50,
                "similarity_boost": 0.75,
                "style": 0.35,
                "use_speaker_boost": True,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code != 200:
                    err_msg = f"ElevenLabs API trả về mã lỗi {resp.status_code}: {resp.text}"
                    logger.warning(f"[ElevenLabsTTSProvider] {err_msg}. Chuyển sang fallback...")
                    return await self.fallback_provider.generate(text, cfg)

                audio_bytes = resp.content

            # Xác định thời lượng bằng pyav hoặc estimation
            duration = self._calculate_audio_duration(audio_bytes, text, cfg.speed)
            timing = TimingEstimator.estimate(text=text, total_duration=duration)

            logger.info(
                f"[ElevenLabsTTSProvider] Tổng hợp giọng biểu cảm thành công: "
                f"{len(audio_bytes)} bytes, ~{duration:.2f}s (voice: {cfg.voice_id})"
            )

            return TTSAudioResult(
                audio_bytes=audio_bytes,
                duration=duration,
                duration_ms=int(round(duration * 1000)),
                format="mp3",
                sample_rate=44100,
                timing=timing,
                voice_config=cfg,
            )

        except Exception as e:
            logger.warning(
                f"[ElevenLabsTTSProvider] Lỗi kết nối tới ElevenLabs: {e}. "
                f"Tự động chuyển tiếp an toàn sang {type(self.fallback_provider).__name__}."
            )
            return await self.fallback_provider.generate(text, cfg)

    def _calculate_audio_duration(self, audio_bytes: bytes, text: str, speed: float) -> float:
        """Đo thời lượng file audio trả về từ ElevenLabs."""
        import wave
        try:
            with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
                return float(wf.getnframes()) / wf.getframerate()
        except Exception:
            pass

        # Fallback ước tính theo số từ
        words = text.split()
        return max(1.0, round(len(words) / (2.6 * max(0.5, speed)), 2))


    async def get_duration(
        self,
        text: str,
        voice_config: Optional[VoiceConfig] = None,
    ) -> float:
        cfg = voice_config or VoiceConfig(voice_id="eleven-rachel", language="vi-VN", speed=1.0)
        words = text.split()
        return max(1.0, round(len(words) / (2.6 * max(0.5, cfg.speed)), 2))

    async def get_timing(
        self,
        text: str,
        voice_config: Optional[VoiceConfig] = None,
    ) -> NarrationTiming:
        cfg = voice_config or VoiceConfig(voice_id="eleven-rachel", language="vi-VN", speed=1.0)
        dur = await self.get_duration(text, cfg)
        return TimingEstimator.estimate(text=text, total_duration=dur)

    async def preview(
        self,
        text: str,
        voice_config: Optional[VoiceConfig] = None,
    ) -> TTSAudioResult:
        preview_text = text.split(".")[0] if "." in text else text
        if len(preview_text) > 80:
            preview_text = preview_text[:80] + "..."
        return await self.generate(preview_text, voice_config)
