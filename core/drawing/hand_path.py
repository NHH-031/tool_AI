from __future__ import annotations

import math
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field

from core.schemas.drawing import DrawingStroke


class HandState(BaseModel):
    """Trạng thái tức thời của bàn tay vẽ tại một mốc thời gian."""
    time_sec: float = Field(description="Mốc thời gian (giây)")
    x: float = Field(description="Tọa độ X của đầu bút trên canvas")
    y: float = Field(description="Tọa độ Y của đầu bút trên canvas")
    is_drawing: bool = Field(description="Bút đang hạ nét trên mặt bảng (True) hay nhấc bút di chuyển (False)")
    stroke_id: Optional[str] = Field(default=None, description="Mã nét vẽ đang thực hiện")
    stroke_progress: float = Field(default=0.0, description="Tiến độ của nét vẽ hiện tại (0.0 đến 1.0)")


class HandPathPlanner:
    """
    Tính toán quỹ đạo di chuyển của bàn tay (Hand Path) theo chuỗi các nét vẽ.
    Xác định chính xác vị trí đầu bút tại bất kỳ thời điểm nào t.
    """

    def __init__(
        self,
        strokes: List[DrawingStroke],
        travel_duration_sec: float = 0.08,
    ):
        self.strokes = strokes
        self.travel_duration_sec = travel_duration_sec
        self.timeline_events: List[dict] = []
        self._build_timeline()

    def _build_timeline(self) -> None:
        """Xây dựng trục thời gian chi tiết cho từng nét vẽ và khoảng chuyển tiếp."""
        self.timeline_events.clear()
        current_time = 0.0

        for i, stroke in enumerate(self.strokes):
            # Sự kiện vẽ nét
            dur = max(0.05, stroke.duration)
            self.timeline_events.append({
                "type": "draw",
                "stroke": stroke,
                "start_time": current_time,
                "end_time": current_time + dur,
                "duration": dur,
            })
            current_time += dur

            # Nếu còn nét tiếp theo, thêm khoảng nghỉ chuyển tiếp (nhấc bút)
            if i + 1 < len(self.strokes):
                next_stroke = self.strokes[i + 1]
                self.timeline_events.append({
                    "type": "travel",
                    "start_pt": stroke.end_point,
                    "end_pt": next_stroke.start_point,
                    "start_time": current_time,
                    "end_time": current_time + self.travel_duration_sec,
                    "duration": self.travel_duration_sec,
                })
                current_time += self.travel_duration_sec

        self.total_duration_sec = current_time

    def get_hand_state(self, time_sec: float) -> HandState:
        """Tính toán vị trí đầu bút và trạng thái vẽ tại mốc thời gian time_sec."""
        if not self.strokes:
            return HandState(time_sec=time_sec, x=0.0, y=0.0, is_drawing=False)

        # Nếu trước thời điểm bắt đầu
        if time_sec <= 0:
            first_pt = self.strokes[0].start_point
            return HandState(
                time_sec=0.0,
                x=first_pt[0],
                y=first_pt[1],
                is_drawing=True,
                stroke_id=self.strokes[0].id,
                stroke_progress=0.0,
            )

        # Nếu sau thời điểm kết thúc toàn bộ nét vẽ
        if time_sec >= self.total_duration_sec:
            last_pt = self.strokes[-1].end_point
            return HandState(
                time_sec=self.total_duration_sec,
                x=last_pt[0],
                y=last_pt[1],
                is_drawing=False,
                stroke_id=self.strokes[-1].id,
                stroke_progress=1.0,
            )

        # Tìm event trong timeline
        for ev in self.timeline_events:
            if ev["start_time"] <= time_sec <= ev["end_time"]:
                dur = ev["duration"]
                t_rel = (time_sec - ev["start_time"]) / dur if dur > 0 else 1.0

                if ev["type"] == "draw":
                    stroke: DrawingStroke = ev["stroke"]
                    pts = stroke.points
                    if not pts:
                        return HandState(time_sec=time_sec, x=0.0, y=0.0, is_drawing=True)
                    # Lấy điểm nội suy trên polyline
                    idx_float = t_rel * (len(pts) - 1)
                    idx = int(idx_float)
                    frac = idx_float - idx
                    if idx >= len(pts) - 1:
                        pt = pts[-1]
                    else:
                        p1, p2 = pts[idx], pts[idx + 1]
                        pt = (p1[0] + frac * (p2[0] - p1[0]), p1[1] + frac * (p2[1] - p1[1]))

                    return HandState(
                        time_sec=time_sec,
                        x=round(pt[0], 2),
                        y=round(pt[1], 2),
                        is_drawing=True,
                        stroke_id=stroke.id,
                        stroke_progress=round(t_rel, 3),
                    )

                elif ev["type"] == "travel":
                    # Nội suy chuyển động mượt mà (smooth cubic ease in-out) giữa 2 nét
                    p_start, p_end = ev["start_pt"], ev["end_pt"]
                    ease_t = 3 * (t_rel**2) - 2 * (t_rel**3)
                    x = p_start[0] + ease_t * (p_end[0] - p_start[0])
                    y = p_start[1] + ease_t * (p_end[1] - p_start[1])
                    return HandState(
                        time_sec=time_sec,
                        x=round(x, 2),
                        y=round(y, 2),
                        is_drawing=False,
                        stroke_id=None,
                        stroke_progress=0.0,
                    )

        # Mặc định an toàn
        return HandState(
            time_sec=time_sec,
            x=self.strokes[-1].end_point[0],
            y=self.strokes[-1].end_point[1],
            is_drawing=False,
        )

    def sample_trajectory(self, fps: int = 30) -> List[HandState]:
        """Lấy mẫu toàn bộ chuỗi vị trí bàn tay theo tốc độ khung hình."""
        if fps <= 0:
            fps = 30
        dt = 1.0 / fps
        num_frames = int(self.total_duration_sec * fps) + 1
        return [self.get_hand_state(f * dt) for f in range(num_frames)]


