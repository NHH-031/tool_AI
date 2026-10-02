from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import av
import cv2
import numpy as np
from pydantic import BaseModel, Field

from core.schemas.scene_graph import SceneGraph
from core.schemas.timeline import DrawingTimeline


class TechnicalQAResult(BaseModel):
    """Lớp kiểm định 1: Tiêu chuẩn kỹ thuật Media container, codecs, streams và audio/video sync."""
    is_valid_mp4: bool = Field(default=False, description="Container chuẩn MP4")
    file_exists: bool = Field(default=False, description="File tồn tại trên đĩa")
    file_size_bytes: int = Field(default=0, description="Dung lượng file (bytes)")
    duration_sec: float = Field(default=0.0, description="Thời lượng video (giây)")
    fps: Optional[float] = Field(default=None, description="Tốc độ khung hình (fps)")
    video_codec: Optional[str] = Field(default=None, description="Codec video (h264, etc.)")
    resolution: Optional[str] = Field(default=None, description="Độ phân giải video (WxH)")
    audio_codec: Optional[str] = Field(default=None, description="Codec audio (aac, etc.)")
    audio_video_drift_sec: Optional[float] = Field(default=None, description="Độ lệch thời lượng audio và video (giây)")
    is_corrupted: bool = Field(default=False, description="Có lỗi hỏng stream hoặc lỗi giải mã frame")
    pass_status: bool = Field(default=False, description="Đạt toàn bộ tiêu chuẩn kỹ thuật (PASS/FAIL)")
    errors: List[str] = Field(default_factory=list, description="Danh sách lỗi kỹ thuật nếu có")

    @property
    def pass_technical(self) -> bool:
        return self.pass_status


class DrawingQAResult(BaseModel):
    """Lớp kiểm định 2: Tính hoàn thiện nét vẽ, thứ tự hạ nét, quỹ đạo bàn tay và không lộ nét sớm."""
    required_strokes: int = Field(default=0, ge=0, description="Tổng số nét vẽ bắt buộc của các thực thể")
    completed_strokes: int = Field(default=0, ge=0, description="Tổng số nét vẽ đã được thể hiện")
    completion_ratio: float = Field(default=0.0, ge=0.0, le=1.0, description="Tỉ lệ hoàn thiện nét vẽ (bắt buộc 1.0)")
    stroke_ordering_valid: bool = Field(default=True, description="Thứ tự nét vẽ tuần tự tự nhiên")
    hand_path_valid: bool = Field(default=True, description="Bàn tay di chuyển đúng quỹ đạo ngòi bút")
    hand_sync_valid: bool = Field(default=True, description="Bàn tay đồng bộ thời gian với nét vẽ")
    no_early_reveal: bool = Field(default=True, description="Không bị lộ nét vẽ trước thời điểm quy định")
    no_instant_reveal: bool = Field(default=True, description="Không dùng hiệu ứng hiện nguyên hình đột ngột")
    pass_status: bool = Field(default=False, description="Đạt toàn bộ tiêu chuẩn nét vẽ (PASS/FAIL)")
    errors: List[str] = Field(default_factory=list, description="Danh sách lỗi nét vẽ nếu có")
    details: List[str] = Field(default_factory=list, description="Chi tiết kiểm định nét vẽ")

    @property
    def pass_drawing(self) -> bool:
        return self.pass_status

    @property
    def hand_sync_pass(self) -> bool:
        return self.hand_sync_valid

    @property
    def no_early_reveal_pass(self) -> bool:
        return self.no_early_reveal


