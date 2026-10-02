from __future__ import annotations

from typing import List
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/music", tags=["Music"])


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
        duration_sec=145,
        bpm=110,
        recommended_volume=0.15,
        tags=["cheerful", "acoustic", "storytelling", "bright"],
    ),
    MusicTrackItem(
        id="whimsical_play",
        title="Playful Forest Marimba",
        artist="Animation Soundworks",
        mood="Vui Nhộn, Tinh Nghịch",
        genre="Children Animation",
        duration_sec=120,
        bpm=124,
        recommended_volume=0.18,
        tags=["whimsical", "monkey", "cartoon", "playful"],
    ),
    MusicTrackItem(
        id="lofi_chill",
        title="Late Night Whiteboard Lofi",
        artist="Tokyo Chillhop Beats",
        mood="Thư Giãn, Tập Trung",
        genre="Lofi Hip Hop",
        duration_sec=180,
        bpm=85,
        recommended_volume=0.12,
        tags=["lofi", "study", "relaxing", "tech"],
    ),
    MusicTrackItem(
        id="corporate_inspire",
        title="Inspiring Innovation",
        artist="Pinnacle Scores",
        mood="Chuyên Nghiệp, Tiến Bộ",
        genre="Corporate Orchestral",
        duration_sec=160,
        bpm=118,
        recommended_volume=0.14,
        tags=["corporate", "pitch", "business", "explainer"],
    ),
    MusicTrackItem(
        id="ambient_minimal",
        title="Subtle Clarity Wave",
        artist="Echoes of Silence",
        mood="Thanh Bình, Trực Quan",
        genre="Ambient Drone",
        duration_sec=210,
        bpm=70,
        recommended_volume=0.10,
        tags=["minimal", "zen", "science", "subtle"],
    ),
]


@router.get("", response_model=List[MusicTrackItem])
async def list_music() -> List[MusicTrackItem]:
    """Trả về danh mục nhạc nền (BGM) bản quyền cho video whiteboard."""
    return MUSIC_CATALOG
