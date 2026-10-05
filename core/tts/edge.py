from __future__ import annotations

import asyncio
from typing import List, Optional
from core.schemas.tts import NarrationTiming, SentenceTiming, TTSAudioResult, VoiceConfig, WordTiming
from .base import InvalidVoiceError, TTSConnectionError, TTSProvider, TTSSynthesisError
from .timing import TimingEstimator


class EdgeTTSProvider(TTSProvider):
    """
    Microsoft Edge Online Neural TTS Provider.
    Hỗ trợ miễn phí chất lượng studio cao:
    - Tiếng Việt: vi-VN-HoaiMyNeural (Nữ), vi-VN-NamMinhNeural (Nam)
    - Tiếng Anh: en-US-AriaNeural, en-US-GuyNeural, en-US-JennyNeural, v.v.
    - Trích xuất native WordBoundary events từ giao thức WebSocket trực tiếp.
    """

    SUPPORTED_VOICES = [
        "vi-VN-HoaiMyNeural",
        "vi-VN-NamMinhNeural",
        "en-US-AriaNeural",
        "en-US-GuyNeural",
        "en-US-JennyNeural",
        "en-GB-SoniaNeural",
    ]

    def __init__(self, default_voice: str = "vi-VN-HoaiMyNeural"):
        self.default_voice = default_voice

    def get_supported_voices(self) -> List[str]:
        return list(self.SUPPORTED_VOICES)

    def _validate_voice(self, voice_config: VoiceConfig) -> None:
        LEGACY_VOICE_MAP = {
            "vi-VN-Standard-A": "vi-VN-HoaiMyNeural",
            "vi-VN-Standard-B": "vi-VN-NamMinhNeural",
            "vi-VN-Standard-C": "vi-VN-HoaiMyNeural",
            "vi-VN-Standard-D": "vi-VN-NamMinhNeural",
            "vi-VN-Wavenet-A": "vi-VN-HoaiMyNeural",
            "vi-VN-Wavenet-B": "vi-VN-NamMinhNeural",
            "vi-VN-Wavenet-C": "vi-VN-HoaiMyNeural",
            "vi-VN-Wavenet-D": "vi-VN-NamMinhNeural",
            "vi-VN-Neural2-A": "vi-VN-HoaiMyNeural",
        }
        if voice_config.voice_id in LEGACY_VOICE_MAP:
            voice_config.voice_id = LEGACY_VOICE_MAP[voice_config.voice_id]
        elif voice_config.voice_id not in self.SUPPORTED_VOICES:
            if not voice_config.voice_id.endswith("Neural"):
                voice_config.voice_id = self.default_voice

    def _format_rate(self, speed: float) -> str:
        diff_pct = int(round((speed - 1.0) * 100))
        if diff_pct >= 0:
            return f"+{diff_pct}%"
        return f"{diff_pct}%"

    def _format_pitch(self, pitch: float) -> str:
        pitch_hz = int(round(pitch))
        if pitch_hz >= 0:
            return f"+{pitch_hz}Hz"
        return f"{pitch_hz}Hz"

    async def generate(
        self,
        text: str,
        voice_config: Optional[VoiceConfig] = None,
    ) -> TTSAudioResult:
        try:
            import edge_tts
        except ImportError:
            raise TTSSynthesisError("Package 'edge-tts' chưa được cài đặt trong môi trường.")

        cfg = voice_config or VoiceConfig(voice_id=self.default_voice)
        self._validate_voice(cfg)

        clean_text = text.strip()
        if not clean_text:
            raise TTSSynthesisError("Văn bản cần đọc không được để trống.")

        rate_str = self._format_rate(cfg.speed)
        pitch_str = self._format_pitch(cfg.pitch)

        communicate = edge_tts.Communicate(
            text=clean_text,
            voice=cfg.voice_id,
            rate=rate_str,
            pitch=pitch_str,
        )

        audio_chunks = bytearray()
        raw_word_events = []

        try:
            async for chunk in communicate.stream():
                chunk_type = chunk.get("type")
                if chunk_type == "audio":
                    audio_chunks.extend(chunk.get("data", b""))
                elif chunk_type == "WordBoundary":
                    # offset & duration tính bằng đơn vị 100 nano-giây (10^-7 giây)
                    offset_sec = chunk["offset"] / 10_000_000.0
                    duration_sec = chunk["duration"] / 10_000_000.0
                    word = chunk["text"]
                    raw_word_events.append({
                        "word": word,
                        "start_time": offset_sec,
                        "end_time": offset_sec + duration_sec,
                        "duration": duration_sec,
                    })
        except Exception as exc:
            raise TTSConnectionError(f"Lỗi kết nối khi gọi Edge TTS: {str(exc)}") from exc

        if not audio_chunks:
            raise TTSSynthesisError("Edge TTS không trả về bất kỳ dữ liệu âm thanh nào.")

        # Xây dựng timing
        words_timing: List[WordTiming] = []
        for ev in raw_word_events:
            words_timing.append(
                WordTiming(
                    word=ev["word"],
                    start_time=round(ev["start_time"], 3),
                    end_time=round(ev["end_time"], 3),
                    duration=round(ev["duration"], 3),
                    confidence=0.98,
                )
            )

        # Tính tổng duration từ audio hoặc từ word cuối cùng
        if words_timing:
            total_duration = round(words_timing[-1].end_time + 0.1, 3)
            sentence_timing = SentenceTiming(
                sentence=clean_text,
                start_time=words_timing[0].start_time,
                end_time=words_timing[-1].end_time,
                duration=total_duration,
                words=words_timing,
            )
            timing = NarrationTiming(
                text=clean_text,
                duration=total_duration,
                timing_level="word",
                is_fallback=False,
                fallback_reason=None,
                words=words_timing,
                sentences=[sentence_timing],
            )
        else:
            # Fallback nếu stream không trả WordBoundary
            # Ước lượng tạm thời 15 ký tự/giây
            estimated_dur = max(0.5, len(clean_text) / (14.0 * cfg.speed))
            timing = TimingEstimator.estimate_timing(
                text=clean_text,
                total_duration=estimated_dur,
                timing_level="fallback_estimated",
                fallback_reason="EdgeTTS stream did not return native WordBoundary events.",
            )
            total_duration = timing.duration

        return TTSAudioResult(
            audio_bytes=bytes(audio_chunks),
            duration=total_duration,
            duration_ms=int(total_duration * 1000),
            format="mp3",  # Edge TTS stream mặc định sinh MP3
            sample_rate=24000,
            channels=1,
            voice_config=cfg,
            timing=timing,
            metadata={
                "provider": "EdgeTTSProvider",
                "voice_id": cfg.voice_id,
                "speed": cfg.speed,
                "pitch": cfg.pitch,
                "has_native_word_boundaries": len(words_timing) > 0,
            },
        )

    async def get_duration(
        self,
        text: str,
        voice_config: Optional[VoiceConfig] = None,
    ) -> float:
        # Nếu chỉ cần đo duration, gọi generate và lấy duration chuẩn
        res = await self.generate(text, voice_config)
        return res.duration

    async def get_timing(
        self,
        text: str,
        voice_config: Optional[VoiceConfig] = None,
    ) -> NarrationTiming:
        res = await self.generate(text, voice_config)
        return res.timing or TimingEstimator.estimate_timing(
            text, res.duration, fallback_reason="No timing returned from EdgeTTS"
        )

    async def preview(
        self,
        text: str,
        voice_config: Optional[VoiceConfig] = None,
    ) -> TTSAudioResult:
        first_sentence = text.strip().split(".")[0] + "." if "." in text else text[:60]
        return await self.generate(first_sentence, voice_config)
