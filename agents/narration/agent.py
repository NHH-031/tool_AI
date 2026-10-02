from __future__ import annotations

from typing import List, Optional
from ..base import AgentContext, AgentResult, BaseProductionAgent
from core.providers.base import TTSProvider
from core.schemas.audio import NarrationSegment
from core.schemas.tts import TTSAudioResult, VoiceConfig


class NarrationAgent(BaseProductionAgent):
    """Agent phụ trách tạo giọng lồng tiếng (Voiceover) và đo lường thời lượng audio chính xác."""

    def __init__(self, tts: TTSProvider, default_voice_config: Optional[VoiceConfig] = None):
        super().__init__(name="NarrationAgent")
        self.tts = tts
        self.default_voice_config = default_voice_config or VoiceConfig(
            voice_id="vi-VN-HoaiMyNeural",
            language="vi-VN",
            speed=1.0,
            pitch=0.0,
        )

    async def run(self, context: AgentContext) -> AgentResult:
        """
        Xử lý kịch bản thoại từ context, tổng hợp audio từng segment và tính toán timing chính xác.
        """
        # Trích xuất dữ liệu từ shared_state hoặc data
        state = context.shared_state if hasattr(context, "shared_state") else getattr(context, "data", {})
        segments_data = state.get("segments") or []
        script_text = state.get("script") or state.get("text") or getattr(context, "prompt", "")
        voice_cfg_dict = state.get("voice_config") or {}
        
        cfg = VoiceConfig(**voice_cfg_dict) if voice_cfg_dict else self.default_voice_config

        if not segments_data and script_text:
            segments_data = [{"text": script_text, "id": "seg_1"}]

        if not segments_data:
            return AgentResult(
                success=True,
                data={
                    "status": "idle",
                    "agent": self.name,
                    "narration_segments": [],
                    "total_duration_sec": 0.0,
                },
            )

        narration_segments: List[NarrationSegment] = []
        audio_results: List[TTSAudioResult] = []
        current_time_ms = 0

        for idx, seg in enumerate(segments_data, start=1):
            text = seg.get("text") if isinstance(seg, dict) else str(seg)
            seg_id = seg.get("id", f"seg_{idx}") if isinstance(seg, dict) else f"seg_{idx}"

            # Gọi TTS Provider
            if hasattr(self.tts, "generate"):
                tts_res: TTSAudioResult = await self.tts.generate(text, cfg)
            else:
                legacy_res = await self.tts.synthesize_speech(
                    text=text,
                    voice_id=cfg.voice_id,
                    language=cfg.language,
                    speed=cfg.speed,
                )
                tts_res = TTSAudioResult(
                    audio_bytes=legacy_res.audio_bytes,
                    duration=legacy_res.duration_ms / 1000.0,
                    duration_ms=legacy_res.duration_ms,
                    format=legacy_res.format,
                    sample_rate=legacy_res.sample_rate,
                    voice_config=cfg,
                )

            duration_ms = tts_res.duration_ms
            narration_seg = NarrationSegment(
                id=seg_id,
                text=text,
                cue_index=idx,
                start_ms=current_time_ms,
                end_ms=current_time_ms + duration_ms,
                duration_ms=duration_ms,
                voice_id=cfg.voice_id,
            )
            narration_segments.append(narration_seg)
            audio_results.append(tts_res)
            current_time_ms += duration_ms

        return AgentResult(
            success=True,
            data={
                "status": "completed",
                "agent": self.name,
                "narration_segments": [s.model_dump() for s in narration_segments],
                "total_duration_sec": round(current_time_ms / 1000.0, 3),
                "total_duration_ms": current_time_ms,
                "voice_config": cfg.model_dump(),
                "segment_count": len(narration_segments),
            },
        )
