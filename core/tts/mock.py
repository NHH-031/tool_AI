from __future__ import annotations

import io
import math
import struct
import wave
from typing import List, Optional
from core.schemas.tts import NarrationTiming, SentenceTiming, TTSAudioResult, VoiceConfig, WordTiming
from .base import InvalidVoiceError, TTSConnectionError, TTSProvider
from .timing import TimingEstimator


class MockTTSProvider(TTSProvider):
    """
    Mock TTS Provider phục vụ kiểm thử tự động deterministic và cô lập (không cần mạng/API).
    Hỗ trợ:
    - Sinh file WAV chuẩn PCM playable thực tế
    - Tùy biến hỗ trợ word-level timing hoặc giả lập provider thiếu word timing (kích hoạt fallback)
    - Mô phỏng lỗi kết nối / lỗi tổng hợp theo số lần (fail_times) để test retry
    - Kiểm tra tính hợp lệ của voiceId
    - Điều chỉnh tốc độ (speed) và cao độ (pitch)
    """

    DEFAULT_VOICES = [
        "vi-VN-Standard-A",
        "vi-VN-Standard-B",
        "vi-VN-Neural-C",
        "en-US-Standard-A",
        "en-US-Standard-B",
        "vi-VN-HoaiMyNeural",
        "vi-VN-NamMinhNeural",
        "en-US-AriaNeural",
        "en-US-GuyNeural",
        "mock_voice_1",
        "mock_voice_2",
        "default",
    ]

    def __init__(
        self,
        char_per_sec: float = 14.0,
        supports_word_timing: bool = True,
        supported_voices: Optional[List[str]] = None,
        fail_times: int = 0,
        audio_format: str = "mp3",
    ):
        self.char_per_sec = char_per_sec
        self.supports_word_timing = supports_word_timing
        self.supported_voices = supported_voices if supported_voices is not None else list(self.DEFAULT_VOICES)
        self.fail_times = fail_times
        self.audio_format = audio_format

    def get_supported_voices(self) -> List[str]:
        return list(self.supported_voices)

    def _validate_voice(self, voice_config: VoiceConfig) -> None:
        if voice_config.voice_id not in self.supported_voices:
            raise InvalidVoiceError(
                f"Giọng đọc '{voice_config.voice_id}' không hợp lệ hoặc không được hỗ trợ bởi provider này. "
                f"Các giọng được hỗ trợ: {self.supported_voices}"
            )

    def _check_and_trigger_failure(self) -> None:
        if self.fail_times > 0:
            self.fail_times -= 1
            raise TTSConnectionError("Lỗi kết nối giả lập tới dịch vụ TTS (Simulated connection timeout)")

    def _calculate_duration(self, text: str, speed: float) -> float:
        clean_text = text.strip()
        if not clean_text:
            return 0.5
        effective_speed = max(0.25, speed)
        # Thời lượng tính theo số ký tự chia cho tốc độ đọc
        raw_sec = len(clean_text) / (self.char_per_sec * effective_speed)
        return max(0.5, round(raw_sec, 3))

    def _generate_synthetic_wav(self, duration_sec: float, pitch_offset: float = 0.0) -> bytes:
        """Sinh chuỗi bytes WAV PCM 16-bit mono 24kHz chứa sóng âm mô phỏng."""
        sample_rate = 24000
        num_samples = int(duration_sec * sample_rate)
        # Tần số cơ bản 220Hz (A3), điều chỉnh theo pitch
        base_freq = 220.0 * (2.0 ** (pitch_offset / 12.0))

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)

            # Sinh sóng sin nhẹ nhàng với envelope fade in / fade out để tránh tiếng click
            frames = bytearray()
            fade_samples = min(sample_rate // 20, num_samples // 4)  # 50ms fade

            for i in range(num_samples):
                t = i / sample_rate
                # Envelope
                envelope = 1.0
                if i < fade_samples:
                    envelope = i / fade_samples
                elif i > num_samples - fade_samples:
                    envelope = (num_samples - i) / fade_samples

                val = int(8000.0 * envelope * math.sin(2.0 * math.pi * base_freq * t))
                frames.extend(struct.pack("<h", max(-32768, min(32767, val))))

            wav_file.writeframes(frames)

        return buffer.getvalue()

    async def get_duration(
        self,
        text: str,
        voice_config: Optional[VoiceConfig] = None,
    ) -> float:
        self._check_and_trigger_failure()
        cfg = voice_config or VoiceConfig(voice_id="default")
        self._validate_voice(cfg)
        return self._calculate_duration(text, cfg.speed)

    async def get_timing(
        self,
        text: str,
        voice_config: Optional[VoiceConfig] = None,
    ) -> NarrationTiming:
        self._check_and_trigger_failure()
        cfg = voice_config or VoiceConfig(voice_id="default")
        self._validate_voice(cfg)

        total_duration = self._calculate_duration(text, cfg.speed)

        # Nếu provider cấu hình không hỗ trợ word timing -> gọi TimingEstimator để sinh fallback
        if not self.supports_word_timing:
            return TimingEstimator.estimate_timing(
                text=text,
                total_duration=total_duration,
                timing_level="fallback_estimated",
                fallback_reason="MockTTSProvider configured with supports_word_timing=False",
            )

        # Nếu hỗ trợ word timing -> sinh native word timing chính xác
        words = text.strip().split()
        if not words:
            return NarrationTiming(
                text=text,
                duration=total_duration,
                timing_level="word",
                is_fallback=False,
                words=[],
                sentences=[],
            )

        word_timings: List[WordTiming] = []
        time_per_word = total_duration / len(words)
        curr = 0.0

        for w in words:
            w_start = round(curr, 3)
            w_end = round(curr + time_per_word, 3)
            word_timings.append(
                WordTiming(
                    word=w,
                    start_time=w_start,
                    end_time=w_end,
                    duration=round(time_per_word, 3),
                    confidence=1.0,
                )
            )
            curr = w_end

        sentence_timing = SentenceTiming(
            sentence=text.strip(),
            start_time=0.0,
            end_time=total_duration,
            duration=total_duration,
            words=word_timings,
        )

        return NarrationTiming(
            text=text.strip(),
            duration=total_duration,
            timing_level="word",
            is_fallback=False,
            fallback_reason=None,
            words=word_timings,
            sentences=[sentence_timing],
        )

    async def generate(
        self,
        text: str,
        voice_config: Optional[VoiceConfig] = None,
    ) -> TTSAudioResult:
        self._check_and_trigger_failure()
        cfg = voice_config or VoiceConfig(voice_id="default")
        self._validate_voice(cfg)

        duration = self._calculate_duration(text, cfg.speed)
        audio_bytes = self._generate_synthetic_wav(duration, cfg.pitch)
        timing = await self.get_timing(text, cfg)

        return TTSAudioResult(
            audio_bytes=audio_bytes,
            duration=duration,
            duration_ms=int(duration * 1000),
            format=self.audio_format,
            sample_rate=24000,
            channels=1,
            voice_config=cfg,
            timing=timing,
            metadata={
                "provider": "MockTTSProvider",
                "char_count": len(text),
                "speed": cfg.speed,
                "pitch": cfg.pitch,
                "has_native_word_timing": self.supports_word_timing,
            },
        )

    async def preview(
        self,
        text: str,
        voice_config: Optional[VoiceConfig] = None,
    ) -> TTSAudioResult:
        """Sinh mẫu nghe thử (preview) ngắn giới hạn tối đa câu đầu hoặc 3 giây."""
        self._check_and_trigger_failure()
        cfg = voice_config or VoiceConfig(voice_id="default")
        self._validate_voice(cfg)

        # Lấy câu đầu tiên để preview nhanh
        first_sentence = text.strip().split(".")[0] + "." if "." in text else text[:60]
        result = await self.generate(first_sentence, cfg)
        result.metadata["preview_mode"] = True
        return result
