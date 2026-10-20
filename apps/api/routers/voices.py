from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

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
        id="vi-VN-HoaiMyNeural",
        name="Hoài My (Edge TTS · Nữ Bắc Bộ)",
        language="Tiếng Việt",
        locale="vi-VN",
        gender="female",
        accent="Bắc Bộ (Truyền Cảm, Rõ Ràng)",
        sample_text="Xin chào các bạn, hôm nay chúng ta sẽ cùng khám phá thế giới tự nhiên kỳ thú.",
        tags=["natural", "storytelling", "vietnamese", "female", "edgetts"],
    ),
    VoiceItem(
        id="vi-VN-NamMinhNeural",
        name="Nam Minh (Edge TTS · Nam Bắc Bộ)",
        language="Tiếng Việt",
        locale="vi-VN",
        gender="male",
        accent="Bắc Bộ (Trầm Ấm, Đĩnh Đạc)",
        sample_text="Con khỉ đang trèo lên cây để lấy một quả chuối.",
        tags=["warm", "explainer", "vietnamese", "male", "edgetts"],
    ),
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
    # Giọng biểu cảm cao cấp ElevenLabs (Task 8.4)
    VoiceItem(
        id="eleven-rachel",
        name="Rachel (ElevenLabs · Biểu Cảm Cao Cấp)",
        language="Đa ngôn ngữ",
        locale="vi-VN / en-US",
        gender="female",
        accent="Dịu Dàng, Dẫn Chuyện Cuốn Hút",
        sample_text="Chào mừng bạn đến với AI Whiteboard Studio, biến ý tưởng thành tranh vẽ tay sống động.",
        tags=["elevenlabs", "expressive", "storytelling", "female"],
    ),
    VoiceItem(
        id="eleven-adam",
        name="Adam (ElevenLabs · Biểu Cảm Cao Cấp)",
        language="Đa ngôn ngữ",
        locale="vi-VN / en-US",
        gender="male",
        accent="Trầm Ấm, Uy Lực, Điện Ảnh",
        sample_text="Hãy cùng theo dõi những bước ngoặt quan trọng trong dự án này.",
        tags=["elevenlabs", "expressive", "cinematic", "male"],
    ),
    VoiceItem(
        id="eleven-antoni",
        name="Antoni (ElevenLabs · Biểu Cảm Cao Cấp)",
        language="Đa ngôn ngữ",
        locale="vi-VN / en-US",
        gender="male",
        accent="Chuyên Nghiệp, Thuyết Trình",
        sample_text="Giải pháp tối ưu hóa quy trình kinh doanh và gia tăng doanh số bền vững.",
        tags=["elevenlabs", "expressive", "professional", "male"],
    ),
    VoiceItem(
        id="eleven-bella",
        name="Bella (ElevenLabs · Biểu Cảm Cao Cấp)",
        language="Đa ngôn ngữ",
        locale="vi-VN / en-US",
        gender="female",
        accent="Tươi Vui, Trẻ Trung, Sinh Động",
        sample_text="Thật tuyệt vời khi được đồng hành cùng các bạn trong bài giảng ngày hôm nay!",
        tags=["elevenlabs", "expressive", "lively", "female"],
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


class UploadCustomAudioRequest(BaseModel):
    project_id: str = "default"
    scene_id: str
    scene_index: int
    audio_data_base64: str
    filename: Optional[str] = "custom_voice.wav"
    text: Optional[str] = None


@router.get("", response_model=List[VoiceItem])
async def list_voices() -> List[VoiceItem]:
    """Trả về danh mục giọng đọc TTS khả dụng."""
    return VOICES_CATALOG


@router.post("/synthesize", response_model=SynthesizeVoiceResponse)
async def synthesize_voice(req: SynthesizeVoiceRequest) -> SynthesizeVoiceResponse:
    """Tổng hợp giọng đọc cho một phân cảnh cụ thể qua LocalTTS / ElevenLabs / EdgeTTS."""
    from core.schemas.tts import VoiceConfig

    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Nội dung lời thoại không được để trống")

    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
    out_dir = PROJECT_ROOT / "output" / "storyboard" / req.project_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # Chọn provider tương ứng với voice_id
    voice_id = req.voice_id or "vi-VN-HoaiMyNeural"
    if voice_id.startswith("eleven-"):
        from core.tts.elevenlabs import ElevenLabsTTSProvider
        tts_provider = ElevenLabsTTSProvider()
    else:
        from core.tts.local import LocalTTSProvider
        tts_provider = LocalTTSProvider()

    cfg = VoiceConfig(
        voice_id=voice_id,
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


@router.post("/upload-custom-audio", response_model=SynthesizeVoiceResponse)
async def upload_custom_audio(req: UploadCustomAudioRequest) -> SynthesizeVoiceResponse:
    """
    Tải lên file thu âm thật hoặc audio ghi âm trực tiếp từ trình duyệt qua Micro (Task 8.2).
    Chuyển đổi và chuẩn hóa thành file âm thanh phân cảnh kèm tính toán thời lượng chính xác.
    """
    from core.audio.mixer import AudioMixer
    from core.tts.timing import TimingEstimator
    import json

    if not req.audio_data_base64:
        raise HTTPException(status_code=400, detail="Dữ liệu âm thanh không được để trống")

    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
    out_dir = PROJECT_ROOT / "output" / "storyboard" / req.project_id
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Tách header base64 nếu có (data:audio/...;base64,xxxx)
        data_str = req.audio_data_base64
        if "," in data_str:
            data_str = data_str.split(",", 1)[1]

        raw_bytes = base64.b64decode(data_str)
        if len(raw_bytes) < 32:
            raise HTTPException(status_code=400, detail="File âm thanh không hợp lệ hoặc dung lượng quá nhỏ")

        # Lưu tạm file raw
        temp_input = out_dir / f"scene_{req.scene_index}_temp_upload.bin"
        temp_input.write_bytes(raw_bytes)

        # Đọc và chuẩn hóa qua AudioMixer (PyAV giải mã được WebM, WAV, MP3, OGG, AAC, v.v.)
        mixer = AudioMixer()
        audio_arr, _ = mixer.read_audio(temp_input)
        duration_sec = audio_arr.shape[1] / float(mixer.sample_rate)

        # Lưu file WAV và MP3 chuẩn hóa
        out_wav = out_dir / f"scene_{req.scene_index}_audio.wav"
        mixer.write_audio(audio_arr, out_wav, codec="pcm_s16le")

        out_mp3 = out_dir / f"scene_{req.scene_index}_audio.mp3"
        mixer.write_audio(audio_arr, out_mp3, codec="libmp3lame")

        # Dọn dẹp file tạm
        try:
            temp_input.unlink(missing_ok=True)
        except Exception:
            pass

        # Tạo metadata timing phân cảnh
        text_content = req.text or f"Phân cảnh {req.scene_index}"
        timing = TimingEstimator.estimate(text=text_content, total_duration=duration_sec)
        timing_file = out_dir / f"scene_{req.scene_index}_timing.json"
        timing_file.write_text(
            json.dumps(timing.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        rel_url = f"/media/storyboard/{req.project_id}/scene_{req.scene_index}_audio.mp3"
        logger.info(
            f"[upload_custom_audio] Đã tải lên và chuẩn hóa audio cá nhân cho cảnh {req.scene_index}: "
            f"duration={duration_sec:.2f}s, url={rel_url}"
        )

        return SynthesizeVoiceResponse(
            scene_id=req.scene_id,
            scene_index=req.scene_index,
            audio_url=rel_url,
            duration_sec=round(duration_sec, 2),
            voice_id="custom_upload",
            status="completed",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[upload_custom_audio] Lỗi xử lý file âm thanh: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Lỗi phân tích file âm thanh: {str(e)}")

