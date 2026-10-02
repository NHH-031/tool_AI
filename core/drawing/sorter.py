from __future__ import annotations

from typing import Dict, List, Optional
from core.schemas.drawing import DrawingStroke


class StrokeOrderPlanner:
    """
    Quy hoạch thứ tự vẽ logic tự nhiên (Stroke Order):
    - Tree: trunk -> branches -> leaves -> fruits
    - Monkey: body -> head -> face -> arms -> legs -> tail
    - Banana: banana_body -> tip -> stem
    Đảm bảo họa sĩ bảng trắng phác họa khung móng nền trước, sau đó đến chi tiết.
    """

    # Thứ tự ưu tiên theo từng loại thực thể
    TREE_ORDER = {
        "trunk": 10,
        "branches": 20,
        "leaves": 30,
        "fruits": 40,
        "outline": 50,
        "detail": 60,
    }

    MONKEY_ORDER = {
        "body": 10,
        "head": 20,
        "face": 30,
        "arms": 40,
        "legs": 50,
        "tail": 60,
        "outline": 70,
        "detail": 80,
    }

    BANANA_ORDER = {
        "banana_body": 10,
        "tip": 20,
        "stem": 30,
        "outline": 40,
        "detail": 50,
    }

    DEFAULT_ORDER = {
        "trunk": 10,
        "body": 10,
        "banana_body": 10,
        "head": 20,
        "branches": 20,
        "face": 30,
        "leaves": 30,
        "arms": 40,
        "legs": 50,
        "tail": 60,
        "stem": 70,
        "outline": 80,
        "detail": 90,
    }

    @classmethod
    def get_priority_map(cls, asset_name: str) -> Dict[str, int]:
        name_lower = asset_name.lower()
        if "tree" in name_lower:
            return cls.TREE_ORDER
        elif "monkey" in name_lower:
            return cls.MONKEY_ORDER
        elif "banana" in name_lower:
            return cls.BANANA_ORDER
        return cls.DEFAULT_ORDER

    @classmethod
    def sort_and_time_strokes(
        cls,
        strokes: List[DrawingStroke],
        asset_name: str = "",
        total_duration_sec: float = 3.0,
    ) -> List[DrawingStroke]:
        """
        Sắp xếp các nét vẽ theo trình tự mỹ thuật tự nhiên và phân bổ thời lượng hợp lý.
        """
        if not strokes:
            return []

        priority_map = cls.get_priority_map(asset_name)

        # Sắp xếp ổn định (stable sort) theo thứ tự ưu tiên ngữ nghĩa
        sorted_strokes = sorted(
            strokes,
            key=lambda s: (priority_map.get(s.semantic_purpose, 100), s.order),
        )

        # Tính tổng chiều dài nét vẽ
        total_length = sum(s.length for s in sorted_strokes)
        if total_length <= 0:
            total_length = len(sorted_strokes) * 100.0

        # Gán lại chỉ số order tuần tự 1..N và tính thời lượng tỉ lệ
        for idx, stroke in enumerate(sorted_strokes, start=1):
            stroke.order = idx
            # Thời lượng mỗi nét tỉ lệ theo chiều dài nét, tối thiểu 0.05s
            if total_length > 0:
                stroke_dur = max(0.05, round((stroke.length / total_length) * total_duration_sec, 3))
            else:
                stroke_dur = round(total_duration_sec / len(sorted_strokes), 3)
            stroke.duration = stroke_dur

        return sorted_strokes
