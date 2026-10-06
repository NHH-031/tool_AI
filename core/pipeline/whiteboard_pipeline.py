import hashlib
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from agents.base import AgentContext
from agents.narration.agent import NarrationAgent
from agents.script.agent import ScriptAgent
from agents.visual_planner.agent import VisualPlannerAgent
from core.assets.providers import AssetProvider, LocalAssetProvider
from core.pipeline.context import PipelineContext
from core.pipeline.semantic_planner import SemanticVisualPlanner
from core.providers.base import LLMProvider
from core.qa.media_probe import MediaProbe, MediaReport
from core.schemas.scene_graph import SceneGraph
from core.schemas.script import ScriptOutput, ScriptSegment
from core.schemas.timeline import DrawingTimeline
from core.schemas.tts import NarrationTiming, VoiceConfig
from core.timeline.synchronizer import DrawingTimelineSynchronizer
from core.tts.base import TTSProvider
from core.tts.mock import MockTTSProvider
from core.validation.illustration import SourceIllustrationValidator
from core.validation.semantic import SemanticValidator
from engines.whiteboard.adapter import WhiteboardEngineAdapter, WhiteboardRenderConfig

logger = logging.getLogger(__name__)


class PipelineResult(BaseModel):
    """Kết quả đầu ra của quy trình sản xuất video Whiteboard hoàn chỉnh (End-to-End)."""
    idea: str = Field(description="Ý tưởng gốc của người dùng")
    script_text: str = Field(description="Kịch bản lời thuyết minh hoàn chỉnh")
    audio_path: str = Field(description="Đường dẫn file âm thanh thuyết minh")
    image_path: str = Field(description="Đường dẫn file ảnh tổng thể scene_composition.png")
    annotation_path: str = Field(description="Đường dẫn file đặc tả phân cảnh scene_annotation.json")
    raw_video_path: str = Field(description="Đường dẫn video kết xuất thô từ Whiteboard Engine")
    final_mp4_path: str = Field(description="Đường dẫn video MP4 cuối cùng đã ghép âm thanh và video")
    media_report: MediaReport = Field(description="Báo cáo kiểm định kỹ thuật và chất lượng trực quan")
    is_success: bool = Field(default=True, description="Toàn bộ pipeline thực thi thành công")
    execution_time_sec: float = Field(default=0.0, description="Tổng thời gian thực thi (giây)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata bổ sung")


def is_idea_prompt(text: str) -> bool:
    """
    Tự động phát hiện nếu chuỗi input là một câu lệnh/yêu cầu/ý tưởng sinh video
    thay vì một kịch bản lời thoại đọc trực tiếp.
    """
    t = text.strip().lower()
    intent_keywords = [
        "hãy", "tóm tắt", "kể về", "kể lại", "kể câu chuyện", "câu chuyện về",
        "giới thiệu về", "viết kịch bản", "làm video", "tạo video", "sinh video",
        "cuộc đời", "tiểu sử", "sự nghiệp", "lịch sử", "giải thích", "review",
        "phân tích", "hành trình", "mô tả", "chia sẻ về", "nói về", "giúp tôi",
        "làm cho tôi", "tạo cho tôi"
    ]
    duration_keywords = [
        "trong 1 phút", "1 phút", "trong 2 phút", "2 phút", "trong 3 phút",
        "30 giây", "30s", "60 giây", "60s", "120s", "nửa phút", "45s", "45 giây"
    ]
    if any(kw in t for kw in duration_keywords):
        return True
    for kw in intent_keywords:
        if t.startswith(kw) or f" {kw} " in f" {t} ":
            return True
    return False


def extract_target_duration_sec(text: str, default_dur: float = 60.0) -> float:
    """
    Trích xuất thời lượng mong muốn (giây) từ văn bản yêu cầu của người dùng.
    Ví dụ: 'trong 1 phút' -> 60.0, '30 giây' -> 30.0, '2 phút' -> 120.0
    """
    import re
    t = text.lower()
    m_min = re.search(r'(\d+)\s*(phút|minute|m\b)', t)
    if m_min:
        return float(m_min.group(1)) * 60.0
    m_sec = re.search(r'(\d+)\s*(giây|giay|second|sec|s\b)', t)
    if m_sec:
        return float(m_sec.group(1))
    return default_dur


