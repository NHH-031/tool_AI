from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from core.storage.archive_manager import archive_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/archive", tags=["Archive"])


class VideoItemResponse(BaseModel):
    id: str
    title: str
    project_id: str
    file_name: str
    absolute_path: str
    video_url: str
    thumbnail_url: Optional[str] = None
    duration_sec: float
    file_size_bytes: int
    file_size_formatted: str
    scene_count: int
    resolution: str
    created_at: str


class StorageStatsResponse(BaseModel):
    storage_path: str
    total_videos: int
    used_storage_bytes: int
    used_storage_formatted: str
    disk_free_bytes: int
    disk_free_formatted: str
    disk_total_formatted: str
    drive_letter: str


class OpenFolderRequest(BaseModel):
    target_path: Optional[str] = None


@router.get("/videos", response_model=List[VideoItemResponse])
async def list_archived_videos() -> List[VideoItemResponse]:
    """Lấy danh sách tất cả các video trong kho lưu trữ trên ổ D."""
    videos = archive_manager.list_videos()
    return [VideoItemResponse(**v) for v in videos]


@router.get("/stats", response_model=StorageStatsResponse)
async def get_archive_stats() -> StorageStatsResponse:
    """Lấy thông tin dung lượng lưu trữ trên ổ D."""
    stats = archive_manager.get_storage_stats()
    return StorageStatsResponse(**stats)


@router.post("/scan", response_model=List[VideoItemResponse])
async def scan_and_sync_archive() -> List[VideoItemResponse]:
    """Quét lại toàn bộ ổ đĩa D để tìm kiếm các video đã xuất và cập nhật vào kho lưu trữ."""
    videos = archive_manager.scan_and_sync()
    return [VideoItemResponse(**v) for v in videos]


@router.post("/open-folder")
async def open_folder_in_explorer(req: OpenFolderRequest = OpenFolderRequest()) -> Dict[str, Any]:
    """Mở thư mục lưu trữ video trong File Explorer của Windows."""
    success = archive_manager.open_in_explorer(req.target_path)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể mở File Explorer trên máy chủ Windows",
        )
    return {"message": "Đã mở thư mục trên File Explorer", "success": True}


@router.delete("/videos/{video_id}")
async def delete_archived_video(
    video_id: str,
    delete_file: bool = Query(True, description="Xóa cả file vật lý trên đĩa cứng"),
) -> Dict[str, Any]:
    """Xóa video khỏi kho lưu trữ và tùy chọn giải phóng dung lượng ổ D."""
    success = archive_manager.delete_video(video_id, delete_file=delete_file)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy video với ID: {video_id}",
        )
    return {"message": "Đã xóa video thành công", "video_id": video_id}