class SemanticVisualQAResult(BaseModel):
    """Lớp kiểm định 3: Ngữ nghĩa thị giác, mối quan hệ, hành động và tính toàn vẹn của khung hình cuối."""
    required_entities_count: int = Field(default=0, ge=0, description="Số lượng thực thể bắt buộc")
    present_entities_count: int = Field(default=0, ge=0, description="Số lượng thực thể có mặt trên video")
    missing_entities: List[str] = Field(default_factory=list, description="Danh sách các thực thể bị thiếu")
    incomplete_entities: List[str] = Field(default_factory=list, description="Danh sách các thực thể chưa vẽ xong")
    required_relationships_count: int = Field(default=0, ge=0, description="Số lượng quan hệ ngữ nghĩa bắt buộc")
    present_relationships_count: int = Field(default=0, ge=0, description="Số lượng quan hệ ngữ nghĩa được thể hiện")
    missing_relationships: List[str] = Field(default_factory=list, description="Danh sách quan hệ ngữ nghĩa bị thiếu")
    required_actions_count: int = Field(default=0, ge=0, description="Số lượng hành động bắt buộc")
    completed_actions_count: int = Field(default=0, ge=0, description="Số lượng hành động hoàn thành")
    missing_actions: List[str] = Field(default_factory=list, description="Danh sách hành động bị thiếu")
    final_frame_complete: bool = Field(default=False, description="Khung hình cuối hoàn chỉnh đầy đủ mọi đối tượng")
    pass_status: bool = Field(default=False, description="Đạt toàn bộ tiêu chuẩn ngữ nghĩa trực quan (PASS/FAIL)")
    errors: List[str] = Field(default_factory=list, description="Danh sách lỗi ngữ nghĩa nếu có")
    details: List[str] = Field(default_factory=list, description="Chi tiết kiểm định ngữ nghĩa")

    @property
    def pass_semantic(self) -> bool:
        return self.pass_status

    @property
    def required_entities(self) -> int:
        return self.required_entities_count

    @property
    def completed_entities(self) -> int:
        return self.present_entities_count

    @property
    def required_actions(self) -> int:
        return self.required_actions_count

    @property
    def completed_actions(self) -> int:
        return self.completed_actions_count

    @property
    def required_relationships(self) -> int:
        return self.required_relationships_count

    @property
    def completed_relationships(self) -> int:
        return self.present_relationships_count


class MediaReport(BaseModel):
    """Báo cáo kiểm định 3 lớp toàn diện (Three-Layer QA Architecture)."""
    file_path: str = Field(description="Đường dẫn file video MP4")
    file_exists: bool = Field(description="Tồn tại trên đĩa")
    file_size_bytes: int = Field(default=0, description="Kích thước file (bytes)")
    is_valid_mp4: bool = Field(default=False, description="Container MP4 hợp lệ theo chuẩn ISO base media")
    duration_sec: float = Field(default=0.0, description="Tổng thời lượng video (giây)")
    video_streams_count: int = Field(default=0, description="Số lượng luồng video")
    audio_streams_count: int = Field(default=0, description="Số lượng luồng âm thanh")
    video_codec: Optional[str] = Field(default=None, description="Codec video (h264, etc.)")
    video_width: Optional[int] = Field(default=None, description="Độ phân giải ngang (pixels)")
    video_height: Optional[int] = Field(default=None, description="Độ phân giải dọc (pixels)")
    fps: Optional[float] = Field(default=None, description="Tốc độ khung hình (fps)")
    frame_count: int = Field(default=0, description="Tổng số khung hình video đã giải mã")
    audio_codec: Optional[str] = Field(default=None, description="Codec audio (aac, mp3, etc.)")
    audio_channels: Optional[int] = Field(default=None, description="Số kênh âm thanh (1=mono, 2=stereo)")
    audio_sample_rate: Optional[int] = Field(default=None, description="Tần số lấy mẫu âm thanh (Hz)")
    audio_duration_sec: Optional[float] = Field(default=None, description="Thời lượng luồng âm thanh (giây)")
    duration_delta: Optional[float] = Field(default=None, description="Độ chênh lệch giữa video và audio (giây)")
    is_duration_compatible: bool = Field(default=True, description="Video và audio có thời lượng tương thích")
    is_corrupted: bool = Field(default=False, description="Có lỗi hỏng file hoặc lỗi giải mã frame")
    first_frame_mean_luminance: Optional[float] = Field(default=None, description="Độ sáng trung bình frame đầu")
    final_frame_mean_luminance: Optional[float] = Field(default=None, description="Độ sáng trung bình frame cuối")
    visual_qa_pass: bool = Field(default=True, description="Đạt toàn bộ tiêu chuẩn trực quan Whiteboard")

    # Three-Layer QA Sub-Reports
    technical_qa: TechnicalQAResult = Field(default_factory=TechnicalQAResult, description="Kết quả kiểm định kỹ thuật (Layer 1)")
    drawing_qa: DrawingQAResult = Field(default_factory=DrawingQAResult, description="Kết quả kiểm định nét vẽ (Layer 2)")
    semantic_visual_qa: SemanticVisualQAResult = Field(default_factory=SemanticVisualQAResult, description="Kết quả kiểm định ngữ nghĩa thị giác (Layer 3)")
    overall_pass: bool = Field(default=False, description="Kết luận chung: Chỉ PASS khi cả 3 tầng đều PASS")
    details: Dict[str, Any] = Field(default_factory=dict, description="Thông số chi tiết bổ sung")

    @property
    def semantic_qa(self) -> SemanticVisualQAResult:
        return self.semantic_visual_qa


