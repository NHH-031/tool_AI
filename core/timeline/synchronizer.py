from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.assets.providers import AssetProvider, LocalAssetProvider
from core.drawing.extractor import SVGStrokeExtractor
from core.drawing.hand_path import transform_strokes_to_canvas
from core.drawing.sorter import StrokeOrderPlanner
from core.schemas.drawing import DrawingStroke
from core.schemas.scene_graph import SceneGraph, VisualEntity
from core.schemas.timeline import DrawingTimeline, DrawingTimelineEvent
from core.schemas.tts import NarrationTiming, WordTiming


class DrawingTimelineSynchronizer:
    """
    Động cơ quy hoạch Drawing Timeline và đồng bộ hóa bàn tay vẽ (Hand Synchronization):
    Narration Timing + Visual Scene Graph + Assets + Drawing Strokes = Drawing Timeline.
    
    Quy tắc bắt buộc:
    1. Bắt đầu bằng âm thanh câu thoại ("Con khỉ...") -> monkey bắt đầu được vẽ.
    2. Cụm từ hành động ("...đang trèo lên cây...") -> thân cây và tư thế leo bám xuất hiện.
    3. Cụm từ tương tác ("...để lấy một quả chuối...") -> nải chuối xuất hiện và tay với chuối hoàn tất.
    4. Timing được co giãn động theo thời lượng thực tế của file âm thanh (TTS Timing).
    5. Bàn tay vẽ (Hand) di chuyển bám sát ngòi bút dọc theo nét vẽ đang hoạt động.
    """

    DEFAULT_CANVAS_WIDTH = 1920
    DEFAULT_CANVAS_HEIGHT = 1080

    def __init__(
        self,
        asset_provider: Optional[AssetProvider] = None,
        canvas_width: int = DEFAULT_CANVAS_WIDTH,
        canvas_height: int = DEFAULT_CANVAS_HEIGHT,
    ):
        self.asset_provider = asset_provider or LocalAssetProvider()
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height

    def _points_to_svg_d(self, points: List[Tuple[float, float]]) -> str:
        """Chuyển đổi danh sách điểm polyline thành chuỗi SVG path d chuẩn."""
        if not points:
            return ""
        d_parts = [f"M {points[0][0]:.2f} {points[0][1]:.2f}"]
        for pt in points[1:]:
            d_parts.append(f"L {pt[0]:.2f} {pt[1]:.2f}")
        return " ".join(d_parts)

    def _interpolate_travel_path(
        self,
        p_start: Tuple[float, float],
        p_end: Tuple[float, float],
        steps: int = 15,
    ) -> List[Tuple[float, float]]:
        """Tạo đường đi trên không mượt mà (smooth ease in-out) giữa 2 điểm nét vẽ."""
        path: List[Tuple[float, float]] = []
        for i in range(steps + 1):
            t = i / steps
            # Smooth cubic ease in-out curve
            ease_t = 3 * (t**2) - 2 * (t**3)
            # Thêm một chút độ cong tự nhiên của cổ tay khi nhấc bút
            lift_arc = math.sin(math.pi * t) * -15.0
            x = p_start[0] + ease_t * (p_end[0] - p_start[0])
            y = p_start[1] + ease_t * (p_end[1] - p_start[1]) + lift_arc
            path.append((round(x, 2), round(y, 2)))
        return path

    def _find_phrase_start(self, words: List[WordTiming], phrases: List[str]) -> Optional[float]:
        """Tìm mốc thời gian bắt đầu của cụm từ hoặc từ khóa trong danh sách WordTiming."""
        if not words:
            return None
        clean_words = [w.word.lower().strip(".,!?:;\"'()[]{}") for w in words]
        sorted_phrases = sorted(phrases, key=lambda p: len(p.split()), reverse=True)
        for phrase in sorted_phrases:
            p_parts = phrase.lower().split()
            p_len = len(p_parts)
            for i in range(len(clean_words) - p_len + 1):
                if clean_words[i:i + p_len] == p_parts:
                    return words[i].start_time
                if p_len == 1 and p_parts[0] in clean_words[i]:
                    return words[i].start_time
        return None

    def _determine_entity_time_windows(
        self,
        scene_graph: SceneGraph,
        narration_timing: NarrationTiming,
    ) -> Dict[str, Tuple[float, float]]:
        """
        Phân bổ cửa sổ thời gian vẽ cho từng entity dựa trên các mốc từ ngữ trong narration timing.
        """
        total_audio_dur = max(2.0, narration_timing.duration)
        words = narration_timing.words

        # Bảng tra cụm từ khóa cho demo monkey-banana-tree
        entity_phrases = {
            "monkey": ["con khỉ", "chú khỉ", "khỉ", "monkey"],
            "tree": ["trèo lên cây", "trèo cây", "trèo", "cây dừa", "cây", "tree", "climb"],
            "banana": ["lấy một quả chuối", "lấy chuối", "quả chuối", "nải chuối", "lấy", "chuối", "banana"],
        }

        # Tìm từ khóa/cụm từ xuất hiện sớm nhất trong narration cho từng entity
        detected_starts: Dict[str, float] = {}

        for entity in scene_graph.entities:
            e_name = entity.name.lower()
            phrases = entity_phrases.get(e_name, [e_name])
            matched_time = self._find_phrase_start(words, phrases)
            if matched_time is not None:
                detected_starts[entity.id] = matched_time

        # Sắp xếp các entity theo thứ tự thời gian xuất hiện
        sorted_entities = sorted(
            scene_graph.entities,
            key=lambda e: detected_starts.get(e.id, 999.0)
        )

        time_windows: Dict[str, Tuple[float, float]] = {}
        num_entities = len(sorted_entities)

        if not detected_starts:
            dur_per_entity = total_audio_dur / max(1, num_entities)
            for idx, e in enumerate(sorted_entities):
                s_t = idx * dur_per_entity
                e_t = (idx + 1) * dur_per_entity
                time_windows[e.id] = (round(s_t, 3), round(e_t, 3))
        else:
            entity_starts: List[Tuple[str, float]] = []
            prev_t = 0.0
            for idx, e in enumerate(sorted_entities):
                st = detected_starts.get(e.id, prev_t + (total_audio_dur / num_entities))
                st = max(prev_t, st)
                entity_starts.append((e.id, st))
                prev_t = st

            for idx, (e_id, st) in enumerate(entity_starts):
                if idx < len(entity_starts) - 1:
                    next_st = entity_starts[idx + 1][1]
                    end_t = next_st
                else:
                    end_t = total_audio_dur
                time_windows[e_id] = (round(st, 3), round(end_t, 3))

        return time_windows

    def _calculate_canvas_placement(
        self,
        entity: VisualEntity,
        scene_graph: SceneGraph,
    ) -> Tuple[float, float, float, float]:
        """
        Tính toán bounding box hiển thị (x, y, width, height) trên canvas 1920x1080.
        Đảm bảo đúng quan hệ không gian:
        - tree: thân cây đứng bên phải
        - monkey: bám trực tiếp trên thân cây
        - banana: treo trên tán cây nơi tay khỉ với tới
        """
        e_name = entity.name.lower()

        pos = entity.position
        if pos and (pos.x != 0 or pos.y != 0) and pos.width > 50 and pos.height > 50:
            return (float(pos.x), float(pos.y), float(pos.width), float(pos.height))

        # Bố cục chuẩn cho bộ 3 Monkey - Tree - Banana
        if "tree" in e_name:
            # Cây dừa cao bên phải canvas
            return (820.0, 80.0, 720.0, 880.0)
        elif "monkey" in e_name:
            # Khỉ leo trên thân cây (vừa vặn bám vào thân dừa ở X=1140)
            return (720.0, 400.0, 440.0, 440.0)
        elif "banana" in e_name:
            # Nải chuối treo ở tán lá trên ngọn cây, ngay phía trên tay khỉ
            return (1120.0, 180.0, 240.0, 240.0)

        # Mặc định căn giữa
        return (600.0, 250.0, 500.0, 500.0)

    def build_timeline(
        self,
        narration_timing: NarrationTiming,
        scene_graph: SceneGraph,
        total_padding_sec: float = 0.5,
    ) -> DrawingTimeline:
        """
        Xây dựng toàn bộ DrawingTimeline hoàn chỉnh đồng bộ theo narration timing.
        """
        # 1. Xác định khung thời gian cho từng entity
        entity_windows = self._determine_entity_time_windows(scene_graph, narration_timing)

        # 2. Thu thập và chuyển đổi nét vẽ của từng entity
        timeline_events: List[DrawingTimelineEvent] = []
        last_nib_pos: Optional[Tuple[float, float]] = None

        # Sắp xếp các entity theo thời gian bắt đầu
        ordered_entity_items = sorted(
            entity_windows.items(),
            key=lambda item: item[1][0]
        )

        entities_schedule: Dict[str, Tuple[float, float]] = {}

        for entity_idx, (entity_id, (win_start, win_end)) in enumerate(ordered_entity_items):
            entity = scene_graph.get_entity(entity_id)
            if not entity:
                continue

            entities_schedule[entity_id] = (win_start, win_end)
            allocated_dur = max(0.2, win_end - win_start)

            pose_action = entity.action or "standing"
            svg_path = None
            asset_id = entity.name

            if hasattr(self.asset_provider, "lookup_sync"):
                lookup_res = self.asset_provider.lookup_sync(entity.name, action=pose_action)
                if lookup_res.found and lookup_res.resolved_path:
                    svg_path = Path(lookup_res.resolved_path)
                    asset_id = lookup_res.asset.id if lookup_res.asset else entity.name

            if not svg_path or not svg_path.exists():
                # Fallback trực tiếp tới thư mục assets/library/svg
                if "monkey" in entity.name:
                    svg_path = Path(
                        "assets/library/svg/monkey_climbing.svg"
                        if "climb" in pose_action.lower()
                        else "assets/library/svg/monkey_standing.svg"
                    )
                elif "tree" in entity.name:
                    svg_path = Path("assets/library/svg/tree_palm.svg")
                elif "banana" in entity.name:
                    svg_path = Path("assets/library/svg/banana_bunch.svg")
                else:
                    svg_path = Path(f"assets/library/svg/{entity.name}.svg")

            # Đọc SVG và trích xuất strokes
            raw_strokes, view_box = SVGStrokeExtractor.extract_strokes_from_svg(
                svg_path,
                asset_id=asset_id,
                asset_name=entity.name,
            )

            # Sắp xếp stroke order tự nhiên
            ordered_strokes = StrokeOrderPlanner.sort_and_time_strokes(
                raw_strokes,
                asset_name=entity.name,
                total_duration_sec=allocated_dur,
            )

            # Tính tọa độ hiển thị trên canvas
            tx, ty, tw, th = self._calculate_canvas_placement(entity, scene_graph)

            # Chuyển đổi tọa độ nét vẽ sang canvas
            canvas_strokes = transform_strokes_to_canvas(
                strokes=ordered_strokes,
                view_box=view_box,
                target_x=tx,
                target_y=ty,
                target_width=tw,
                target_height=th,
            )

            # Lọc các stroke có điểm hợp lệ
            valid_strokes = [s for s in canvas_strokes if s.points and len(s.points) >= 2]
            num_strokes = len(valid_strokes)
            if num_strokes == 0:
                continue

            # Di chuyển tay từ entity trước tới entity hiện tại nếu có
            inter_travel_dur = 0.0
            inter_travel_path = None
            if last_nib_pos is not None:
                first_pt = valid_strokes[0].points[0]
                dist = math.hypot(first_pt[0] - last_nib_pos[0], first_pt[1] - last_nib_pos[1])
                if dist > 5.0:
                    inter_travel_dur = min(0.06, allocated_dur * 0.08)
                    inter_travel_path = self._interpolate_travel_path(last_nib_pos, first_pt)

            dur_for_strokes = max(0.1, allocated_dur - inter_travel_dur)

            # Tính toán các đoạn di chuyển giữa các nét vẽ trong cùng entity
            travel_segments = []
            for idx in range(num_strokes - 1):
                p1 = valid_strokes[idx].points[-1]
                p2 = valid_strokes[idx + 1].points[0]
                dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
                travel_segments.append((p1, p2, dist))

            if travel_segments:
                # 12% thời lượng cho di chuyển nội bộ, 88% cho vẽ nét
                total_travel_budget = dur_for_strokes * 0.12
                total_dist = sum(ts[2] for ts in travel_segments)
                if total_dist <= 0:
                    total_dist = 1.0
                individual_travel_durations = [
                    (ts[2] / total_dist) * total_travel_budget
                    for ts in travel_segments
                ]
            else:
                total_travel_budget = 0.0
                individual_travel_durations = []

            draw_budget = dur_for_strokes - total_travel_budget
            total_geom_len = sum(s.length for s in valid_strokes)
            if total_geom_len <= 0:
                total_geom_len = 1.0

            curr_time = win_start

            # Emit inter-entity travel event nếu có
            if inter_travel_path and inter_travel_dur > 0:
                tr_end = curr_time + inter_travel_dur
                timeline_events.append(
                    DrawingTimelineEvent(
                        start_time=round(curr_time, 3),
                        end_time=round(tr_end, 3),
                        asset_id=entity.name,
                        stroke_id=f"inter_travel_{entity_id}",
                        action="hand_travel",
                        hand_path=inter_travel_path,
                        semantic_purpose="travel",
                        entity_id=entity_id,
                    )
                )
                curr_time = tr_end

            for s_idx, s in enumerate(valid_strokes):
                stroke_dur = round(draw_budget * (s.length / total_geom_len), 3)
                s_pts = s.points
                stroke_end_time = round(curr_time + stroke_dur, 3)
                canvas_d = self._points_to_svg_d(s_pts)

                timeline_events.append(
                    DrawingTimelineEvent(
                        start_time=round(curr_time, 3),
                        end_time=stroke_end_time,
                        asset_id=entity.name,
                        stroke_id=s.id,
                        action="draw",
                        hand_path=s_pts,
                        semantic_purpose=s.semantic_purpose,
                        stroke_d=canvas_d,
                        stroke_width=s.stroke_width,
                        color_hex=s.color_hex,
                        entity_id=entity_id,
                        points=s_pts,
                        metadata={
                            "entity_name": entity.name,
                            "length": s.length,
                        },
                    )
                )

                curr_time = stroke_end_time
                last_nib_pos = s_pts[-1]

                # Nếu chưa phải nét cuối -> chèn travel sang nét tiếp theo
                if s_idx < len(individual_travel_durations):
                    tr_dur = round(individual_travel_durations[s_idx], 3)
                    p_start, p_end, _ = travel_segments[s_idx]
                    tr_path = self._interpolate_travel_path(p_start, p_end)
                    timeline_events.append(
                        DrawingTimelineEvent(
                            start_time=round(curr_time, 3),
                            end_time=round(curr_time + tr_dur, 3),
                            asset_id=entity.name,
                            stroke_id=f"travel_{entity_id}_{s.id}",
                            action="hand_travel",
                            hand_path=tr_path,
                            semantic_purpose="travel",
                            entity_id=entity_id,
                        )
                    )
                    curr_time = round(curr_time + tr_dur, 3)

        # Sắp xếp các sự kiện theo thời gian bắt đầu đơn điệu
        timeline_events.sort(key=lambda ev: (ev.start_time, ev.end_time))

        total_timeline_dur = (
            timeline_events[-1].end_time + total_padding_sec
            if timeline_events
            else narration_timing.duration + total_padding_sec
        )

        return DrawingTimeline(
            events=timeline_events,
            total_duration=round(total_timeline_dur, 3),
            canvas_width=self.canvas_width,
            canvas_height=self.canvas_height,
            narration_text=narration_timing.text,
            narration_timing=narration_timing,
            entities_schedule=entities_schedule,
            metadata={
                "synchronizer": "DrawingTimelineSynchronizer",
                "scene_id": scene_graph.scene_id,
                "total_events": len(timeline_events),
                "total_strokes": sum(1 for e in timeline_events if e.action == "draw"),
            },
        )