class WhiteboardPipeline:
    """
    Hệ thống sản xuất video Whiteboard Animation tự động End-to-End:
    User Input (Script / Idea) → PipelineContext → Narration (TTS) → Visual Planner → Assets → Drawing Strokes → Timeline → Whiteboard Engine → MP4.
    TUYỆT ĐỐI KHÔNG dùng monkey fixture làm default input cho kịch bản của người dùng.
    """

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        script_agent: Optional[ScriptAgent] = None,
        narration_agent: Optional[NarrationAgent] = None,
        visual_planner_agent: Optional[VisualPlannerAgent] = None,
        asset_provider: Optional[AssetProvider] = None,
        timeline_synchronizer: Optional[DrawingTimelineSynchronizer] = None,
        whiteboard_adapter: Optional[WhiteboardEngineAdapter] = None,
        tts_provider: Optional[TTSProvider] = None,
    ):
        self.llm_provider = llm_provider
        self.script_agent = script_agent or (ScriptAgent(llm=llm_provider) if llm_provider else None)
        self.visual_planner_agent = visual_planner_agent
        if tts_provider is not None:
            self.tts_provider = tts_provider
        else:
            try:
                from core.tts.edge import EdgeTTSProvider
                self.tts_provider = EdgeTTSProvider(default_voice="vi-VN-HoaiMyNeural")
            except Exception as e_tts:
                logger.warning(f"[WhiteboardPipeline] Could not load EdgeTTSProvider ({e_tts}), using MockTTSProvider.")
                self.tts_provider = MockTTSProvider(char_per_sec=11.0)
        self.narration_agent = narration_agent or NarrationAgent(tts=self.tts_provider)
        self.asset_provider = asset_provider or LocalAssetProvider()
        self.timeline_synchronizer = timeline_synchronizer or DrawingTimelineSynchronizer(asset_provider=self.asset_provider)
        self.whiteboard_adapter = whiteboard_adapter or WhiteboardEngineAdapter()

    async def run(
        self,
        idea: str = "",
        script: Optional[str] = None,
        input_mode: str = "SCRIPT",
        output_dir: Path | str = "output",
        render_config: Optional[WhiteboardRenderConfig] = None,
        voice_config: Optional[VoiceConfig] = None,
        context: Optional[PipelineContext] = None,
        job_id: Optional[str] = None,
        has_color: bool = True,
        target_duration_sec: Optional[float] = None,
    ) -> PipelineResult:
        """
        Thực thi toàn bộ pipeline từ Input đầu vào tới file MP4 hoàn chỉnh.
        Nếu input_mode == 'SCRIPT', userScript là Source of Truth (trừ khi phát hiện prompt/ý tưởng).
        Nếu input_mode == 'IDEA' hoặc phát hiện lệnh tóm tắt, tự động kích hoạt Storyboard đa phân cảnh.
        """
        start_time = time.perf_counter()
        out_dir = Path(output_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        # -------------------------------------------------------------
        # Bước 0: Khởi tạo và đồng bộ PipelineContext
        # -------------------------------------------------------------
        if context is not None:
            ctx = context
        else:
            raw_input = (script or idea).strip()
            if not raw_input:
                raise ValueError("Script or Idea is required.")
            j_id = job_id or f"job-{hashlib.md5(raw_input.encode('utf-8')).hexdigest()[:8]}"
            ctx = PipelineContext.create(
                job_id=j_id,
                input_text=raw_input,
                input_mode=input_mode,
                language=(voice_config.language if voice_config else "vi"),
                voice_id=(voice_config.voice_id if voice_config else "vi-VN-HoaiMyNeural"),
                speed=(voice_config.speed if voice_config else 1.0),
            )

        # Trích xuất thời lượng và tự động nhận diện ý định của người dùng
        user_text = (ctx.original_input or ctx.script or idea or script or "").strip()
        effective_dur = target_duration_sec or extract_target_duration_sec(user_text, default_dur=60.0)

        if ctx.input_mode == "SCRIPT" and is_idea_prompt(user_text):
            logger.info(
                f"[INTENT_AUTO_DETECT] Input '{user_text}' recognized as an IDEA/COMMAND prompt rather than "
                f"literal voiceover narration. Auto-promoting to IDEA mode with target duration {effective_dur}s."
            )
            ctx.input_mode = "IDEA"

        logger.info(
            f"[CREATE_VIDEO_REQUEST] jobId={ctx.job_id} inputMode={ctx.input_mode} "
            f"targetDur={effective_dur}s scriptHash={ctx.script_hash} text='{user_text}'"
        )

        # -------------------------------------------------------------
        # Bước 1: Source of Truth & Script Segments Resolution
        # -------------------------------------------------------------
        if ctx.input_mode == "SCRIPT":
            script_text = ctx.script
            if not script_text.strip():
                raise ValueError("Script is required when input_mode is 'SCRIPT'.")
            required_ents = list(SemanticValidator.extract_required_entities(script_text))
            from core.artwork.gemini_director import GeminiScriptDirector
            v_prompt_script = GeminiScriptDirector.create_single_scene_prompt(script_text, has_color=has_color) if GeminiScriptDirector.is_available() else ""
            segments = [
                ScriptSegment(
                    cue_index=1,
                    text=script_text,
                    estimated_duration_sec=max(3.5, round(len(script_text.split()) / 2.8, 1)),
                    semantic_meaning=f"Phân cảnh diễn hoạt cho kịch bản: {script_text}",
                    key_entities=required_ents,
                    visual_prompt=v_prompt_script,
                )
            ]
            logger.info(
                f"[SCRIPT_STAGE] jobId={ctx.job_id} sourceOfTruth=userScript script='{script_text}' "
                f"segments=1 entities={required_ents}"
            )
        else:
            # Mode IDEA: AI Script Agent / Gemini Script Director tạo kịch bản từ ý tưởng
            idea_text = ctx.original_input or ctx.script or user_text
            if not idea_text.strip():
                raise ValueError("Idea is required when input_mode is 'IDEA'.")

            from core.artwork.gemini_director import GeminiScriptDirector
            if GeminiScriptDirector.is_available():
                sb_scenes = GeminiScriptDirector.create_storyboard(
                    idea=idea_text,
                    target_duration_sec=effective_dur,
                    has_color=has_color,
                )
                segments = [
                    ScriptSegment(
                        cue_index=s.scene_index,
                        text=s.narration,
                        estimated_duration_sec=s.estimated_duration_sec,
                        semantic_meaning=s.title,
                        key_entities=list(SemanticValidator.extract_required_entities(s.narration)),
                        visual_prompt=s.visual_prompt,
                    )
                    for s in sb_scenes
                ]
                script_text = " ".join(s.narration for s in sb_scenes)
            elif self.script_agent is not None:
                script_res = await self.script_agent.generate_script(
                    idea=idea_text,
                    language=ctx.language,
                    target_duration_sec=int(effective_dur),
                )
                if not script_res.success:
                    raise RuntimeError(f"ScriptAgent failed: {script_res.error_message}")
                script_text = script_res.data.get("script", idea_text)
                script_output_dict = script_res.data.get("script_output", {})
                raw_segments = script_output_dict.get("segments", [])
                segments = [ScriptSegment.model_validate(s) for s in raw_segments] if raw_segments else [
                    ScriptSegment(
                        cue_index=1,
                        text=script_text,
                        estimated_duration_sec=effective_dur,
                        semantic_meaning=script_text,
                    )
                ]
            else:
                script_text = idea_text
                segments = [
                    ScriptSegment(
                        cue_index=1,
                        text=script_text,
                        estimated_duration_sec=effective_dur,
                        semantic_meaning=script_text,
                    )
                ]
            logger.info(
                f"[SCRIPT_STAGE] jobId={ctx.job_id} sourceOfTruth=ideaGenerated script='{script_text}' "
                f"segments={len(segments)}"
            )

        v_id = ctx.voice_id
        if not voice_config and (not v_id or v_id == "vi-VN-HoaiMyNeural"):
            hist_keywords = ["chiến dịch", "chiến thắng", "quân đội", "lịch sử", "hào hùng", "bộ đội", "điện biên phủ", "kháng chiến", "độc lập", "tướng", "quân ta", "chiến hào", "hầm"]
            check_text = (idea or script or ctx.original_input or script_text or "").lower()
            if any(kw in check_text for kw in hist_keywords):
                v_id = "vi-VN-NamMinhNeural"
        v_cfg = voice_config or VoiceConfig(voice_id=v_id, language=ctx.language, speed=ctx.speed)

        # -------------------------------------------------------------
        # Nếu kịch bản gồm nhiều phân cảnh (Multi-Scene Storyboard)
        # -------------------------------------------------------------
        if len(segments) > 1:
            scene_clips: list[Path] = []
            first_image_path = None
            first_annot_path = None
            first_sg = None
            first_timeline = None

            for s_idx, seg in enumerate(segments):
                scene_num = s_idx + 1
                seg_text = seg.text.strip()
                logger.info(f"[MULTI_SCENE] Processing Scene {scene_num}/{len(segments)}: '{seg_text[:60]}...'")

                # 1. Tạo audio cho phân cảnh này
                seg_audio = await self.tts_provider.generate(seg_text, v_cfg)
                seg_timing = seg_audio.timing or await self.tts_provider.get_timing(seg_text, v_cfg)
                seg_audio_file = out_dir / f"scene_{scene_num}_narration.wav"
                seg_audio.save_to_file(seg_audio_file)

                # 2. Lập kế hoạch ngữ nghĩa cho phân cảnh này
                seg_plan = SemanticVisualPlanner.plan_from_script(
                    script=seg_text,
                    segments=[seg],
                    title=f"{seg.semantic_meaning or f'Cảnh {scene_num}'}",
                )
                seg_sg = seg_plan.scenes[0].scene_graph
                seg_sg.scene_id = f"scene_{scene_num}"
                seg_sg.narration = seg_text
                seg_sg.has_color = has_color
                seg_sg.visual_prompt = getattr(seg, "visual_prompt", "") or seg.semantic_meaning

                # 3. Đồng bộ Timeline
                seg_timeline = self.timeline_synchronizer.build_timeline(
                    narration_timing=seg_timing,
                    scene_graph=seg_sg,
                )

                # 4. Tạo Artwork & Annotation cho phân cảnh
                seg_img, seg_annot = self.whiteboard_adapter.prepare_scene_artifacts(
                    scene_graph=seg_sg,
                    timeline=seg_timeline,
                    output_dir=out_dir,
                )
                if first_image_path is None:
                    first_image_path = seg_img
                    first_annot_path = seg_annot
                    first_sg = seg_sg
                    first_timeline = seg_timeline

                # 5. Render Video cho phân cảnh
                seg_raw_video = out_dir / f"scene_{scene_num}_raw.mp4"
                seg_cfg = render_config or WhiteboardRenderConfig(
                    fps=24,
                    cap_long_edge=640,
                    ink_path="skeleton",
                    color_fill="contour-wipe" if has_color else "none",
                    has_color=has_color,
                    total_ms=int(round(seg_timeline.total_duration * 1000)),
                )
                self.whiteboard_adapter.render_scene(
                    image_path=seg_img,
                    annotation_path=seg_annot,
                    output_path=seg_raw_video,
                    config=seg_cfg,
                )

                # 6. Mux Audio & Video của phân cảnh
                seg_final_mp4 = out_dir / f"scene_{scene_num}_final.mp4"
                self.whiteboard_adapter.mux_audio_video(
                    video_path=seg_raw_video,
                    audio_path=seg_audio_file,
                    output_path=seg_final_mp4,
                )
                scene_clips.append(seg_final_mp4)

            # 7. Ghép nối toàn bộ phân cảnh thành video và audio hoàn chỉnh
            merged_final_mp4 = out_dir / f"{ctx.job_id}_final.mp4"
            from scripts.merge_scenes import _ffmpeg_concat_copy, _pyav_concat
            concat_ok = _ffmpeg_concat_copy(scene_clips, merged_final_mp4) or _pyav_concat(scene_clips, merged_final_mp4)
            final_video_out = merged_final_mp4 if (concat_ok and merged_final_mp4.exists()) else scene_clips[0]

            merged_audio = out_dir / f"{ctx.job_id}_narration.wav"
            try:
                import wave
                with wave.open(str(merged_audio), "wb") as outfile:
                    for i, s_clip in enumerate(scene_clips):
                        s_aud = out_dir / f"scene_{i+1}_narration.wav"
                        if s_aud.exists():
                            with wave.open(str(s_aud), "rb") as infile:
                                if i == 0:
                                    outfile.setparams(infile.getparams())
                                outfile.writeframes(infile.readframes(infile.getnframes()))
            except Exception as e_aud:
                logger.warning(f"Error concatenating scene audios: {e_aud}")
                merged_audio = out_dir / "scene_1_narration.wav"

            segments_meta = [
                {
                    "segment_id": f"seg-{idx+1:02d}",
                    "text": seg.text,
                    "estimated_duration": seg.estimated_duration_sec,
                    "semantic_meaning": seg.semantic_meaning,
                    "keywords": list(SemanticValidator.extract_required_entities(seg.text)) or ["story"],
                    "visual_prompt": getattr(seg, "visual_prompt", ""),
                }
                for idx, seg in enumerate(segments)
            ]
            scenes_meta = [
                {
                    "id": f"scene-{idx+1:02d}",
                    "scene_index": idx + 1,
                    "title": seg.semantic_meaning or f"Cảnh {idx+1}",
                    "duration_ms": int(seg.estimated_duration_sec * 1000),
                    "entities_count": 2,
                }
                for idx, seg in enumerate(segments)
            ]

            total_exec_time = round(time.perf_counter() - start_time, 3)
            return PipelineResult(
                idea=idea or ctx.original_input,
                script_text=script_text,
                audio_path=str(merged_audio),
                image_path=str(first_image_path),
                annotation_path=str(first_annot_path),
                raw_video_path=str(scene_clips[0]),
                final_mp4_path=str(final_video_out),
                media_report=MediaProbe.inspect_media(
                    file_path=final_video_out,
                    scene_graph=first_sg,
                    timeline=first_timeline,
                    script_text=script_text,
                ),
                is_success=True,
                execution_time_sec=total_exec_time,
                metadata={
                    "job_id": ctx.job_id,
                    "input_mode": ctx.input_mode,
                    "has_color": has_color,
                    "scenes_count": len(scene_clips),
                    "script_hash": ctx.script_hash,
                    "segments_meta": segments_meta,
                    "scenes_meta": scenes_meta,
                    "timeline_duration": sum(s.estimated_duration_sec for s in segments),
                    "audio_duration": sum(s.estimated_duration_sec for s in segments),
                },
            )

        # -------------------------------------------------------------
        # Bước 2: Script → Narration & Audio Timing (TTS) cho phân cảnh đơn
        # -------------------------------------------------------------
        audio_res = await self.tts_provider.generate(script_text, v_cfg)
        narration_timing = audio_res.timing or await self.tts_provider.get_timing(script_text, v_cfg)

        audio_file = out_dir / "narration.wav"
        audio_res.save_to_file(audio_file)

        # -------------------------------------------------------------
        # Bước 3: Script & Narration → Visual Scene Graph
        # -------------------------------------------------------------
        if self.visual_planner_agent is not None:
            vp_res = await self.visual_planner_agent.plan_visuals(
                script=script_text,
                segments=segments,
            )
            if vp_res.success:
                plan_data = vp_res.data["visual_plan"]
                first_scene = plan_data["scenes"][0]
                scene_graph = SceneGraph.model_validate(first_scene["scene_graph"])
            else:
                plan = SemanticVisualPlanner.plan_from_script(
                    script=script_text,
                    segments=segments,
                    title=f"Scene {ctx.job_id}",
                )
                scene_graph = plan.scenes[0].scene_graph
        else:
            plan = SemanticVisualPlanner.plan_from_script(
                script=script_text,
                segments=segments,
                title=f"Scene {ctx.job_id}",
            )
            scene_graph = plan.scenes[0].scene_graph
        if segments and getattr(segments[0], "visual_prompt", ""):
            scene_graph.visual_prompt = segments[0].visual_prompt
        scene_graph.has_color = has_color

        entity_labels = [e.label for e in scene_graph.entities]
        logger.info(
            f"[VISUAL_PLAN_STAGE] jobId={ctx.job_id} scriptHash={ctx.script_hash} "
            f"entities={entity_labels} relationships={len(scene_graph.relationships)}"
        )

        # -------------------------------------------------------------
        # Bước 4: Assets + Drawing Strokes → Drawing Timeline
        # -------------------------------------------------------------
        timeline: DrawingTimeline = self.timeline_synchronizer.build_timeline(
            narration_timing=narration_timing,
            scene_graph=scene_graph,
        )
        logger.info(
            f"[DRAWING_STAGE] jobId={ctx.job_id} sceneId={scene_graph.scene_id} "
            f"totalEvents={len(timeline.events)}"
        )

        # -------------------------------------------------------------
        # Bước 5: Adapter Export → Scene Composition Image & Annotation JSON
        # -------------------------------------------------------------
        image_path, annotation_path = self.whiteboard_adapter.prepare_scene_artifacts(
            scene_graph=scene_graph,
            timeline=timeline,
            output_dir=out_dir,
        )

        # -------------------------------------------------------------
        # Bước 5.5: Source Illustration & Annotation Validation Gate
        # -------------------------------------------------------------
        illustration_val = SourceIllustrationValidator.validate_pre_render(
            script_text=script_text,
            scene_graph=scene_graph,
            timeline=timeline,
            image_path=image_path,
            annotation_path=annotation_path,
        )
        if not illustration_val.is_valid:
            error_msg = f"Illustration validation failed before render: {'; '.join(illustration_val.errors)}"
            logger.error(f"[ILLUSTRATION_VALIDATION_ERROR] jobId={ctx.job_id} errors={illustration_val.errors}")
            raise RuntimeError(error_msg)

        logger.info(
            f"[ILLUSTRATION_VALIDATION_STAGE] jobId={ctx.job_id} status=PASS "
            f"visionStatus={illustration_val.vision_qa_status}"
        )

        # -------------------------------------------------------------
        # Bước 6: Whiteboard Engine → Video Rendering
        # -------------------------------------------------------------
        raw_video_path = out_dir / f"{scene_graph.scene_id}_raw.mp4"
        cfg = render_config or WhiteboardRenderConfig(
            fps=24,
            cap_long_edge=640,
            ink_path="skeleton",
            color_fill="contour-wipe" if has_color else "none",
            has_color=has_color,
            total_ms=int(round(timeline.total_duration * 1000)),
        )

        self.whiteboard_adapter.render_scene(
            image_path=image_path,
            annotation_path=annotation_path,
            output_path=raw_video_path,
            config=cfg,
        )
        logger.info(f"[RENDER_STAGE] jobId={ctx.job_id} artifact={raw_video_path}")

        # -------------------------------------------------------------
        # Bước 7: Mux Audio + Video → Final MP4
        # -------------------------------------------------------------
        final_mp4_path = out_dir / f"{scene_graph.scene_id}_final.mp4"
        self.whiteboard_adapter.mux_audio_video(
            video_path=raw_video_path,
            audio_path=audio_file,
            output_path=final_mp4_path,
        )

        # -------------------------------------------------------------
        # Bước 8: Media QA & Four-Layer Visual QA
        # -------------------------------------------------------------
        report = MediaProbe.inspect_media(
            file_path=final_mp4_path,
            scene_graph=scene_graph,
            timeline=timeline,
            script_text=script_text,
        )
        logger.info(
            f"[QA_STAGE] jobId={ctx.job_id} result={{'overall_pass': report.overall_pass, "
            f"'technical_qa': getattr(report.technical_qa, 'pass_technical', False), "
            f"'drawing_qa': getattr(report.drawing_qa, 'pass_drawing', False), "
            f"'semantic_qa': getattr(report.semantic_qa, 'pass_semantic', False), "
            f"'visual_style_qa': getattr(report.visual_style_qa, 'pass_style', False)}}"
        )

        total_exec_time = round(time.perf_counter() - start_time, 3)

        return PipelineResult(
            idea=idea or ctx.original_input,
            script_text=script_text,
            audio_path=str(audio_file),
            image_path=str(image_path),
            annotation_path=str(annotation_path),
            raw_video_path=str(raw_video_path),
            final_mp4_path=str(final_mp4_path),
            media_report=report,
            is_success=report.overall_pass,
            execution_time_sec=total_exec_time,
            metadata={
                "job_id": ctx.job_id,
                "project_id": ctx.project_id,
                "input_mode": ctx.input_mode,
                "has_color": has_color,
                "script_hash": ctx.script_hash,
                "scene_id": scene_graph.scene_id,
                "entities": entity_labels,
                "total_events": len(timeline.events),
                "total_strokes": sum(1 for e in timeline.events if e.action == "draw"),
                "timeline_duration": timeline.total_duration,
                "audio_duration": narration_timing.duration,
            },
        )
