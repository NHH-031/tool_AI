"""Module quản lý từ điển ánh xạ ngữ nghĩa đa ngôn ngữ (VN -> EN) cho Artwork Generators."""
import json
import logging
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger(__name__)

_MAP_CACHE: List[Tuple[str, str]] = []


def get_vietnamese_mapping() -> List[Tuple[str, str]]:
    """Trả về danh sách các cặp (từ khóa tiếng Việt, mô tả tiếng Anh tương ứng)."""
    global _MAP_CACHE
    if not _MAP_CACHE:
        json_path = Path(__file__).parent / "vi_to_en.json"
        if json_path.exists():
            try:
                raw_data = json.loads(json_path.read_text(encoding="utf-8"))
                _MAP_CACHE = [(item[0], item[1]) for item in raw_data]
            except Exception as e:
                logger.error(f"[translations] Error loading vi_to_en.json: {e}")
                _MAP_CACHE = []
    return _MAP_CACHE
