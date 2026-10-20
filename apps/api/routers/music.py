from pathlib import Path
from typing import List
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

