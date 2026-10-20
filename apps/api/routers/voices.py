from __future__ import annotations

from typing import List
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/voices", tags=["Voices"])


class VoiceItem(BaseModel):
    id: str
    name: str
    language: str
    locale: str
    gender: str
    accent: str
    sample_text: str
    supported_speeds: List[float] = Field(default_factory=lambda: [0.8, 1.0, 1.2, 1.5])
    is_neural: bool = True
    tags: List[str] = Field(default_factory=list)


VOICES_CATALOG: List[VoiceItem] = [
    VoiceItem(
        id="vi-VN-Standard-A",
        name="Mai Chi",
        language="Tiếng Việt",
        locale="vi-VN",
        gender="female",
        accent="Bắc Bộ (Truyền Cảm)",
        sample_text="Xin chào các bạn, hôm nay chúng ta sẽ cùng khám phá thế giới tự nhiên kỳ thú.",
        tags=["natural", "storytelling", "vietnamese", "female"],
    ),
    VoiceItem(
        id="vi-VN-Standard-B",
        name="Nam Khánh",
        language="Tiếng Việt",
        locale="vi-VN",
        gender="male",
        accent="Bắc Bộ (Trầm Ấm)",
        sample_text="Con khỉ đang trèo lên cây để lấy một quả chuối.",
        tags=["warm", "explainer", "vietnamese", "male"],
    ),
    VoiceItem(
        id="vi-VN-Neural-C",
        name="Thảo My",
        language="Tiếng Việt",
        locale="vi-VN",
        gender="female",
        accent="Nam Bộ (Ngọt Ngào)",
        sample_text="Chào bạn! Hãy cùng tôi tìm hiểu bài học thú vị ngày hôm nay nhé.",
        tags=["friendly", "educational", "vietnamese", "female"],
    ),
    VoiceItem(
        id="en-US-Standard-A",
        name="Arthur",
        language="English",
        locale="en-US",
        gender="male",
        accent="American (Professional)",
        sample_text="Welcome to AI Whiteboard Studio, turning your ideas into hand-drawn stories.",
        tags=["authoritative", "corporate", "english", "male"],
    ),
    VoiceItem(
        id="en-US-Standard-B",
        name="Elena",
        language="English",
        locale="en-US",
        gender="female",
        accent="American (Lively)",
        sample_text="Watch as complex ideas unfold through real-time dynamic hand drawings.",
        tags=["expressive", "youtube", "english", "female"],
    ),
    VoiceItem(
        id="vieneu-local-1",
        name="VieNeu AI (Local · Bắc Bộ)",
        language="Tiếng Việt",
        locale="vi-VN",
        gender="male",
        accent="Bắc Bộ Tự Nhiên",
        sample_text="Xin chào các bạn, đây là giọng đọc AI VieNeu thế hệ mới.",
        tags=["local", "vieneu", "vietnamese", "male"],
    ),
    VoiceItem(
        id="voicestudio-local-1",
        name="VoiceStudio (Local · Nam Bộ)",
        language="Tiếng Việt",
        locale="vi-VN",
        gender="female",
        accent="Nam Bộ Ngọt Ngào",
        sample_text="Chào mừng bạn đến với kênh kiến thức và giải trí.",
        tags=["local", "voicestudio", "vietnamese", "female"],
    ),
]


class SynthesizeVoiceRequest(BaseModel):
    scene_id: str
    scene_index: int
    text: str = Field(min_length=1)
    voice_id: str = "vi-VN-Standard-B"
    speed: float = 1.0
    project_id: str = "default"


class SynthesizeVoiceResponse(BaseModel):
    scene_id: str
    scene_index: int
    audio_url: str
    duration_sec: float
    voice_id: str
    status: str = "completed"


@router.get("", response_model=List[VoiceItem])
async def list_voices() -> List[VoiceItem]:
    """Trả về danh mục giọng đọc TTS khả dụng."""
    return VOICES_CATALOG


@router.post("/synthesize", response_model=SynthesizeVoiceResponse)
async def synthesize_voice(req: SynthesizeVoiceRequest) -> SynthesizeVoiceResponse:
    """Tổng hợp giọng đọc cho một phân cảnh cụ thể qua LocalTTSProvider / EdgeTTS."""
    from pathlib import Path
    from fastapi import HTTPException
    from core.schemas.tts import VoiceConfig
    from core.tts.local import LocalTTSProvider

    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Nội dung lời thoại không được để trống")

    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
    out_dir = PROJECT_ROOT / "output" / "storyboard" / req.project_id
    out_dir.mkdir(parents=True, exist_ok=True)

    tts_provider = LocalTTSProvider()
    cfg = VoiceConfig(
        voice_id=req.voice_id or "vi-VN-HoaiMyNeural",
        language="vi-VN",
        speed=req.speed or 1.0,
    )

    try:
        result = await tts_provider.generate(text=req.text, voice_config=cfg)
        ext = result.format if getattr(result, "format", None) else "mp3"
        out_audio = out_dir / f"scene_{req.scene_index}_audio.{ext}"
        out_audio.write_bytes(result.audio_bytes)

        # Lưu thêm bản wav nếu là mp3 để đảm bảo tương thích ngược với mọi module
        legacy_wav = out_dir / f"scene_{req.scene_index}_audio.wav"
        if legacy_wav != out_audio:
            legacy_wav.write_bytes(result.audio_bytes)

        # Lưu metadata timing (WordBoundary / Sentence) phục vụ sinh phụ đề SRT / Karaoke
        if getattr(result, "timing", None):
            try:
                import json
                timing_file = out_dir / f"scene_{req.scene_index}_timing.json"
                timing_file.write_text(
                    json.dumps(result.timing.model_dump(), ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            except Exception as e_timing:
                logger.warning(f"[synthesize_voice] Không thể lưu timing file: {e_timing}")

        rel_url = f"/media/storyboard/{req.project_id}/{out_audio.name}"
        return SynthesizeVoiceResponse(
            scene_id=req.scene_id,
            scene_index=req.scene_index,
            audio_url=rel_url,
            duration_sec=round(result.duration, 2),
            voice_id=req.voice_id,
            status="completed",
        )
    except Exception as e:
        logger.error(f"[synthesize_voice] Lỗi khi tạo giọng đọc cảnh {req.scene_index}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi thu âm giọng đọc: {str(e)}"
        )
