from __future__ import annotations

from pathlib import Path
from typing import Optional
from ..providers.base import StorageProvider


class AssetManager:
    """Quản lý đường dẫn, lưu trữ và bóc tách các asset cho từng dự án."""

    def __init__(self, storage: StorageProvider, project_id: str):
        self.storage = storage
        self.project_id = project_id

    def _resolve_key(self, scene_id: Optional[str], filename: str) -> str:
        if scene_id:
            return f"projects/{self.project_id}/scenes/{scene_id}/{filename}"
        return f"projects/{self.project_id}/{filename}"

    async def save_image(self, scene_id: str, image_bytes: bytes, filename: str = "lineart.png") -> str:
        key = self._resolve_key(scene_id, filename)
        return await self.storage.save_asset(key, image_bytes, content_type="image/png")

    async def save_audio(self, scene_id: str, audio_bytes: bytes, filename: str = "narration.mp3") -> str:
        key = self._resolve_key(scene_id, filename)
        return await self.storage.save_asset(key, audio_bytes, content_type="audio/mpeg")

    async def save_annotation(self, scene_id: str, json_text: str, filename: str = "scene.annotation.json") -> str:
        key = self._resolve_key(scene_id, filename)
        return await self.storage.save_asset(key, json_text.encode("utf-8"), content_type="application/json")