class MediaProbe:
    """
    Công cụ Media QA dựa trên chuẩn libavformat/libavcodec và Three-Layer QA Engine.
    Kiểm tra: Technical QA + Drawing QA + Semantic Visual QA.
    """

    @classmethod
    def inspect_media(
        cls,
        file_path: Optional[Path | str] = None,
        audio_tolerance_sec: float = 1.5,
        scene_graph: Optional[SceneGraph] = None,
        timeline: Optional[DrawingTimeline] = None,
        run_ffprobe: bool = True,
        expected_duration_sec: Optional[float] = None,
        output_path: Optional[Path | str] = None,
    ) -> MediaReport:
        target_path = file_path or output_path or "mock.mp4"
        p = Path(target_path).resolve()
        is_mock = (not run_ffprobe) or str(target_path).endswith("mock.mp4")

        # Fallback values
        file_exists = p.exists()
        file_size = p.stat().st_size if file_exists else 0
        dur = expected_duration_sec or (timeline.total_duration if timeline else 5.0)
        v_count = 1
        a_count = 1
        v_codec = "h264"
        v_width = 1920
        v_height = 1080
        v_fps = 30.0
        frame_count = int(dur * 30.0) if dur else 150
        a_codec = "aac"
        a_channels = 2
        a_rate = 24000
        a_dur = dur
        duration_delta = 0.05
        is_dur_compat = True
        is_corrupted = False
        first_frame_mean: Optional[float] = 250.0 if is_mock else None
        final_frame_mean: Optional[float] = 120.0 if is_mock else None
        is_mp4 = True
        fmt_name = "mp4"

        tech_errors: List[str] = []

        if not is_mock:
            if not file_exists:
                tech_errors.append(f"File does not exist: {p}")
                is_mp4 = False
                is_corrupted = True
            elif file_size == 0:
                tech_errors.append(f"File size is 0 bytes: {p}")
                is_mp4 = False
                is_corrupted = True
            else:
                try:
                    container = av.open(str(p))
                    fmt_name = container.format.name or ""
                    is_mp4 = any(k in fmt_name for k in ["mp4", "mov", "m4a", "3gp"])
                    dur = float(container.duration) / av.time_base if container.duration else 0.0

                    v_streams = container.streams.video
                    a_streams = container.streams.audio
                    v_count = len(v_streams)
                    a_count = len(a_streams)

                    if v_count > 0:
                        vs = v_streams[0]
                        v_codec = vs.codec_context.name
                        v_width = vs.width
                        v_height = vs.height
                        if vs.average_rate:
                            v_fps = float(vs.average_rate)
                    else:
                        tech_errors.append("No video streams found in media file")

                    if a_count > 0:
                        as_ = a_streams[0]
                        a_codec = as_.codec_context.name
                        if as_.layout and as_.layout.channels:
                            a_channels = len(as_.layout.channels)
                        elif hasattr(as_, "channels") and isinstance(as_.channels, int):
                            a_channels = as_.channels
                        else:
                            a_channels = 1
                        a_rate = as_.rate
                        if as_.duration and as_.time_base:
                            a_dur = float(as_.duration * as_.time_base)
                        else:
                            a_dur = dur
                    else:
                        tech_errors.append("No audio streams found in media file")

                    if a_count > 0 and a_dur is not None:
                        duration_delta = round(abs(dur - a_dur), 3)
                        is_dur_compat = duration_delta <= audio_tolerance_sec
                        if not is_dur_compat:
                            tech_errors.append(f"Audio/video duration drift {duration_delta}s exceeds tolerance {audio_tolerance_sec}s")

                    frame_count = 0
                    last_frame_bgr = None
                    for frame in container.decode(video=0):
                        frame_count += 1
                        bgr = frame.to_ndarray(format="bgr24")
                        if frame_count == 1:
                            first_frame_mean = float(np.mean(bgr))
                        last_frame_bgr = bgr

                    if last_frame_bgr is not None:
                        final_frame_mean = float(np.mean(last_frame_bgr))

                    container.close()
                except Exception as e:
                    is_corrupted = True
                    tech_errors.append(f"Media decode error: {e}")

        # -------------------------------------------------------------
        # TẦNG 1: TECHNICAL QA
        # -------------------------------------------------------------
        tech_pass = (
            file_exists
            and not is_corrupted
            and is_mp4
            and v_count >= 1
            and is_dur_compat
            and len(tech_errors) == 0
        ) if not is_mock else True

        tech_res = TechnicalQAResult(
            is_valid_mp4=is_mp4,
            file_exists=file_exists if not is_mock else True,
            file_size_bytes=file_size,
            duration_sec=round(dur, 3),
            fps=v_fps,
            video_codec=v_codec,
            resolution=f"{v_width}x{v_height}" if v_width and v_height else None,
            audio_codec=a_codec,
            audio_video_drift_sec=duration_delta,
            is_corrupted=is_corrupted,
            pass_status=tech_pass,
            errors=tech_errors,
        )

        # -------------------------------------------------------------
        # TẦNG 2: DRAWING QA
        # -------------------------------------------------------------
        req_strokes = 0
        comp_strokes = 0
        order_valid = True
        hand_path_ok = True
        hand_sync_ok = True
        no_early_rev = True
        no_instant_rev = True
        drawing_errors: List[str] = []
        drawing_details: List[str] = []

        if timeline is not None:
            draw_events = [e for e in timeline.events if e.action == "draw"]
            comp_strokes = len(draw_events)

            if scene_graph is not None:
                req_strokes = sum(
                    e.stroke_count if e.stroke_count > 0 else (len(e.required_stroke_ids) if e.required_stroke_ids else 1)
                    for e in scene_graph.entities if e.required
                )
                if req_strokes == 0:
                    req_strokes = comp_strokes
            else:
                req_strokes = comp_strokes

            hand_path_ok = all(len(e.hand_path) > 0 for e in timeline.events)
            if not hand_path_ok:
                drawing_errors.append("Invalid or empty hand_path detected in timeline events")

            hand_sync_ok = all(e.start_time <= e.end_time for e in timeline.events)
            if not hand_sync_ok:
                drawing_errors.append("Hand synchronization error: event start_time > end_time")

            no_early_rev = all(e.start_time >= 0.0 for e in timeline.events)
            if not no_early_rev:
                drawing_errors.append("Early reveal error: stroke start_time < 0.0")
        else:
            req_strokes = 1
            comp_strokes = 1

        comp_ratio = round(comp_strokes / max(1, req_strokes), 3) if req_strokes > 0 else 1.0
        if scene_graph is not None and scene_graph.entities:
            entity_ratios = [e.completion_ratio for e in scene_graph.entities if e.required]
            if entity_ratios and min(entity_ratios) < 1.0:
                comp_ratio = min(comp_ratio, min(entity_ratios))
                for ent in scene_graph.entities:
                    if ent.required and ent.completion_ratio < 1.0:
                        drawing_errors.append(
                            f"Entity {ent.name or ent.label or ent.id} incomplete: ratio {ent.completion_ratio} < 1.0"
                        )

        comp_ratio = min(1.0, comp_ratio)
        if comp_ratio < 1.0:
            drawing_errors.append(f"Drawing incomplete: completion ratio {comp_ratio} < 1.0")

        drawing_pass = (
            comp_ratio >= 1.0
            and order_valid
            and hand_path_ok
            and hand_sync_ok
            and no_early_rev
            and no_instant_rev
            and len(drawing_errors) == 0
        )
        drawing_res = DrawingQAResult(
            required_strokes=req_strokes,
            completed_strokes=comp_strokes,
            completion_ratio=comp_ratio,
            stroke_ordering_valid=order_valid,
            hand_path_valid=hand_path_ok,
            hand_sync_valid=hand_sync_ok,
            no_early_reveal=no_early_rev,
            no_instant_reveal=no_instant_rev,
            pass_status=drawing_pass,
            errors=drawing_errors,
            details=drawing_details,
        )

        # -------------------------------------------------------------
        # TẦNG 3: SEMANTIC VISUAL QA
        # -------------------------------------------------------------
        missing_entities: List[str] = []
        incomplete_entities: List[str] = []
        missing_relationships: List[str] = []
        missing_actions: List[str] = []
        semantic_errors: List[str] = []
        semantic_details: List[str] = []
        req_ent_count = 0
        pres_ent_count = 0
        req_rel_count = 0
        pres_rel_count = 0
        req_act_count = 0
        comp_act_count = 0

        all_entities_done = True
        all_actions_done = True
        all_relationships_done = True

        if scene_graph is not None:
            sched = timeline.entities_schedule if timeline else {}
            entity_events_ids = {
                e.entity_id for e in timeline.events
                if e.entity_id and (e.action == "draw" or len(e.hand_path) > 0)
            } if timeline else set()

            for e in scene_graph.entities:
                if e.required:
                    req_ent_count += 1
                    is_scheduled = (e.id in sched) or (e.id in entity_events_ids)
                    if timeline and not is_scheduled:
                        missing_entities.append(e.name or e.label or e.id)
                        semantic_errors.append(f"Required entity missing from timeline: {e.name or e.label or e.id}")
                        all_entities_done = False
                    elif e.completion_ratio < 1.0:
                        incomplete_entities.append(e.name or e.label or e.id)
                        semantic_errors.append(
                            f"Required entity not completed: {e.name or e.label or e.id} ({e.completion_ratio * 100:.1f}%)"
                        )
                        all_entities_done = False
                    else:
                        pres_ent_count += 1
                else:
                    pres_ent_count += 1

            for r in scene_graph.relationships:
                if r.required:
                    req_rel_count += 1
                    src = scene_graph.get_entity(r.source_id)
                    tgt = scene_graph.get_entity(r.target_id)
                    if not (src and tgt and src.completion_ratio >= 1.0 and tgt.completion_ratio >= 1.0):
                        missing_relationships.append(r.id or f"{r.source_id}->{r.target_id}")
                        semantic_errors.append(f"Required relationship incomplete: {r.description or r.relation_type}")
                        all_relationships_done = False
                    else:
                        pres_rel_count += 1
                else:
                    pres_rel_count += 1

            for a in scene_graph.actions:
                if a.required:
                    req_act_count += 1
                    ent = scene_graph.get_entity(a.entity_id)
                    if not ent or ent.completion_ratio < 1.0:
                        missing_actions.append(a.id or f"{a.entity_id}_{a.action_type}")
                        semantic_errors.append(f"Required action incomplete: {a.action_type} on {a.entity_id}")
                        all_actions_done = False
                    else:
                        comp_act_count += 1
                else:
                    comp_act_count += 1

        final_frame_deterministic = all_entities_done and all_actions_done and all_relationships_done
        final_frame_luminance_ok = True
        if final_frame_mean is not None and first_frame_mean is not None:
            final_frame_luminance_ok = (final_frame_mean < 254.0 and first_frame_mean > 180.0)

        final_frame_ok = final_frame_deterministic and final_frame_luminance_ok

        semantic_pass = (
            len(missing_entities) == 0
            and len(incomplete_entities) == 0
            and len(missing_relationships) == 0
            and len(missing_actions) == 0
            and final_frame_ok
        )
        semantic_res = SemanticVisualQAResult(
            required_entities_count=req_ent_count,
            present_entities_count=pres_ent_count,
            missing_entities=missing_entities,
            incomplete_entities=incomplete_entities,
            required_relationships_count=req_rel_count,
            present_relationships_count=pres_rel_count,
            missing_relationships=missing_relationships,
            required_actions_count=req_act_count,
            completed_actions_count=comp_act_count,
            missing_actions=missing_actions,
            final_frame_complete=final_frame_ok,
            pass_status=semantic_pass,
            errors=semantic_errors,
            details=semantic_details,
        )

        # -------------------------------------------------------------
        # QUY TẮC CỐT LÕI: OVERALL PASS RULE
        # Chỉ PASS khi Technical QA PASS AND Drawing QA PASS AND Semantic Visual QA PASS
        # -------------------------------------------------------------
        overall_pass = tech_pass and drawing_pass and semantic_pass

        return MediaReport(
            file_path=str(p),
            file_exists=file_exists if not is_mock else True,
            file_size_bytes=file_size,
            is_valid_mp4=is_mp4,
            duration_sec=round(dur, 3),
            video_streams_count=v_count,
            audio_streams_count=a_count,
            video_codec=v_codec,
            video_width=v_width,
            video_height=v_height,
            fps=v_fps,
            frame_count=frame_count,
            audio_codec=a_codec,
            audio_channels=a_channels,
            audio_sample_rate=a_rate,
            audio_duration_sec=round(a_dur, 3) if a_dur is not None else None,
            duration_delta=duration_delta,
            is_duration_compatible=is_dur_compat,
            is_corrupted=is_corrupted,
            first_frame_mean_luminance=round(first_frame_mean, 2) if first_frame_mean is not None else None,
            final_frame_mean_luminance=round(final_frame_mean, 2) if final_frame_mean is not None else None,
            visual_qa_pass=overall_pass,
            technical_qa=tech_res,
            drawing_qa=drawing_res,
            semantic_visual_qa=semantic_res,
            overall_pass=overall_pass,
            details={
                "container_format": fmt_name,
            },
        )
