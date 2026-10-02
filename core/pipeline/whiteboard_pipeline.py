from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from agents.base import AgentContext
from agents.narration.agent import NarrationAgent
from agents.script.agent import ScriptAgent
from agents.visual_planner.agent import VisualPlannerAgent
from core.assets.providers import AssetProvider, LocalAssetProvider
from core.providers.base import LLMProvider
from core.providers.mock import MockLLMProvider
from core.qa.media_probe import MediaProbe, MediaReport
from core.schemas.scene_graph import SceneGraph
from core.schemas.script import ScriptOutput
from core.schemas.timeline import DrawingTimeline
from core.schemas.tts import NarrationTiming, VoiceConfig
from core.timeline.synchronizer import DrawingTimelineSynchronizer
from core.tts.base import TTSProvider
from core.tts.mock import MockTTSProvider
from engines.whiteboard.adapter import WhiteboardEngineAdapter, WhiteboardRenderConfig
from tests.fixtures.test_cases_data import get_case_5_monkey_tree_banana


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
    Idea → Script → Narration (TTS) → Visual Planner → Assets → Drawing Strokes → Timeline → Whiteboard Engine → MP4.
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
        case5 = get_case_5_monkey_tree_banana()

        if script_agent is not None:
            self.script_agent = script_agent
        else:
            default_script_llm = llm_provider or MockLLMProvider(
                structured_responses=[
                    ScriptOutput(
                        title="Hành trình khỉ lấy chuối",
                        script=case5["script_text"],
                        segments=case5["segments"],
                    )
                ]
            )
            self.script_agent = ScriptAgent(llm=default_script_llm)

        if visual_planner_agent is not None:
            self.visual_planner_agent = visual_planner_agent
        else:
            default_vp_llm = llm_provider or MockLLMProvider(
                structured_responses=[case5["visual_plan"]]
            )
            self.visual_planner_agent = VisualPlannerAgent(llm=default_vp_llm)

        self.tts_provider = tts_provider or MockTTSProvider(char_per_sec=11.0)
        self.narration_agent = narration_agent or NarrationAgent(tts=self.tts_provider)
        self.asset_provider = asset_provider or LocalAssetProvider()
        self.timeline_synchronizer = timeline_synchronizer or DrawingTimelineSynchronizer(asset_provider=self.asset_provider)
        self.whiteboard_adapter = whiteboard_adapter or WhiteboardEngineAdapter()

    async def run(
        self,
        idea: str,
        output_dir: Path | str,
        render_config: Optional[WhiteboardRenderConfig] = None,
        voice_config: Optional[VoiceConfig] = None,
    ) -> PipelineResult:
        """
        Thực thi toàn bộ pipeline từ Idea đầu vào tới file MP4 hoàn chỉnh.
        """
        start_time = time.perf_counter()
        out_dir = Path(output_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        # -------------------------------------------------------------
        # Bước 1: Idea → Script
        # -------------------------------------------------------------
        script_res = await self.script_agent.generate_script(
            idea=idea,
            language="vi",
            target_duration_sec=5,
        )
        if not script_res.success:
            raise RuntimeError(f"ScriptAgent failed: {script_res.error_message}")

        script_text = script_res.data.get("script", idea)
        script_output_dict = script_res.data.get("script_output", {})
        raw_segments = script_output_dict.get("segments", [])
        from core.schemas.script import ScriptSegment
        segments = [ScriptSegment.model_validate(s) for s in raw_segments]

        # -------------------------------------------------------------
        # Bước 2: Script → Narration & Audio Timing (TTS)
        # -------------------------------------------------------------
        v_cfg = voice_config or VoiceConfig(voice_id="vi-VN-HoaiMyNeural", language="vi-VN", speed=1.0)
        audio_res = await self.tts_provider.generate(script_text, v_cfg)
        narration_timing = audio_res.timing or await self.tts_provider.get_timing(script_text, v_cfg)

        audio_file = out_dir / "narration.wav"
        audio_res.save_to_file(audio_file)

        # -------------------------------------------------------------
        # Bước 3: Script & Narration → Visual Scene Graph
        # -------------------------------------------------------------
        vp_res = await self.visual_planner_agent.plan_visuals(
            script=script_text,
            segments=segments,
        )
        if not vp_res.success:
            raise RuntimeError(f"VisualPlannerAgent failed: {vp_res.error_message}")

        plan_data = vp_res.data["visual_plan"]
        first_scene = plan_data["scenes"][0]
        scene_graph = SceneGraph.model_validate(first_scene["scene_graph"])

        # -------------------------------------------------------------
        # Bước 4: Assets + Drawing Strokes → Drawing Timeline
        # -------------------------------------------------------------
        timeline: DrawingTimeline = self.timeline_synchronizer.build_timeline(
            narration_timing=narration_timing,
            scene_graph=scene_graph,
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
        # Bước 8: Media QA & Visual QA
        # -------------------------------------------------------------
        report = MediaProbe.inspect_media(final_mp4_path)

        total_exec_time = round(time.perf_counter() - start_time, 3)

        return PipelineResult(
            idea=idea,
            script_text=script_text,
            audio_path=str(audio_file),
            image_path=str(image_path),
            annotation_path=str(annotation_path),
            raw_video_path=str(raw_video_path),
            final_mp4_path=str(final_mp4_path),
            media_report=report,
            is_success=report.file_exists and report.is_valid_mp4 and not report.is_corrupted,
            execution_time_sec=total_exec_time,
            metadata={
                "scene_id": scene_graph.scene_id,
                "total_events": len(timeline.events),
                "total_strokes": sum(1 for e in timeline.events if e.action == "draw"),
                "timeline_duration": timeline.total_duration,
                "audio_duration": narration_timing.duration,
            },
        )
