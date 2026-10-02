from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional
from core.schemas.tts import NarrationTiming, TTSAudioResult, VoiceConfig


class TTSError(Exception):
    """Lỗi nền tảng của hệ thống Text-to-Speech."""
    pass


class InvalidVoiceError(TTSError):
    """Lỗi khi voiceId không hợp lệ hoặc không được hỗ trợ bởi provider."""
    pass


class TTSConnectionError(TTSError):
    """Lỗi mất kết nối mạng hoặc timeout tới dịch vụ TTS."""
    pass


class TTSSynthesisError(TTSError):
    """Lỗi trong quá trình tổng hợp âm thanh."""
    pass


from core.providers.base import TTSProvider as LegacyTTSProvider


class TTSProvider(LegacyTTSProvider, ABC):
    """
    Giao diện trừu tượng chuẩn (Interface) cho Text-to-Speech Provider.
    Tuân thủ nguyên tắc không hard-code provider, cho phép cắm ghép Mock, EdgeTTS, ElevenLabs, v.v.
    """

    @abstractmethod
    async def generate(
        self,
        text: str,
        voice_config: Optional[VoiceConfig] = None,
    ) -> TTSAudioResult:
        """
        Tổng hợp toàn diện âm thanh cho văn bản.
        Trả về TTSAudioResult gồm:
        - audio bytes/file
        - duration (giây)
        - metadata
        - timing (word timing nếu hỗ trợ, hoặc fallback rõ ràng)
        """
        pass

    @abstractmethod
    async def get_duration(
        self,
        text: str,
        voice_config: Optional[VoiceConfig] = None,
    ) -> float:
        """Lấy thời lượng phát âm (giây) của văn bản tương ứng với cấu hình giọng/tốc độ."""
        pass

    @abstractmethod
    async def get_timing(
        self,
        text: str,
        voice_config: Optional[VoiceConfig] = None,
    ) -> NarrationTiming:
        """
        Lấy thông tin timing (ưu tiên word timing hoặc phoneme timing).
        Nếu không hỗ trợ word timing, phải trả về fallback được đánh dấu rõ ràng.
        """
        pass

    @abstractmethod
    async def preview(
        self,
        text: str,
        voice_config: Optional[VoiceConfig] = None,
    ) -> TTSAudioResult:
        """
        Sinh bản nghe thử (preview) nhanh chóng (ví dụ chỉ đọc câu đầu hoặc giới hạn 3 giây).
        """
        pass

    @abstractmethod
    def get_supported_voices(self) -> List[str]:
        """Trả về danh sách các voice ID được hỗ trợ bởi provider này."""
        pass

    async def synthesize_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        language: str = "vi-VN",
        speed: float = 1.0,
    ):
        """Phương thức tương thích ngược với Phase 02 (core/providers/base.py)."""
        from core.providers.base import AudioSynthesisResult

        cfg = VoiceConfig(
            voice_id=voice_id or "default",
            language=language,
            speed=speed,
        )
        res = await self.generate(text, cfg)
        return AudioSynthesisResult(
            audio_bytes=res.audio_bytes,
            format=res.format,
            duration_ms=res.duration_ms,
            sample_rate=res.sample_rate,
        )
