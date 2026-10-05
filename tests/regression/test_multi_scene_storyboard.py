from pathlib import Path
import pytest
from PIL import Image

from core.artwork.gemini_director import GeminiScriptDirector, StoryboardScene
from core.artwork.generator import PollinationsArtProvider, HighFidelityArtProvider
from core.artwork.prompt_builder import StructuredIllustrationPrompt
from core.pipeline.semantic_planner import SemanticVisualPlanner
from core.schemas.script import ScriptSegment
from core.timeline.synchronizer import DrawingTimelineSynchronizer
from core.tts.mock import MockTTSProvider
from core.schemas.tts import VoiceConfig


def test_gemini_script_director_storyboard():
    """Kiểm tra GeminiScriptDirector tự động phân tích và tạo kịch bản 3 phân cảnh cho Điện Biên Phủ."""
    idea = "kể về chiến dịch Điện Biên Phủ"
    scenes = GeminiScriptDirector.create_storyboard(idea, target_scenes=3)

    assert len(scenes) >= 3, f"FAIL: Phải sinh ít nhất 3 phân cảnh, nhận được {len(scenes)}"
    for idx, sc in enumerate(scenes):
        assert sc.scene_index == idx + 1
        assert len(sc.narration.strip()) > 10, f"FAIL: Lời thoại cảnh {idx+1} quá ngắn"
        assert len(sc.visual_prompt.strip()) > 20, f"FAIL: Visual prompt cảnh {idx+1} quá ngắn"
        assert "Notion" in sc.visual_prompt or "line art" in sc.visual_prompt.lower()
        assert sc.estimated_duration_sec > 0


@pytest.mark.asyncio
async def test_pollinations_art_provider_generation(tmp_path):
    """Kiểm tra PollinationsArtProvider tạo ảnh 1920x1080 chuẩn Notion doodle."""
    provider = PollinationsArtProvider(fallback_provider=HighFidelityArtProvider())
    prompt = StructuredIllustrationPrompt(
        subject="Vietnamese soldiers pulling heavy artillery across steep mountain passes",
        action="soldiers pulling ropes climbing uphill",
        relationship="pulling artillery through mountains",
        composition="16:9",
        pose="pulling",
        line_style="clean black line art",
        whiteboard_style="Notion doodle",
        background="#F5EBD7",
        negative_constraints="no text",
        full_prompt="Vietnamese soldiers pulling heavy artillery in Dien Bien Phu battle",
        scene_context="Bộ đội kéo pháo vào trận địa Điện Biên Phủ",
    )
    out_file = tmp_path / "pollinations_test.png"
    result = await provider.generate_artwork(prompt, out_file)

    assert result.exists()
    assert result.stat().st_size > 5000
    with Image.open(result) as img:
        assert img.size == (1920, 1080)


@pytest.mark.asyncio
async def test_multi_scene_timeline_synchronization():
    """Kiểm tra mỗi phân cảnh có timeline và thời lượng khớp chính xác với audio thuyết minh."""
    tts = MockTTSProvider(char_per_sec=10.0)
    v_cfg = VoiceConfig(voice_id="vi-VN-NamMinhNeural", language="vi")

    story_scenes = [
        "Năm 1954, tập đoàn cứ điểm Điện Biên Phủ được xây dựng kiên cố tại thung lũng Mường Thanh.",
        "Hàng vạn chiến sĩ ta xẻ núi, kéo pháo lên những dốc đèo hiểm trở chuẩn bị tiến công.",
        "Chiều ngày 7 tháng 5 năm 1954, lá cờ Quyết chiến Quyết thắng tung bay trên nóc hầm Đờ Cát.",
    ]

    synchronizer = DrawingTimelineSynchronizer()

    for idx, text in enumerate(story_scenes):
        seg = ScriptSegment(
            cue_index=idx + 1,
            text=text,
            estimated_duration_sec=8.0,
            semantic_meaning=f"Cảnh {idx + 1}",
        )
        audio_res = await tts.generate(text, v_cfg)
        timing = audio_res.timing or await tts.get_timing(text, v_cfg)

        plan = SemanticVisualPlanner.plan_from_script(script=text, segments=[seg], title=f"Cảnh {idx+1}")
        sg = plan.scenes[0].scene_graph

        timeline = synchronizer.build_timeline(narration_timing=timing, scene_graph=sg)

        # Đảm bảo timeline khớp sát thời lượng audio
        assert abs(timeline.total_duration - timing.duration) < 1.0, (
            f"Cảnh {idx+1}: Timeline ({timeline.total_duration:.2f}s) không khớp Audio ({timing.duration:.2f}s)"
        )
        assert len(timeline.events) >= 1
