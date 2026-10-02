from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field
from core.schemas.tts import NarrationTiming


class TimelineEvent(BaseModel):
    """Sự kiện hợp nhất diễn ra trên trục thời gian của phân cảnh."""
    id: str = Field(description="Mã định danh duy nhất của sự kiện")
    event_type: Literal["narration", "drawing", "camera", "transition", "pause"] = Field(
        description="Loại sự kiện trên timeline",
    )
    start_ms: int = Field(ge=0, description="Thời điểm bắt đầu sự kiện (ms)")
    end_ms: int = Field(ge=0, description="Thời điểm kết thúc sự kiện (ms)")
    duration_ms: int = Field(ge=0, description="Thời lượng sự kiện (ms)")
    target_id: Optional[str] = Field(
        default=None,
        description="Mã ID đối tượng liên quan (VisualEntity ID hoặc Narration ID)",
    )
    description: str = Field(default="", description="Mô tả diễn giải sự kiện")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Dữ liệu phụ trợ tùy biến")


class DrawingTimelineEvent(BaseModel):
    """
    Sự kiện vẽ vector trên trục thời gian đồng bộ.
    Mỗi event tương ứng với một nét vẽ (stroke) hoặc một hành động di chuyển bút (hand_travel).
    """
    model_config = ConfigDict(populate_by_name=True)

    start_time: float = Field(alias="startTime", ge=0.0, description="Thời điểm bắt đầu sự kiện (giây)")
    end_time: float = Field(alias="endTime", ge=0.0, description="Thời điểm kết thúc sự kiện (giây)")
    asset_id: str = Field(alias="assetId", description="Mã định danh asset đang vẽ")
    stroke_id: str = Field(alias="strokeId", description="Mã nét vẽ (hoặc ID hành động di chuyển)")
    action: Literal["draw", "hand_travel", "pause", "highlight"] = Field(
        default="draw",
        description="Hành động vẽ thực tế hoặc di chuyển bàn tay trên không",
    )
    hand_path: List[Tuple[float, float]] = Field(
        default_factory=list,
        alias="handPath",
        description="Quỹ đạo tọa độ (x, y) bàn tay di chuyển trong sự kiện này",
    )
    semantic_purpose: str = Field(
        default="outline",
        alias="semanticPurpose",
        description="Mục đích ngữ nghĩa (trunk, branches, body, head, arms, banana_body, v.v.)",
    )
    stroke_d: str = Field(default="", description="Chuỗi SVG path d đã được map sang tọa độ canvas")
    stroke_width: float = Field(default=6.0, description="Độ dày nét vẽ trên canvas")
    color_hex: str = Field(default="#1A1A1A", description="Mã màu nét vẽ hex")
    entity_id: Optional[str] = Field(default=None, description="Mã entity tương ứng trong Scene Graph")
    points: List[Tuple[float, float]] = Field(default_factory=list, description="Các điểm mẫu của nét vẽ")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata bổ trợ")

    @property
    def startTime(self) -> float:
        return self.start_time

    @property
    def endTime(self) -> float:
        return self.end_time

    @property
    def assetId(self) -> str:
        return self.asset_id

    @property
    def strokeId(self) -> str:
        return self.stroke_id

    @property
    def handPath(self) -> List[Tuple[float, float]]:
        return self.hand_path

    @property
    def semanticPurpose(self) -> str:
        return self.semantic_purpose

    @property
    def duration(self) -> float:
        return round(self.end_time - self.start_time, 3)


class DrawingTimeline(BaseModel):
    """
    Toàn bộ timeline vẽ vector của phân cảnh video, hợp nhất:
    Narration timing + Visual Scene Graph + Assets + Drawing Strokes.
    """
    model_config = ConfigDict(populate_by_name=True)

    events: List[DrawingTimelineEvent] = Field(default_factory=list, description="Danh sách tuần tự các sự kiện vẽ")
    total_duration: float = Field(ge=0.0, description="Tổng thời lượng timeline (giây)")
    canvas_width: int = Field(default=1920, description="Chiều rộng canvas hiển thị (pixels)")
    canvas_height: int = Field(default=1080, description="Chiều cao canvas hiển thị (pixels)")
    narration_text: str = Field(default="", description="Toàn bộ kịch bản thuyết minh")
    narration_timing: Optional[NarrationTiming] = Field(default=None, description="Chi tiết timing của thuyết minh")
    entities_schedule: Dict[str, Tuple[float, float]] = Field(
        default_factory=dict,
        description="Lịch trình xuất hiện của từng entity {entity_id: (start_time, end_time)}",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata phụ trợ")

    def get_active_event_at(self, t: float) -> Optional[DrawingTimelineEvent]:
        """Lấy sự kiện đang diễn ra tại mốc thời gian t."""
        for ev in self.events:
            if ev.start_time <= t <= ev.end_time:
                return ev
        return None

    def get_drawn_strokes_at(self, t: float) -> List[DrawingTimelineEvent]:
        """Lấy danh sách các nét vẽ đã hoặc đang được vẽ tại mốc thời gian t."""
        return [ev for ev in self.events if ev.action == "draw" and ev.start_time <= t]

    def get_hand_position_at(self, t: float) -> Tuple[float, float, bool]:
        """
        Tính toán vị trí chính xác (x, y) của đầu ngòi bút tại mốc thời gian t.
        Trả về (x, y, is_drawing).
        """
        if not self.events:
            return (self.canvas_width / 2.0, self.canvas_height / 2.0, False)

        if t <= self.events[0].start_time:
            # Chưa bắt đầu: đặt bút tại điểm đầu của stroke đầu tiên
            first_path = self.events[0].hand_path
            if first_path:
                return (first_path[0][0], first_path[0][1], False)
            return (self.canvas_width / 2.0, self.canvas_height / 2.0, False)

        if t >= self.events[-1].end_time:
            # Đã vẽ xong: đặt bút tại điểm cuối của stroke cuối cùng
            last_path = self.events[-1].hand_path
            if last_path:
                return (last_path[-1][0], last_path[-1][1], False)
            return (self.canvas_width / 2.0, self.canvas_height / 2.0, False)

        active_ev = self.get_active_event_at(t)
        if active_ev is not None and active_ev.hand_path:
            ev_dur = max(0.001, active_ev.end_time - active_ev.start_time)
            progress = max(0.0, min(1.0, (t - active_ev.start_time) / ev_dur))
            path_len = len(active_ev.hand_path)
            idx = min(int(progress * path_len), path_len - 1)
            pt = active_ev.hand_path[idx]
            is_drawing = (active_ev.action == "draw")
            return (pt[0], pt[1], is_drawing)

        # Nếu rơi vào khoảng nghỉ giữa các sự kiện
        # Tìm sự kiện gần nhất trước t
        prev_ev = None
        for ev in self.events:
            if ev.end_time <= t:
                prev_ev = ev
            elif ev.start_time > t:
                break
        if prev_ev and prev_ev.hand_path:
            return (prev_ev.hand_path[-1][0], prev_ev.hand_path[-1][1], False)

        return (self.canvas_width / 2.0, self.canvas_height / 2.0, False)
