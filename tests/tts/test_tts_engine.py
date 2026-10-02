from __future__ import annotations

import pytest
from core.schemas.tts import VoiceConfig, WordTiming
from core.tts.base import InvalidVoiceError, TTSConnectionError
from core.tts.mock import MockTTSProvider
from core.tts.resilient import ResilientTTSProvider
from core.tts.timing import TimingEstimator
from agents.narration.agent import NarrationAgent
from agents.base import AgentContext


@pytest.mark.asyncio
async def test_audio_generation():
    """Kiểm tra chức năng sinh âm thanh cơ bản trả về đầy đủ audio bytes, duration, format, sample_rate."""
    tts = MockTTSProvider()
    cfg = VoiceConfig(voice_id="vi-VN-HoaiMyNeural", language="vi-VN", speed=1.0)
    result = await tts.generate("Xin chào, đây là video hoạt họa bảng trắng.", cfg)

    assert result.audio_bytes is not None
    assert len(result.audio_bytes) > 0
    assert result.duration > 0.0
    assert result.duration_ms == int(result.duration * 1000)
    assert result.sample_rate == 24000
    assert result.channels == 1
    assert result.voice_config.voice_id == "vi-VN-HoaiMyNeural"
    assert result.timing is not None


@pytest.mark.asyncio
async def test_duration_calculation_and_monotonicity():
    """Kiểm tra tính toán thời lượng phát âm: văn bản dài hơn thì duration phải lớn hơn."""
    tts = MockTTSProvider()
    short_text = "Chào bạn."
    long_text = "Chào bạn, hôm nay chúng ta sẽ cùng nhau tìm hiểu về nguyên lý hoạt động của động cơ nét vẽ bảng trắng AI."

    dur_short = await tts.get_duration(short_text)
    dur_long = await tts.get_duration(long_text)

    assert dur_short > 0.0
    assert dur_long > dur_short
    assert dur_long >= dur_short * 2.0


@pytest.mark.asyncio
async def test_speed_control():
    """Kiểm tra thay đổi tốc độ đọc (speed): speed=2.0 phải rút ngắn thời lượng so với speed=1.0."""
    tts = MockTTSProvider()
    text = "Thử nghiệm kiểm soát tốc độ phát âm thanh trong Whiteboard Studio."

    cfg_normal = VoiceConfig(voice_id="default", speed=1.0)
    cfg_fast = VoiceConfig(voice_id="default", speed=2.0)
    cfg_slow = VoiceConfig(voice_id="default", speed=0.5)

    res_normal = await tts.generate(text, cfg_normal)
    res_fast = await tts.generate(text, cfg_fast)
    res_slow = await tts.generate(text, cfg_slow)

    # Tốc độ nhanh phải có thời lượng ngắn hơn tốc độ bình thường
    assert res_fast.duration < res_normal.duration
    # Tốc độ chậm phải có thời lượng dài hơn tốc độ bình thường
    assert res_slow.duration > res_normal.duration
    # Tỷ lệ thời lượng tương đương nghịch đảo của speed
    ratio = res_normal.duration / res_fast.duration
    assert 1.7 <= ratio <= 2.3


@pytest.mark.asyncio
async def test_word_timing_when_supported():
    """Kiểm tra word timing thực tế khi provider hỗ trợ word alignment."""
    tts = MockTTSProvider(supports_word_timing=True)
    text = "Con khỉ leo cây lấy chuối"
    cfg = VoiceConfig(voice_id="vi-VN-NamMinhNeural", speed=1.0)

    timing = await tts.get_timing(text, cfg)

    assert timing.timing_level == "word"
    assert timing.is_fallback is False
    assert timing.fallback_reason is None
    assert len(timing.words) == 6

    # Kiểm tra tính đơn điệu và không chồng chéo của các từ
    prev_end = 0.0
    for w in timing.words:
        assert isinstance(w, WordTiming)
        assert w.start_time >= prev_end - 0.001
        assert w.end_time > w.start_time
        assert w.duration > 0.0
        prev_end = w.end_time

    assert abs(timing.words[-1].end_time - timing.duration) < 0.05


@pytest.mark.asyncio
async def test_fallback_timing_when_unsupported():
    """
    Kiểm tra cơ chế timing dự phòng (fallback timing):
    - Khi provider không hỗ trợ word timing, hệ thống phải kích hoạt TimingEstimator.
    - Bắt buộc đánh dấu is_fallback=True.
    - timing_level phải là fallback_estimated.
    - Không được giả vờ là timing chính xác.
    """
    tts_no_word = MockTTSProvider(supports_word_timing=False)
    text = "Đoạn văn này kiểm tra fallback timing. Nếu provider không có word boundary thì phải ước lượng rõ ràng."

    timing = await tts_no_word.get_timing(text)

    assert timing.is_fallback is True
    assert timing.timing_level == "fallback_estimated"
    assert timing.fallback_reason is not None
    assert "supports_word_timing=False" in timing.fallback_reason

    # Danh sách từ vẫn được ước lượng đầy đủ và có thời gian tăng dần
    assert len(timing.words) > 0
    for w in timing.words:
        assert w.confidence == 0.5  # Phản ánh tính chất ước lượng
        assert w.end_time > w.start_time

    assert len(timing.sentences) >= 2


