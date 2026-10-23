from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

from core.schemas.drawing import DrawingStroke
from .vectorizer import VectorStrokeSegment


class NaturalStrokeSorter:
    """
    Bộ quy hoạch thứ tự vẽ tự nhiên của người thật (Natural Stroke Order Planner):
    1. Trình tự cấp bậc mỹ thuật: Outline (khung ngoài) -> Structure (nét chính) -> Detail (chi tiết) -> Shading (tô bóng).
    2. Hướng vẽ tự nhiên của cánh tay người: Ưu tiên vẽ từ trên xuống dưới, từ trái qua phải để không bị che khuất tầm nhìn.
    3. Tối ưu hóa quỹ đạo nhấc bút (Pen Travel Optimization): Tìm nét vẽ gần nhất tiếp theo và tự động đảo ngược chiều nét (reverse stroke) nếu vẽ từ đầu đối diện tiết kiệm hành trình di chuyển của bàn tay.
    4. Phân bổ thời lượng tự nhiên: Theo chiều dài hình học kèm hiệu ứng gia tốc vẽ mềm mại (ease-in-out).
    """

    CATEGORY_PRIORITY: Dict[str, int] = {
        "outline": 10,
        "trunk": 10,
        "body": 10,
        "banana_body": 10,
        "structure": 20,
        "head": 20,
        "branches": 20,
        "face": 30,
        "leaves": 30,
        "arms": 40,
        "legs": 50,
        "detail": 60,
        "tail": 60,
        "fruits": 60,
        "stem": 70,
        "shading": 80,
        "hatch": 80,
        "color_fill": 90,
        "fill": 90,
        "color": 90,
        "wash": 90,
    }

    @classmethod
    def sort_strokes_naturally(
        cls,
        strokes: List[DrawingStroke],
        canvas_width: float = 1920.0,
        canvas_height: float = 1080.0,
        total_duration_sec: float = 4.0,
        allow_reverse_direction: bool = True,
    ) -> List[DrawingStroke]:
        """
        Sắp xếp danh sách nét vẽ theo quy tắc vẽ tay tự nhiên và tối ưu quãng đường bàn tay di chuyển.
        """
        if not strokes:
            return []

        # 1. Nhóm các nét vẽ theo nhóm ưu tiên mỹ thuật
        def get_priority(s: DrawingStroke) -> int:
            return cls.CATEGORY_PRIORITY.get(s.semantic_purpose.lower(), 50)

        # Gom các nét vẽ theo từng bậc ưu tiên
        priority_buckets: Dict[int, List[DrawingStroke]] = {}
        for s in strokes:
            p = get_priority(s)
            priority_buckets.setdefault(p, []).append(s)

        sorted_priorities = sorted(priority_buckets.keys())
        ordered_all: List[DrawingStroke] = []
        current_hand_pos: Tuple[float, float] = (0.0, 0.0)

        # 2. Duyệt qua từng bậc ưu tiên và áp dụng tối ưu hóa đường đi ngắn nhất (Greedy TSP + Spatial bias)
        for prio in sorted_priorities:
            bucket = priority_buckets[prio]
            if not bucket:
                continue

            unvisited = list(bucket)

            # Chọn nét đầu tiên của nhóm: ưu tiên nét ở góc trên bên trái (Top-Left)
            def initial_cost(s: DrawingStroke) -> float:
                sp = s.start_point
                # Trọng số Y (từ trên xuống) và X (từ trái qua)
                return sp[1] * 1.5 + sp[0]

            unvisited.sort(key=initial_cost)
            current_stroke = unvisited.pop(0)
            ordered_all.append(current_stroke)
            current_hand_pos = current_stroke.end_point

            # Lần lượt chọn nét tiếp theo gần nhất
            while unvisited:
                best_idx = 0
                best_dist = float("inf")
                should_reverse = False

                for i, cand in enumerate(unvisited):
                    # Khoảng cách từ đầu bút hiện tại đến điểm đầu nét cand
                    d_start = math.hypot(
                        current_hand_pos[0] - cand.start_point[0],
                        current_hand_pos[1] - cand.start_point[1],
                    )
                    # Khoảng cách từ đầu bút hiện tại đến điểm cuối nét cand (nếu đảo chiều)
                    d_end = math.hypot(
                        current_hand_pos[0] - cand.end_point[0],
                        current_hand_pos[1] - cand.end_point[1],
                    )

                    # Phạt khoảng cách nếu nét nằm quá xa về phía trên (hạn chế tay vẽ giật ngược lên)
                    bias_start = (cand.start_point[1] - current_hand_pos[1]) * -0.2
                    cost_start = d_start + max(0.0, bias_start)

                    bias_end = (cand.end_point[1] - current_hand_pos[1]) * -0.2
                    cost_end = d_end + max(0.0, bias_end)

                    if cost_start < best_dist:
                        best_dist = cost_start
                        best_idx = i
                        should_reverse = False

                    if allow_reverse_direction and cost_end < best_dist:
                        best_dist = cost_end
                        best_idx = i
                        should_reverse = True

                chosen = unvisited.pop(best_idx)

                # Nếu khoảng cách đến điểm cuối gần hơn nhiều, đảo chiều nét vẽ
                if should_reverse:
                    chosen = cls._reverse_stroke(chosen)

                ordered_all.append(chosen)
                current_hand_pos = chosen.end_point

        # 3. Phân bổ thời lượng chi tiết cho từng nét vẽ
        total_len = sum(s.length for s in ordered_all)
        if total_len <= 0:
            total_len = len(ordered_all) * 100.0

        for idx, stroke in enumerate(ordered_all, start=1):
            stroke.order = idx
            # Tỉ lệ thời lượng theo chiều dài, tối thiểu 0.04s và tối đa 1.5s cho 1 nét
            prop_dur = (stroke.length / total_len) * total_duration_sec
            stroke.duration = max(0.035, min(1.8, round(prop_dur, 3)))

        return ordered_all

    @staticmethod
    def _reverse_stroke(stroke: DrawingStroke) -> DrawingStroke:
        """Đảo ngược hướng vẽ của nét (điểm cuối thành điểm đầu)."""
        rev_points = list(reversed(stroke.points))
        return DrawingStroke(
            id=stroke.id,
            asset_id=stroke.asset_id,
            path=stroke.path,
            order=stroke.order,
            duration=stroke.duration,
            start_point=rev_points[0] if rev_points else stroke.end_point,
            end_point=rev_points[-1] if rev_points else stroke.start_point,
            semantic_purpose=stroke.semantic_purpose,
            points=rev_points,
            length=stroke.length,
            color_hex=stroke.color_hex,
            stroke_width=stroke.stroke_width,
            path_mode=stroke.path_mode,
        )
