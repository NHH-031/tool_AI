from __future__ import annotations

import datetime
import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ARCHIVE_STORAGE_DIR = PROJECT_ROOT / "output" / "export"
REGISTRY_FILE = PROJECT_ROOT / "output" / "video_archive.json"


def _format_size(size_bytes: int) -> str:
    """Format dung lượng sang KB, MB, GB dễ đọc."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def _get_video_duration(video_path: Path) -> float:
    """Đo thời lượng video mp4 bằng av hoặc ffprobe nếu có."""
    try:
        import av
        with av.open(str(video_path)) as container:
            if container.duration:
                return float(container.duration) / av.time_base
            for s in container.streams:
                if s.duration and s.time_base:
                    return float(s.duration * s.time_base)
    except Exception:
        pass
    return 0.0


class VideoArchiveManager:
    """Quản lý kho lưu trữ video bền vững trên ổ D của hệ thống."""

    def __init__(self, storage_dir: Optional[Path] = None, registry_file: Optional[Path] = None):
        self.storage_dir = storage_dir or ARCHIVE_STORAGE_DIR
        self.registry_file = registry_file or REGISTRY_FILE
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)

    def _load_registry(self) -> Dict[str, Dict[str, Any]]:
        if not self.registry_file.exists():
            return {}
        try:
            content = self.registry_file.read_text(encoding="utf-8")
            return json.loads(content)
        except Exception as e:
            logger.warning(f"Lỗi đọc registry file: {e}")
            return {}

    def _save_registry(self, data: Dict[str, Dict[str, Any]]) -> None:
        try:
            self.registry_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error(f"Lỗi ghi registry file: {e}")

    def add_video(
        self,
        job_id: str,
        title: str,
        project_id: str,
        file_path: Path,
        duration_sec: float = 0.0,
        scene_count: int = 1,
        thumbnail_url: Optional[str] = None,
        resolution: str = "1280x720",
    ) -> Dict[str, Any]:
        """Đăng ký video mới vào kho lưu trữ vĩnh viễn trên ổ D."""
        registry = self._load_registry()
        video_id = job_id or f"vid-{int(datetime.datetime.now().timestamp())}"

        if not duration_sec or duration_sec <= 0.0:
            duration_sec = _get_video_duration(file_path)

        file_size = file_path.stat().st_size if file_path.exists() else 0

        # Tìm thumbnail nếu chưa có
        if not thumbnail_url and file_path.parent.exists():
            thumb_cands = list(file_path.parent.glob("scene_1*.png")) or list(file_path.parent.glob("*.png"))
            if thumb_cands:
                rel = thumb_cands[0].relative_to(PROJECT_ROOT / "output")
                thumbnail_url = f"/media/{rel.as_posix()}"

        rel_video = file_path.relative_to(PROJECT_ROOT / "output") if file_path.is_relative_to(PROJECT_ROOT / "output") else file_path.name
        video_url = f"/media/{Path(rel_video).as_posix()}"

        record = {
            "id": video_id,
            "title": title or "Whiteboard Video",
            "project_id": project_id,
            "file_name": file_path.name,
            "absolute_path": str(file_path.resolve()),
            "video_url": video_url,
            "thumbnail_url": thumbnail_url,
            "duration_sec": round(duration_sec, 2),
            "file_size_bytes": file_size,
            "file_size_formatted": _format_size(file_size),
            "scene_count": scene_count,
            "resolution": resolution,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

        registry[video_id] = record
        self._save_registry(registry)
        logger.info(f"Đã lưu video '{title}' vào kho lưu trữ: {file_path}")
        return record

    def list_videos(self) -> List[Dict[str, Any]]:
        """Lấy danh sách video từ kho lưu trữ (tự động kiểm tra file còn tồn tại trên đĩa)."""
        # Tự động scan nếu registry còn trống hoặc file trên đĩa mới hơn
        registry = self._load_registry()
        if not registry:
            self.scan_and_sync()
            registry = self._load_registry()

        items = []
        for vid_id, data in registry.items():
            abs_p = Path(data.get("absolute_path", ""))
            if abs_p.exists():
                # Cập nhật size nếu thay đổi
                cur_size = abs_p.stat().st_size
                if cur_size != data.get("file_size_bytes"):
                    data["file_size_bytes"] = cur_size
                    data["file_size_formatted"] = _format_size(cur_size)
                items.append(data)

        # Sắp xếp từ mới nhất đến cũ nhất
        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return items

    def scan_and_sync(self) -> List[Dict[str, Any]]:
        """Quét toàn bộ thư mục output/export trên ổ D và cập nhật kho lưu trữ."""
        registry = self._load_registry()
        search_dirs = [
            self.storage_dir,
            PROJECT_ROOT / "output" / "export",
            PROJECT_ROOT / "output",
        ]

        found_files: List[Path] = []
        seen_paths = set()

        # Quét ưu tiên các file _final.mp4 hoặc trong export
        for base in search_dirs:
            if not base.exists():
                continue
            for mp4 in base.rglob("*.mp4"):
                # Bỏ qua các file _raw.mp4 tạm thời
                if "_raw.mp4" in mp4.name.lower():
                    continue
                # Chỉ lấy các file video phân cảnh hoặc video final
                if mp4.name.endswith("_final.mp4") or "export" in str(mp4):
                    resolved = str(mp4.resolve())
                    if resolved not in seen_paths:
                        seen_paths.add(resolved)
                        found_files.append(mp4)

        for mp4 in found_files:
            file_str = str(mp4.resolve())
            # Kiểm tra xem file đã có trong registry chưa
            existing_key = None
            for k, v in registry.items():
                if v.get("absolute_path") == file_str:
                    existing_key = k
                    break

            if not existing_key:
                # Tạo bản ghi mới cho video tìm thấy
                vid_id = f"vid-{mp4.stem}"
                # Đo duration
                dur = _get_video_duration(mp4)
                size = mp4.stat().st_size

                # Tự suy luận title từ folder cha
                parent_name = mp4.parent.name
                if "solar" in parent_name.lower():
                    title = "Pin năng lượng mặt trời hoạt động thế nào"
                elif "monkey" in parent_name.lower():
                    title = "Con khỉ trèo cây lấy chuối"
                elif "truong_giang" in parent_name.lower():
                    title = "Truyện cổ tích Trường Giang"
                elif "tiktok" in parent_name.lower():
                    title = "Video Whiteboard TikTok Ngắn"
                elif "astronaut" in parent_name.lower():
                    title = "Phi hành gia trên Sao Hỏa"
                else:
                    title = f"Video Whiteboard ({parent_name})"

                # Thumbnail
                thumb_url = None
                thumb_cands = list(mp4.parent.glob("*.png"))
                if thumb_cands:
                    rel = thumb_cands[0].relative_to(PROJECT_ROOT / "output")
                    thumb_url = f"/media/{rel.as_posix()}"

                try:
                    rel_video = mp4.relative_to(PROJECT_ROOT / "output")
                    video_url = f"/media/{rel_video.as_posix()}"
                except ValueError:
                    video_url = f"/media/export/{mp4.name}"

                ctime = datetime.datetime.fromtimestamp(mp4.stat().st_mtime, tz=datetime.timezone.utc).isoformat()

                registry[vid_id] = {
                    "id": vid_id,
                    "title": title,
                    "project_id": parent_name,
                    "file_name": mp4.name,
                    "absolute_path": file_str,
                    "video_url": video_url,
                    "thumbnail_url": thumb_url,
                    "duration_sec": round(dur, 2) if dur > 0 else 5.0,
                    "file_size_bytes": size,
                    "file_size_formatted": _format_size(size),
                    "scene_count": 1,
                    "resolution": "1280x720",
                    "created_at": ctime,
                }

        self._save_registry(registry)
        return self.list_videos()

    def delete_video(self, video_id: str, delete_file: bool = True) -> bool:
        """Xóa video khỏi kho và tùy chọn xóa file trên ổ D."""
        registry = self._load_registry()
        if video_id not in registry:
            return False

        item = registry.pop(video_id)
        self._save_registry(registry)

        if delete_file:
            abs_p = Path(item.get("absolute_path", ""))
            try:
                if abs_p.exists():
                    abs_p.unlink()
                    logger.info(f"Đã xóa file video trên ổ đĩa: {abs_p}")
            except Exception as e:
                logger.warning(f"Lỗi khi xóa file vật lý: {e}")

        return True

    def open_in_explorer(self, target_path: Optional[str] = None) -> bool:
        """Mở thư mục hoặc file trong Windows Explorer ổ D."""
        path_to_open = Path(target_path) if target_path else self.storage_dir
        if not path_to_open.exists():
            path_to_open = self.storage_dir

        try:
            if path_to_open.is_file():
                # Bôi đen file trong thư mục
                subprocess.Popen(f'explorer.exe /select,"{path_to_open.resolve()}"')
            else:
                # Mở thư mục
                subprocess.Popen(f'explorer.exe "{path_to_open.resolve()}"')
            return True
        except Exception as e:
            logger.error(f"Lỗi khi mở Windows Explorer: {e}")
            return False

    def get_storage_stats(self) -> Dict[str, Any]:
        """Lấy thông tin thống kê dung lượng ổ D và kho lưu trữ."""
        videos = self.list_videos()
        total_size = sum(v.get("file_size_bytes", 0) for v in videos)

        # Lấy dung lượng ổ đĩa D
        free_bytes = 0
        total_disk_bytes = 0
        try:
            usage = shutil.disk_usage(str(self.storage_dir))
            free_bytes = usage.free
            total_disk_bytes = usage.total
        except Exception:
            pass

        return {
            "storage_path": str(self.storage_dir.resolve()),
            "total_videos": len(videos),
            "used_storage_bytes": total_size,
            "used_storage_formatted": _format_size(total_size),
            "disk_free_bytes": free_bytes,
            "disk_free_formatted": _format_size(free_bytes),
            "disk_total_formatted": _format_size(total_disk_bytes),
            "drive_letter": str(self.storage_dir.resolve().drive) or "D:",
        }


# Global singleton instance
archive_manager = VideoArchiveManager()
