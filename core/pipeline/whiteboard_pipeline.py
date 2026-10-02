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
        self.visual_planner_agent = visual_planner_agent or (VisualPlannerAgent(llm=llm_provider) if llm_provider else None)
        self.tts_provider = tts_provider or MockTTSProvider(char_per_sec=11.0)
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
    ) -> PipelineResult:
        """
        Thực thi toàn bộ pipeline từ Input đầu vào tới file MP4 hoàn chỉnh.
        Nếu input_mode == 'SCRIPT', userScript là Source of Truth.
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
                voice_id=(voice_config.voice_id if voice_config else "vi-VN-Standard-B"),
                speed=(voice_config.speed if voice_config else 1.0),
            )

        logger.info(
            f"[CREATE_VIDEO_REQUEST] jobId={ctx.job_id} inputMode={ctx.input_mode} "
            f"scriptHash={ctx.script_hash} script='{ctx.script}'"
        )

        # -------------------------------------------------------------
        # Bước 1: Source of Truth & Script Segments Resolution
        # -------------------------------------------------------------
        if ctx.input_mode == "SCRIPT":
            script_text = ctx.script
            if not script_text.strip():
                raise ValueError("Script is required when input_mode is 'SCRIPT'.")
            required_ents = list(SemanticValidator.extract_required_entities(script_text))
            segments = [
                ScriptSegment(
                    cue_index=1,
                    text=script_text,
                    estimated_duration_sec=max(3.5, round(len(script_text.split()) / 2.8, 1)),
                    semantic_meaning=f"Phân cảnh diễn hoạt cho kịch bản: {script_text}",
                    key_entities=required_ents,
                )
            ]
            logger.info(
                f"[SCRIPT_STAGE] jobId={ctx.job_id} sourceOfTruth=userScript script='{script_text}' "
                f"segments=1 entities={required_ents}"
            )
        else:
            # Mode IDEA: AI Script Agent tạo kịch bản từ ý tưởng
            idea_text = ctx.original_input or ctx.script
            if not idea_text.strip():
                raise ValueError("Idea is required when input_mode is 'IDEA'.")

            if self.script_agent is not None:
                script_res = await self.script_agent.generate_script(
                    idea=idea_text,
                    language=ctx.language,
                    target_duration_sec=5,
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
                        estimated_duration_sec=5.0,
                        semantic_meaning=script_text,
                    )
                ]
            else:
                script_text = idea_text
                segments = [
                    ScriptSegment(
                        cue_index=1,
                        text=script_text,
                        estimated_duration_sec=5.0,
                        semantic_meaning=script_text,
                    )
                ]
            logger.info(
                f"[SCRIPT_STAGE] jobId={ctx.job_id} sourceOfTruth=ideaGenerated script='{script_text}' "
                f"segments={len(segments)}"
            )

        # -------------------------------------------------------------
        # Bước 2: Script → Narration & Audio Timing (TTS)
        # -------------------------------------------------------------
        v_cfg = voice_config or VoiceConfig(voice_id=ctx.voice_id, language=ctx.language, speed=ctx.speed)
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
        # Bước 6: Whiteboard Engine → Video Rendering
        # -------------------------------------------------------------
        raw_video_path = out_dir / f"{scene_graph.scene_id}_raw.mp4"
        cfg = render_config or WhiteboardRenderConfig(
            fps=24,
            cap_long_edge=640,
            ink_path="grid",
            color_fill="contour-wipe",
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
        # Bước 8: Media QA & Three-Layer Visual QA
        # -------------------------------------------------------------
        report = MediaProbe.inspect_media(
            file_path=final_mp4_path,
            scene_graph=scene_graph,
            timeline=timeline,
        )
        logger.info(
            f"[QA_STAGE] jobId={ctx.job_id} result={{'overall_pass': report.overall_pass, "
            f"'technical_qa': getattr(report.technical_qa, 'pass_technical', False), "
            f"'drawing_qa': getattr(report.drawing_qa, 'pass_drawing', False), "
            f"'semantic_qa': getattr(report.semantic_qa, 'pass_semantic', False)}}"
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
                "script_hash": ctx.script_hash,
                "scene_id": scene_graph.scene_id,
                "entities": entity_labels,
                "total_events": len(timeline.events),
                "total_strokes": sum(1 for e in timeline.events if e.action == "draw"),
                "timeline_duration": timeline.total_duration,
                "audio_duration": narration_timing.duration,
            },
        )
