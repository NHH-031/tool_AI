from __future__ import annotations

import hashlib
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class PipelineContext(BaseModel):
    """Data contract chuẩn xuyên suốt toàn bộ các stage của Whiteboard Pipeline."""
    job_id: str = Field(description="Mã định danh duy nhất của production job")
    project_id: str = Field(default="proj-default", description="Mã dự án liên kết")
    input_mode: str = Field(default="SCRIPT", description="Chế độ nhập: 'SCRIPT' | 'IDEA'")
    original_input: str = Field(description="Dữ liệu nguyên bản người dùng nhập")
    script: str = Field(description="Kịch bản dùng làm Source of Truth cho toàn bộ pipeline")
    script_hash: str = Field(description="Mã băm SHA-256 đối soát tính nhất quán")
    language: str = Field(default="vi", description="Ngôn ngữ thuyết minh")
    voice_id: str = Field(default="vi-VN-Standard-B", description="Giọng đọc thuyết minh")
    speed: float = Field(default=1.0, description="Tốc độ đọc")
    music_id: str = Field(default="whimsical_play", description="Nhạc nền")
    music_volume: float = Field(default=0.15, description="Âm lượng nhạc nền")
    visual_style: str = Field(default="notion_minimal", description="Phong cách hình ảnh")
    aspect_ratio: str = Field(default="16:9", description="Tỉ lệ khung hình")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata bổ sung")

    @classmethod
    def create(
        cls,
        job_id: str,
        input_text: str,
        input_mode: str = "SCRIPT",
        title: str = "Whiteboard Video",
        language: str = "vi",
        voice_id: str = "vi-VN-Standard-B",
        speed: float = 1.0,
        music_id: str = "whimsical_play",
        music_volume: float = 0.15,
        visual_style: str = "notion_minimal",
        aspect_ratio: str = "16:9",
        project_id: str = "proj-default",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PipelineContext:
        clean_text = input_text.strip()
        h = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()[:12]
        return cls(
            job_id=job_id,
            project_id=project_id,
            input_mode=input_mode.upper(),
            original_input=clean_text,
            script=clean_text,
            script_hash=h,
            language=language,
            voice_id=voice_id,
            speed=speed,
            music_id=music_id,
            music_volume=music_volume,
            visual_style=visual_style,
            aspect_ratio=aspect_ratio,
            metadata=metadata or {},
        )