def transform_strokes_to_canvas(
    strokes: List[DrawingStroke],
    view_box: str,
    target_x: float,
    target_y: float,
    target_width: float,
    target_height: float,
) -> List[DrawingStroke]:
    """
    Chuyển đổi hệ tọa độ của các nét vẽ từ SVG viewBox sang tọa độ Canvas đích.
    Giữ nguyên tỉ lệ khung hình (aspect ratio fit) bên trong bounding box.
    """
    vb_parts = [float(v) for v in view_box.split()] if view_box else [0, 0, 500, 500]
    if len(vb_parts) == 4:
        vb_x, vb_y, vb_w, vb_h = vb_parts
    else:
        vb_x, vb_y, vb_w, vb_h = 0.0, 0.0, 500.0, 500.0

    scale_x = target_width / vb_w if vb_w > 0 else 1.0
    scale_y = target_height / vb_h if vb_h > 0 else 1.0
    scale = min(scale_x, scale_y)

    # Căn giữa trong bounding box
    offset_x = target_x + (target_width - vb_w * scale) / 2.0
    offset_y = target_y + (target_height - vb_h * scale) / 2.0

    transformed: List[DrawingStroke] = []
    for s in strokes:
        new_pts = [
            (
                round(offset_x + (pt[0] - vb_x) * scale, 2),
                round(offset_y + (pt[1] - vb_y) * scale, 2),
            )
            for pt in s.points
        ]
        transformed.append(
            DrawingStroke(
                id=s.id,
                asset_id=s.asset_id,
                path=s.path,
                order=s.order,
                duration=s.duration,
                start_point=new_pts[0] if new_pts else (0.0, 0.0),
                end_point=new_pts[-1] if new_pts else (0.0, 0.0),
                semantic_purpose=s.semantic_purpose,
                points=new_pts,
                length=round(s.length * scale, 2),
                color_hex=s.color_hex,
                stroke_width=round(s.stroke_width * scale, 2),
                path_mode=s.path_mode,
            )
        )
    return transformed
