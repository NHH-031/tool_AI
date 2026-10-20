from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/music", tags=["Music"])
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class MusicTrackItem(BaseModel):
    id: str
    title: str
    artist: str
    mood: str
    genre: str
    duration_sec: int
    bpm: int
    recommended_volume: float = 0.15
    preview_url: str = ""
    tags: List[str] = Field(default_factory=list)


MUSIC_CATALOG: List[MusicTrackItem] = [
    MusicTrackItem(
        id="acoustic_uplift",
        title="Sunny Morning Ukulele",
        artist="Studio Acoustic Collective",
        mood="Tươi Sáng, Hứng Khởi",
        genre="Acoustic Folk",
        duration_sec=64,
        bpm=110,
        recommended_volume=0.15,
        preview_url="/music/acoustic_uplift/preview",
        tags=["cheerful", "acoustic", "storytelling", "bright"],
    ),
    MusicTrackItem(
        id="whimsical_play",
        title="Playful Forest Marimba",
        artist="Animation Soundworks",
        mood="Vui Nhộn, Tinh Nghịch",
        genre="Children Animation",
        duration_sec=64,
        bpm=124,
        recommended_volume=0.18,
        preview_url="/music/whimsical_play/preview",
        tags=["whimsical", "monkey", "cartoon", "playful"],
    ),
    MusicTrackItem(
        id="lofi_chill",
        title="Late Night Whiteboard Lofi",
        artist="Tokyo Chillhop Beats",
        mood="Thư Giãn, Tập Trung",
        genre="Lofi Hip Hop",
        duration_sec=64,
        bpm=85,
        recommended_volume=0.12,
        preview_url="/music/lofi_chill/preview",
        tags=["lofi", "study", "relaxing", "tech"],
    ),
    MusicTrackItem(
        id="corporate_inspire",
        title="Inspiring Innovation",
        artist="Pinnacle Scores",
        mood="Chuyên Nghiệp, Tiến Bộ",
        genre="Corporate Orchestral",
        duration_sec=64,
        bpm=118,
        recommended_volume=0.14,
        preview_url="/music/corporate_inspire/preview",
        tags=["corporate", "pitch", "business", "explainer"],
    ),
    MusicTrackItem(
        id="ambient_minimal",
        title="Subtle Clarity Wave",
        artist="Echoes of Silence",
        mood="Thanh Bình, Trực Quan",
        genre="Ambient Drone",
        duration_sec=64,
        bpm=70,
        recommended_volume=0.10,
        preview_url="/music/ambient_minimal/preview",
        tags=["minimal", "zen", "science", "subtle"],
    ),
]


@router.get("", response_model=List[MusicTrackItem])
async def list_music() -> List[MusicTrackItem]:
    """Trả về danh mục nhạc nền (BGM) bản quyền cho video whiteboard."""
    return MUSIC_CATALOG


@router.get("/{music_id}/preview")
async def get_music_preview(music_id: str):
    """Phát nhạc thử BGM định dạng MP3/WAV."""
    music_dir = PROJECT_ROOT / "assets" / "audio" / "music"
    for ext in [".mp3", ".wav", ".aac"]:
        file_path = music_dir / f"{music_id}{ext}"
        if file_path.exists():
            media_type = "audio/mpeg" if ext == ".mp3" else ("audio/wav" if ext == ".wav" else "audio/aac")
            return FileResponse(
                path=file_path,
                media_type=media_type,
                filename=f"{music_id}{ext}",
            )
    raise HTTPException(status_code=404, detail=f"Không tìm thấy file nhạc nền: {music_id}")


class UploadCustomBgmRequest(BaseModel):
    title: str = Field(min_length=1)
    audio_data_base64: str
    mood: Optional[str] = "Tùy Biến"
    genre: Optional[str] = "Nhạc Cá Nhân"
    recommended_volume: Optional[float] = 0.15


@router.post("/upload-custom-bgm", response_model=MusicTrackItem)
async def upload_custom_bgm(req: UploadCustomBgmRequest) -> MusicTrackItem:
    """
    Tải lên file nhạc nền cá nhân MP3/WAV (Task 8.3).
    Chuẩn hóa và lưu trữ trong thư mục BGM của dự án để sử dụng cho toàn bộ video.
    """
    import base64
    import uuid
    from core.audio.mixer import AudioMixer

    if not req.audio_data_base64:
        raise HTTPException(status_code=400, detail="Dữ liệu âm thanh không được để trống")

    music_dir = PROJECT_ROOT / "assets" / "audio" / "music"
    music_dir.mkdir(parents=True, exist_ok=True)

    try:
        data_str = req.audio_data_base64
        if "," in data_str:
            data_str = data_str.split(",", 1)[1]

        raw_bytes = base64.b64decode(data_str)
        if len(raw_bytes) < 64:
            raise HTTPException(status_code=400, detail="Dung lượng file nhạc không hợp lệ")

        custom_id = f"custom_{uuid.uuid4().hex[:8]}"
        temp_input = music_dir / f"{custom_id}_temp.bin"
        temp_input.write_bytes(raw_bytes)

        mixer = AudioMixer()
        audio_arr, _ = mixer.read_audio(temp_input)
        duration_sec = int(round(audio_arr.shape[1] / float(mixer.sample_rate)))

        out_mp3 = music_dir / f"{custom_id}.mp3"
        mixer.write_audio(audio_arr, out_mp3, codec="libmp3lame")

        try:
            temp_input.unlink(missing_ok=True)
        except Exception:
            pass

        track_item = MusicTrackItem(
            id=custom_id,
            title=req.title.strip(),
            artist="Người dùng tải lên",
            mood=req.mood or "Tùy Biến",
            genre=req.genre or "Nhạc Cá Nhân",
            duration_sec=max(5, duration_sec),
            bpm=110,
            recommended_volume=req.recommended_volume or 0.15,
            preview_url=f"/music/{custom_id}/preview",
            tags=["custom", "user_upload", "bgm"],
        )

        # Chèn lên đầu danh mục nhạc khả dụng
        MUSIC_CATALOG.insert(0, track_item)

        return track_item

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tải nhạc nền cá nhân: {str(e)}")


