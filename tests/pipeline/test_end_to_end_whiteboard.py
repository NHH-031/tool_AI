import pytest
from pathlib import Path

from core.pipeline.whiteboard_pipeline import WhiteboardPipeline
from core.qa.media_probe import MediaProbe
from core.schemas.annotation import AnnotationSchema
from core.schemas.scene_graph import Position, SceneGraph, VisualEntity, VisualRelationship
from core.schemas.tts import NarrationTiming, WordTiming
from core.timeline.synchronizer import DrawingTimelineSynchronizer
from engines.whiteboard.adapter import WhiteboardEngineAdapter, WhiteboardRenderConfig


@pytest.fixture
def monkey_banana_scene_graph() -> SceneGraph:
    """Fixture tạo SceneGraph cho câu chuyện Con khỉ trèo cây lấy chuối."""
    sg = SceneGraph(
        scene_id="scene_monkey_banana_demo",
        description="Con khỉ đang trèo lên cây để lấy một quả chuối.",
    )
    sg.add_entity(
        VisualEntity(
            id="entity_tree",
            name="tree",
            label="tree",
            importance="primary",
            layer=1,
            position=Position(x=820, y=80, width=720, height=880),
        )
    )
    sg.add_entity(
        VisualEntity(
            id="entity_monkey",
            name="monkey",
            label="monkey",
            importance="primary",
            layer=2,
            action="climbing",
            position=Position(x=720, y=400, width=440, height=440),
        )
    )
    sg.add_entity(
        VisualEntity(
            id="entity_banana",
            name="banana",
            label="banana",
            importance="primary",
            layer=3,
            position=Position(x=1120, y=180, width=240, height=240),
        )
    )
    sg.add_relationship(
        VisualRelationship(
            source_id="entity_monkey",
            target_id="entity_tree",
            relation_type="climbing",
            description="monkey climbing tree",
        )
    )
    sg.add_relationship(
        VisualRelationship(
            source_id="entity_monkey",
            target_id="entity_banana",
            relation_type="reaching",
            description="monkey reaching banana",
        )
    )
    return sg


@pytest.fixture
def mock_narration_timing() -> NarrationTiming:
    """Timing chuẩn từ narration TTS cho câu: 'Con khỉ đang trèo lên cây để lấy một quả chuối.'"""
    return NarrationTiming(
        text="Con khỉ đang trèo lên cây để lấy một quả chuối.",
        duration=4.5,
        words=[
            WordTiming(word="Con", start_time=0.10, end_time=0.35),
            WordTiming(word="khỉ", start_time=0.35, end_time=0.75),
            WordTiming(word="đang", start_time=0.80, end_time=1.05),
            WordTiming(word="trèo", start_time=1.10, end_time=1.45),
            WordTiming(word="lên", start_time=1.45, end_time=1.70),
            WordTiming(word="cây", start_time=1.70, end_time=2.15),
            WordTiming(word="để", start_time=2.20, end_time=2.40),
            WordTiming(word="lấy", start_time=2.45, end_time=2.75),
            WordTiming(word="một", start_time=2.80, end_time=3.05),
            WordTiming(word="quả", start_time=3.10, end_time=3.40),
            WordTiming(word="chuối.", start_time=3.45, end_time=4.10),
        ],
        provider_name="MockTTSProvider",
        is_word_level=True,
    )


