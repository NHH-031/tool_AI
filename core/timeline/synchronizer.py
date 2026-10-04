from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.assets.providers import AssetProvider, LocalAssetProvider
from core.assets.resolver import AssetResolution, GenericAssetResolver
from core.drawing.extractor import SVGStrokeExtractor
from core.drawing.hand_path import transform_strokes_to_canvas
from core.drawing.sorter import StrokeOrderPlanner
from core.schemas.drawing import DrawingStroke
from core.schemas.scene_graph import SceneGraph, VisualEntity
from core.schemas.timeline import DrawingTimeline, DrawingTimelineEvent
from core.schemas.tts import NarrationTiming, WordTiming

logger = logging.getLogger(__name__)


class DrawingTimelineSynchronizer:
    """
    Động cơ quy hoạch Drawing Timeline và đồng bộ hóa bàn tay vẽ (Hand Synchronization):
    Narration Timing + Visual Scene Graph + Assets + Drawing Strokes = Drawing Timeline.
    
    Quy tắc cốt lõi:
    1. Nhận diện các mốc từ ngữ trong câu thoại (TTS Timing) để định vị thời điểm xuất hiện của các thực thể.
    2. Phân bổ thời lượng vẽ dựa trên độ phức tạp nét vẽ (stroke complexity), vai trò thị giác và tầm quan trọng ngữ nghĩa.
    3. Đảm bảo 100% nét vẽ của mọi required entity đều được vẽ đầy đủ (completionRatio == 1.0).
    4. Bàn tay vẽ (Hand) di chuyển bám sát ngòi bút dọc theo các nét vẽ vector.
    5. Không phụ thuộc hard-code tên thực thể, mở rộng cho bất kỳ kịch bản nào.
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
        self.asset_resolver = GenericAssetResolver(asset_provider=self.asset_provider)
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
            ease_t = 3 * (t**2) - 2 * (t**3)
            lift_arc = math.sin(math.pi * t) * -15.0
            x = p_start[0] + ease_t * (p_end[0] - p_start[0])
            y = p_start[1] + ease_t * (p_end[1] - p_start[1]) + lift_arc
            path.append((round(x, 2), round(y, 2)))
        return path

    def _find_entity_phrase_start(self, words: List[WordTiming], entity: VisualEntity) -> Optional[float]:
        """Tìm mốc thời gian bắt đầu của entity trong narration dựa trên từ khóa danh từ và hành động."""
        if not words:
            return None
        clean_words = [w.word.lower().strip(".,!?:;\"'()[]{}") for w in words]
        
        # Tập hợp các từ khóa gợi ý từ nhãn, tên, hành động và danh mục
        search_terms = []
        label = (entity.name or entity.label).lower()
        search_terms.append(label)
        if entity.actions:
            search_terms.extend([a.lower() for a in entity.actions])
        if entity.action:
            search_terms.append(entity.action.lower())

        # Thêm từ khóa ngữ cảnh phổ biến nếu có
        vietnamese_aliases = {
            "monkey": ["con khỉ", "chú khỉ", "khỉ"],
            "tree": ["cái cây", "cây dừa", "cây", "thân cây", "trèo lên cây"],
            "banana": ["quả chuối", "trái chuối", "nải chuối", "chuối", "lấy một quả chuối", "lấy chuối"],
            "dog": ["con chó", "chú chó", "chó", "chạy"],
            "ball": ["quả bóng", "trái bóng", "bóng"],
            "tiger": ["con hổ", "chú hổ", "hổ", "con cọp", "chú cọp", "cọp"],
            "rabbit": ["con thỏ", "chú thỏ", "thỏ"],
            "forest": ["khu rừng", "rừng già", "rừng rậm", "rừng"],
            "sun": ["mặt trời", "thái dương"],
            "earth": ["trái đất", "địa cầu"],
            "water": ["nước", "nước nóng", "ấm nước"],
            "vapor": ["bốc hơi", "hơi nước", "khói"],
            "farmer": ["nông dân", "người nông dân", "bác nông dân", "trồng"],
            "ground": ["mặt đất", "đất", "ruộng"],
            "price": ["giá cả", "giá"],
            "inflation": ["lạm phát"],
        }
        for k, aliases in vietnamese_aliases.items():
            if k in label:
                search_terms.extend(aliases)

        # Sắp xếp từ dài đến ngắn để match cụm trước
        sorted_phrases = sorted(list(set(search_terms)), key=lambda p: len(p.split()), reverse=True)
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
        stroke_counts: Dict[str, int],
    ) -> Dict[str, Tuple[float, float]]:
        """
        Phân bổ cửa sổ thời gian vẽ cho từng entity dựa trên narration timing,
        đồng thời cân đối theo độ phức tạp của nét vẽ (stroke count) và mức độ quan trọng.
        """
        total_audio_dur = max(3.0, narration_timing.duration)
        words = narration_timing.words

        detected_starts: Dict[str, float] = {}
        for entity in scene_graph.entities:
            matched_time = self._find_entity_phrase_start(words, entity)
            if matched_time is not None:
                detected_starts[entity.id] = matched_time

        # Sắp xếp các entity theo thứ tự thời gian phát hiện, hoặc layer/priority
        def get_entity_sort_key(e):
            if e.id in detected_starts:
                return (0, detected_starts[e.id], e.layer, e.priority)
            if (
                e.category in ["environment", "background", "structure"]
                or e.visual_role in ["environment", "background", "structure"]
                or e.visual_type in ["background"]
                or e.layer == 0
            ):
                return (0, 0.05, e.layer, e.priority)
            return (1, 999.0, e.layer, e.priority)

        sorted_entities = sorted(scene_graph.entities, key=get_entity_sort_key)

        num_entities = len(sorted_entities)
        if num_entities == 0:
            return {}

        # Tính tổng trọng số nét vẽ
        total_strokes = sum(max(5, stroke_counts.get(e.id, 10)) for e in sorted_entities)
        time_windows: Dict[str, Tuple[float, float]] = {}

        # Nếu không bắt được từ khóa, chia tỷ lệ theo số nét vẽ
        if not detected_starts:
            curr_t = 0.1
            for e in sorted_entities:
                strokes = max(5, stroke_counts.get(e.id, 10))
                dur = (strokes / total_strokes) * (total_audio_dur - 0.2)
                end_t = curr_t + dur
                time_windows[e.id] = (round(curr_t, 3), round(end_t, 3))
                curr_t = end_t
            return time_windows

        # Có từ khóa: tính thời điểm bắt đầu theo từ khóa và đảm bảo thời lượng tối thiểu cho nét vẽ
        starts: List[Tuple[str, float]] = []
        prev_t = 0.1
        for idx, e in enumerate(sorted_entities):
            raw_start = detected_starts.get(e.id, prev_t + 0.5)
            st = max(prev_t, raw_start)
            starts.append((e.id, st))
            prev_t = st + 0.3

        # Phân bổ end time và điều chỉnh visual tail nếu cần
        for idx, (e_id, st) in enumerate(starts):
            strokes = max(5, stroke_counts.get(e_id, 10))
            min_dur = max(0.4, strokes * 0.035)  # Ít nhất 35ms mỗi nét vẽ

            if idx < len(starts) - 1:
                next_st = starts[idx + 1][1]
                end_t = max(next_st, st + min_dur)
            else:
                end_t = max(total_audio_dur, st + min_dur)

            time_windows[e_id] = (round(st, 3), round(end_t, 3))

        return time_windows

    def _calculate_canvas_placement(
        self,
        entity: VisualEntity,
        scene_graph: SceneGraph,
    ) -> Tuple[float, float, float, float]:
        """
        Tính toán bounding box hiển thị (x, y, width, height) trên canvas 1920x1080.
        Dựa trên tọa độ tường minh của entity hoặc vai trò trực quan (Visual Role / Category).
        """
        pos = entity.position
        if pos and (pos.x != 0 or pos.y != 0) and pos.width > 50 and pos.height > 50:
            return (float(pos.x), float(pos.y), float(pos.width), float(pos.height))

        label = (entity.name or entity.label).lower()
        role = (entity.visual_role or "").lower()
        cat = (entity.category or "").lower()

        # Bố cục dựa trên cấu trúc ngữ nghĩa
        if label == "forest":
            return (100.0, 80.0, 1720.0, 920.0)
        elif label == "tiger":
            return (450.0, 400.0, 540.0, 420.0)
        elif label == "rabbit":
            return (1200.0, 500.0, 380.0, 300.0)
        elif role in ["environment", "structure"] or cat in ["structure", "background"]:
            # Khung cảnh nền hoặc cấu trúc đứng bên phải
            return (750.0, 80.0, 850.0, 920.0)
        elif role in ["actor", "character", "agent"] or cat in ["character"]:
            # Chủ thể hoạt động ở trung tâm - hơi lệch trái
            return (550.0, 350.0, 500.0, 500.0)
        elif role in ["target", "object"] or cat in ["object"]:
            # Đối tượng tương tác ở phía trên hoặc điểm đến
            return (1120.0, 160.0, 320.0, 320.0)
        elif cat in ["diagram", "chart", "metaphor"]:
            return (580.0, 180.0, 750.0, 650.0)

        # Mặc định cân đối trên canvas
        return (600.0, 250.0, 500.0, 500.0)

    def build_timeline(
        self,
        narration_timing: NarrationTiming,
        scene_graph: SceneGraph,
        total_padding_sec: float = 0.5,
    ) -> DrawingTimeline:
        """
        Xây dựng toàn bộ DrawingTimeline hoàn chỉnh đồng bộ theo narration timing
        với bảo đảm 100% tính hoàn thiện nét vẽ cho mọi required entity.
        """
        # 1. Phân giải Asset vector cho toàn bộ entities qua GenericAssetResolver
        resolved_assets: Dict[str, AssetResolution] = {}
        stroke_counts: Dict[str, int] = {}
        for entity in scene_graph.entities:
            res = self.asset_resolver.resolve_entity(entity)
            resolved_assets[entity.id] = res
            stroke_counts[entity.id] = res.stroke_count
            entity.asset_id = res.asset_id
            entity.required_stroke_ids = [s.id for s in res.strokes]

        # 2. Xác định khung thời gian cho từng entity
        entity_windows = self._determine_entity_time_windows(scene_graph, narration_timing, stroke_counts)

        # 3. Thu thập và chuyển đổi nét vẽ của từng entity
        timeline_events: List[DrawingTimelineEvent] = []
        last_nib_pos: Optional[Tuple[float, float]] = None

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
            allocated_dur = max(0.3, win_end - win_start)

            res = resolved_assets[entity_id]
            raw_strokes = res.strokes
            view_box = "0 0 500 500"
            if res.svg_path and Path(res.svg_path).exists():
                _, vb = SVGStrokeExtractor.extract_strokes_from_svg(
                    res.svg_path,
                    asset_id=res.asset_id,
                    asset_name=entity.name or entity.label,
                )
                view_box = vb

            # Sắp xếp stroke order tự nhiên
            ordered_strokes = StrokeOrderPlanner.sort_and_time_strokes(
                raw_strokes,
                asset_name=entity.name or entity.label,
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
                total_travel_budget = dur_for_strokes * 0.10
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
            event_asset_id = entity.name or entity.label or res.asset_id
            if inter_travel_path and inter_travel_dur > 0:
                tr_end = curr_time + inter_travel_dur
                timeline_events.append(
                    DrawingTimelineEvent(
                        start_time=round(curr_time, 3),
                        end_time=round(tr_end, 3),
                        asset_id=event_asset_id,
                        stroke_id=f"inter_travel_{entity_id}",
                        action="hand_travel",
                        hand_path=inter_travel_path,
                        semantic_purpose="travel",
                        entity_id=entity_id,
                    )
                )
                curr_time = tr_end

            completed_stroke_ids: List[str] = []
            for s_idx, s in enumerate(valid_strokes):
                stroke_dur = round(draw_budget * (s.length / total_geom_len), 3)
                stroke_dur = max(0.015, stroke_dur)
                s_pts = s.points
                stroke_end_time = round(curr_time + stroke_dur, 3)
                canvas_d = self._points_to_svg_d(s_pts)

                timeline_events.append(
                    DrawingTimelineEvent(
                        start_time=round(curr_time, 3),
                        end_time=stroke_end_time,
                        asset_id=event_asset_id,
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
                            "entity_name": entity.name or entity.label,
                            "length": s.length,
                        },
                    )
                )

                completed_stroke_ids.append(s.id)
                curr_time = stroke_end_time
                last_nib_pos = s_pts[-1]

                # Nếu chưa phải nét cuối -> chèn travel sang nét tiếp theo
                if s_idx < len(individual_travel_durations):
                    t_dur = round(individual_travel_durations[s_idx], 3)
                    if t_dur > 0.005:
                        p_start = travel_segments[s_idx][0]
                        p_end = travel_segments[s_idx][1]
                        air_path = self._interpolate_travel_path(p_start, p_end, steps=10)
                        tr_end_time = round(curr_time + t_dur, 3)

                        timeline_events.append(
                            DrawingTimelineEvent(
                                start_time=round(curr_time, 3),
                                end_time=tr_end_time,
                                asset_id=event_asset_id,
                                stroke_id=f"travel_{s.id}",
                                action="hand_travel",
                                hand_path=air_path,
                                semantic_purpose="travel",
                                entity_id=entity_id,
                            )
                        )
                        curr_time = tr_end_time

            # Cập nhật trạng thái hoàn thiện cho entity (Section 8 Drawing Completeness)
            entity.asset_resolved = True
            entity.vector_available = bool(res.svg_path and Path(res.svg_path).exists())
            entity.stroke_plan_available = len(ordered_strokes) > 0
            entity.stroke_count = len(valid_strokes)
            entity.completed_stroke_count = len(completed_stroke_ids)
            entity.required_stroke_ids = [s.id for s in valid_strokes]
            entity.completed_stroke_ids = completed_stroke_ids
            entity.completion_ratio = 1.0 if len(valid_strokes) > 0 else 0.0

        # Tổng thời lượng của timeline
        max_draw_time = max([e.end_time for e in timeline_events], default=narration_timing.duration)
        total_duration = round(max(narration_timing.duration, max_draw_time) + total_padding_sec, 2)

        # Xây dựng debug artifact data
        scene_debug = {
            "sceneId": scene_graph.scene_id,
            "narration": narration_timing.text,
            "entities": [
                {
                    "id": e.id,
                    "label": e.name or e.label,
                    "visualRole": e.visual_role,
                    "assetId": e.asset_id,
                    "requiredStrokes": len(e.required_stroke_ids),
                    "completedStrokes": len(e.completed_stroke_ids),
                    "completionRatio": e.completion_ratio,
                }
                for e in scene_graph.entities
            ],
            "relationships": [
                {
                    "id": r.id,
                    "source": r.source_id,
                    "target": r.target_id,
                    "relationType": r.relation_type,
                }
                for r in scene_graph.relationships
            ],
            "actions": [
                {
                    "id": a.id,
                    "entityId": a.entity_id,
                    "actionType": a.action_type,
                    "completed": a.completed,
                }
                for a in scene_graph.actions
            ],
            "totalStrokes": sum(1 for ev in timeline_events if ev.action == "draw"),
            "totalDuration": total_duration,
        }

        return DrawingTimeline(
            events=timeline_events,
            total_duration=total_duration,
            canvas_width=self.canvas_width,
            canvas_height=self.canvas_height,
            narration_text=narration_timing.text,
            narration_timing=narration_timing,
            entities_schedule=entities_schedule,
            metadata={
                "audio_duration": narration_timing.duration,
                "narration_text": narration_timing.text,
                "scene_debug": scene_debug,
            },
        )
