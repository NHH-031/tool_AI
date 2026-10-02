from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class VoiceConfig(BaseModel):
    """Cấu hình giọng đọc TTS."""
    model_config = ConfigDict(populate_by_name=True)

    voice_id: str = Field(default="vi-VN-HoaiMyNeural", alias="voiceId", description="ID định danh giọng đọc")
    language: str = Field(default="vi-VN", description="Mã ngôn ngữ IETF (vi-VN, en-US,...)")
    speed: float = Field(default=1.0, ge=0.25, le=4.0, description="Tốc độ đọc (1.0 là bình thường)")
    pitch: float = Field(default=0.0, ge=-50.0, le=50.0, description="Độ cao giọng đọc (Hz hoặc semitones)")


class WordTiming(BaseModel):
    """Mốc thời gian phát âm của từng từ đơn lẻ."""
    word: str = Field(description="Từ được phát âm")
    start_time: float = Field(ge=0.0, description="Thời điểm bắt đầu (giây)")
    end_time: float = Field(ge=0.0, description="Thời điểm kết thúc (giây)")
    duration: float = Field(ge=0.0, description="Thời lượng phát âm từ (giây)")
    confidence: Optional[float] = Field(default=1.0, ge=0.0, le=1.0, description="Độ tin cậy của alignment")


class SentenceTiming(BaseModel):
    """Mốc thời gian phát âm của cả câu văn."""
    sentence: str = Field(description="Nội dung câu")
    start_time: float = Field(ge=0.0, description="Thời điểm bắt đầu câu (giây)")
    end_time: float = Field(ge=0.0, description="Thời điểm kết thúc câu (giây)")
    duration: float = Field(ge=0.0, description="Thời lượng phát âm câu (giây)")
    words: List[WordTiming] = Field(default_factory=list, description="Danh sách mốc thời gian từng từ trong câu")


class NarrationTiming(BaseModel):
    """Toàn bộ thông tin timing của đoạn thuyết minh."""
    text: str = Field(description="Toàn bộ văn bản thuyết minh")
    duration: float = Field(ge=0.0, description="Tổng thời lượng phát âm (giây)")
    timing_level: Literal["phoneme", "word", "sentence", "segment", "fallback_estimated"] = Field(
        default="word",
        description="Mức độ chi tiết của timing",
    )
    is_fallback: bool = Field(
        default=False,
        description="Cờ đánh dấu timing này là ước lượng dự phòng (fallback) hay timing thực",
    )
    fallback_reason: Optional[str] = Field(
        default=None,
        description="Lý do phải sử dụng timing dự phòng ước lượng",
    )
    words: List[WordTiming] = Field(default_factory=list, description="Các từ kèm mốc thời gian")
    sentences: List[SentenceTiming] = Field(default_factory=list, description="Các câu kèm mốc thời gian")


class TTSAudioResult(BaseModel):
    """Kết quả sinh âm thanh từ TTS Provider."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    audio_bytes: bytes = Field(description="Dữ liệu nhị phân âm thanh (WAV/MP3)")
    duration: float = Field(ge=0.0, description="Thời lượng phát âm thanh (giây)")
    duration_ms: int = Field(ge=0, description="Thời lượng phát âm thanh (mili-giây)")
    format: str = Field(default="wav", description="Định dạng âm thanh (wav, mp3)")
    sample_rate: int = Field(default=24000, description="Sample rate (Hz)")
    channels: int = Field(default=1, description="Số kênh âm thanh (1=mono, 2=stereo)")
    voice_config: VoiceConfig = Field(description="Cấu hình giọng đọc đã dùng")
    timing: Optional[NarrationTiming] = Field(default=None, description="Thông tin timing nếu provider hỗ trợ")
    audio_path: Optional[Path] = Field(default=None, description="Đường dẫn file âm thanh đã lưu nếu có")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata bổ sung từ provider")

    def save_to_file(self, destination_path: Path | str) -> Path:
        """Ghi dữ liệu audio bytes ra file đĩa và cập nhật audio_path."""
        dest = Path(destination_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(self.audio_bytes)
        self.audio_path = dest
        return dest