def test_adapter_prepare_artifacts(tmp_path, monkey_banana_scene_graph, mock_narration_timing):
    """Kiểm tra adapter chuyển đổi SceneGraph và DrawingTimeline sang image và annotation.json."""
    synchronizer = DrawingTimelineSynchronizer()
    timeline = synchronizer.build_timeline(mock_narration_timing, monkey_banana_scene_graph)

    adapter = WhiteboardEngineAdapter()
    img_path, ann_path = adapter.prepare_scene_artifacts(
        scene_graph=monkey_banana_scene_graph,
        timeline=timeline,
        output_dir=tmp_path,
    )

    assert img_path.exists()
    assert img_path.stat().st_size > 0
    assert ann_path.exists()

    # Validate JSON cấu trúc theo AnnotationSchema
    ann_content = ann_path.read_text(encoding="utf-8")
    ann_schema = AnnotationSchema.model_validate_json(ann_content)

    assert ann_schema.canvas.width == 1920
    assert ann_schema.canvas.height == 1080
    assert len(ann_schema.elements) == 3

    # Kiểm tra thứ tự và bảo vệ che chắn (protectedRegions ngăn lộ nét sớm)
    elements = ann_schema.elements
    assert elements[0].id == "entity_monkey"
    assert len(elements[0].reveal.protectedRegions) == 2  # tree và banana được bảo vệ khi khỉ vẽ

    assert elements[1].id == "entity_tree"
    assert len(elements[1].reveal.protectedRegions) == 1  # banana được bảo vệ khi cây vẽ

    assert elements[2].id == "entity_banana"
    assert len(elements[2].reveal.protectedRegions) == 0


def test_media_probe_error_detection(tmp_path):
    """Kiểm tra MediaProbe phát hiện chính xác file không tồn tại hoặc rỗng."""
    non_existent = tmp_path / "missing.mp4"
    report_none = MediaProbe.inspect_media(non_existent)
    assert report_none.file_exists is False
    assert report_none.is_valid_mp4 is False

    empty_file = tmp_path / "empty.mp4"
    empty_file.write_bytes(b"")
    report_empty = MediaProbe.inspect_media(empty_file)
    assert report_empty.file_exists is True
    assert report_empty.file_size_bytes == 0
    assert report_empty.is_corrupted is True


@pytest.mark.asyncio
async def test_end_to_end_whiteboard_generation(tmp_path):
    """
    Test End-to-End toàn diện của Phase 09:
    Idea → Script → Narration → Visual Planner → Assets → Strokes → Timeline → Engine → MP4
    """
    pipeline = WhiteboardPipeline()
    cfg = WhiteboardRenderConfig(
        fps=24,
        cap_long_edge=640,
        ink_path="grid",
        color_fill="contour-wipe",
    )

    idea = "Con khỉ đang trèo lên cây để lấy một quả chuối."
    result = await pipeline.run(
        idea=idea,
        output_dir=tmp_path,
        render_config=cfg,
    )

    # 1. Pipeline hoàn thành thành công
    assert result.is_success is True
    assert result.execution_time_sec > 0.0

    # 2. Toàn bộ file sản phẩm trung gian và cuối cùng phải tồn tại trên đĩa
    assert Path(result.audio_path).exists()
    assert Path(result.image_path).exists()
    assert Path(result.annotation_path).exists()
    assert Path(result.raw_video_path).exists()
    assert Path(result.final_mp4_path).exists()

    final_mp4 = Path(result.final_mp4_path)
    assert final_mp4.stat().st_size > 50_000, "MP4 video phải có dung lượng thực tế hợp lệ"

    # 3. Technical Media QA bằng MediaProbe
    report = result.media_report
    assert report.file_exists is True
    assert report.is_valid_mp4 is True
    assert report.is_corrupted is False
    assert report.duration_sec >= 3.5

    # 4. Stream Validation
    assert report.video_streams_count == 1
    assert report.audio_streams_count == 1
    assert report.video_codec == "h264"
    assert report.audio_codec == "aac"
    assert report.video_width == 640
    assert report.video_height == 360
    assert report.fps == 24.0
    assert report.frame_count >= 80

    # 5. Audio-Video Duration Compatibility
    assert report.is_duration_compatible is True
    assert report.duration_delta is not None
    assert report.duration_delta < 1.0, f"Độ lệch thời lượng video ({report.duration_sec}s) và audio ({report.audio_duration_sec}s) phải < 1.0s"

    # 6. Visual Invariants QA
    assert report.visual_qa_pass is True
    assert report.first_frame_mean_luminance is not None
    assert report.first_frame_mean_luminance > 180.0, "Khung hình đầu phải là bảng trắng sáng"
    assert report.final_frame_mean_luminance is not None
    assert report.final_frame_mean_luminance < 254.0, "Khung hình cuối phải có nét vẽ mực"