@pytest.mark.asyncio
async def test_voice_selection_and_validation():
    """Kiểm tra lựa chọn giọng đọc hợp lệ và từ chối giọng không tồn tại."""
    tts = MockTTSProvider()
    valid_voices = tts.get_supported_voices()
    assert "vi-VN-HoaiMyNeural" in valid_voices
    assert "en-US-AriaNeural" in valid_voices

    # 1. Giọng hợp lệ -> thành công
    cfg_valid = VoiceConfig(voice_id="vi-VN-NamMinhNeural")
    res = await tts.generate("Xin chào bạn", cfg_valid)
    assert res.voice_config.voice_id == "vi-VN-NamMinhNeural"

    # 2. Giọng không hợp lệ -> ném lỗi InvalidVoiceError
    cfg_invalid = VoiceConfig(voice_id="alien_voice_unknown_999")
    with pytest.raises(InvalidVoiceError) as exc_info:
        await tts.generate("Xin chào", cfg_invalid)
    assert "alien_voice_unknown_999" in str(exc_info.value)


@pytest.mark.asyncio
async def test_failure_retry_and_fallback():
    """
    Kiểm tra cơ chế chịu lỗi (resilience):
    - Primary provider lỗi tạm thời (2 lần) -> ResilientTTSProvider thử lại và thành công.
    - Primary provider chết hẳn -> Tự động kích hoạt Fallback provider.
    """
    # 1. Thử lại thành công sau 2 lần lỗi
    primary_with_transient_error = MockTTSProvider(fail_times=2)
    resilient_tts = ResilientTTSProvider(
        primary_provider=primary_with_transient_error,
        max_retries=2,
        initial_delay=0.01,
    )
    res1 = await resilient_tts.generate("Kiểm thử retry tự động.")
    assert res1.duration > 0.0

    # 2. Chuyển hướng sang fallback khi primary thất bại vượt ngưỡng retry
    primary_fatal = MockTTSProvider(fail_times=10)
    secondary_fallback = MockTTSProvider(char_per_sec=16.0)
    resilient_fallback_tts = ResilientTTSProvider(
        primary_provider=primary_fatal,
        fallback_provider=secondary_fallback,
        max_retries=1,
        initial_delay=0.01,
    )
    res2 = await resilient_fallback_tts.generate("Kiểm thử fallback provider.")
    assert res2.duration > 0.0
    assert res2.metadata.get("resilient_fallback_active") is True


@pytest.mark.asyncio
async def test_preview_generation():
    """Kiểm tra preview chỉ sinh mẫu âm thanh ngắn phục vụ kiểm duyệt nhanh."""
    tts = MockTTSProvider()
    long_narrative = (
        "Đây là câu mở đầu của câu chuyện. "
        "Sau đó là phần thân bài rất dài chứa nhiều nội dung chi tiết. "
        "Cuối cùng là phần kết luận tóm tắt bài học."
    )
    preview_res = await tts.preview(long_narrative)
    full_res = await tts.generate(long_narrative)

    assert preview_res.duration < full_res.duration
    assert preview_res.metadata.get("preview_mode") is True


@pytest.mark.asyncio
async def test_narration_agent_integration():
    """Kiểm tra NarrationAgent phối hợp với TTSProvider tính toán timeline segments chuẩn xác."""
    tts = MockTTSProvider(char_per_sec=15.0)
    agent = NarrationAgent(tts=tts)

    context = AgentContext(
        project_id="proj_tts_test",
        project_title="Monkey Tree Story",
        prompt="Kịch bản câu chuyện chú khỉ",
        shared_state={
            "segments": [
                {"id": "seg_1", "text": "Ngày xửa ngày xưa, trong một khu rừng nhiệt đới xanh mát."},
                {"id": "seg_2", "text": "Có một chú khỉ con thông minh đang leo trèo trên ngọn cây dừa."},
                {"id": "seg_3", "text": "Chú phát hiện ra một nải chuối chín vàng ươm thơm lừng."},
            ],
            "voice_config": {
                "voiceId": "vi-VN-HoaiMyNeural",
                "language": "vi-VN",
                "speed": 1.0,
            },
        },
    )

    result = await agent.run(context)
    assert result.success is True

    segments = result.data["narration_segments"]
    assert len(segments) == 3
    assert result.data["total_duration_sec"] > 0

    # Kiểm tra timeline liên tục không bị đứt đoạn hoặc giẫm đạp mốc thời gian
    curr_ms = 0
    for seg in segments:
        assert seg["start_ms"] == curr_ms
        assert seg["end_ms"] > seg["start_ms"]
        assert seg["duration_ms"] == seg["end_ms"] - seg["start_ms"]
        curr_ms = seg["end_ms"]

    assert result.data["total_duration_ms"] == curr_ms


@pytest.mark.asyncio
async def test_audio_result_save_to_file(tmp_path):
    """Kiểm tra ghi dữ liệu audio file ra đĩa và cập nhật audio_path."""
    tts = MockTTSProvider()
    res = await tts.generate("Kiểm thử ghi file audio.")
    output_file = tmp_path / "narration_test.wav"

    saved_path = res.save_to_file(output_file)
    assert saved_path.exists()
    assert saved_path.stat().st_size == len(res.audio_bytes)
    assert res.audio_path == saved_path
