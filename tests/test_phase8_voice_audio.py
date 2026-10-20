import asyncio
import base64
import io
import math
import struct
import wave
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np

from core.audio.mixer import AudioMixer
from core.tts.elevenlabs import ElevenLabsTTSProvider, ELEVENLABS_VOICE_MAP
from core.schemas.tts import VoiceConfig, TTSAudioResult
from apps.api.routers.voices import (
    VOICES_CATALOG,
    UploadCustomAudioRequest,
    upload_custom_audio,
)
from apps.api.routers.music import (
    MUSIC_CATALOG,
    UploadCustomBgmRequest,
    upload_custom_bgm,
)
from apps.api.routers.export import ExportSceneItem, RenderExportRequest


def _create_synthetic_wav_bytes(duration_sec: float = 1.0, freq: float = 440.0, sample_rate: int = 44100) -> bytes:
    """Tạo file WAV sóng sin giả lập để test upload và decoding."""
    buf = io.BytesIO()
    num_samples = int(sample_rate * duration_sec)
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for i in range(num_samples):
            val = int(32767.0 * 0.5 * math.sin(2.0 * math.pi * freq * i / sample_rate))
            frames.extend(struct.pack("<h", val))
        wf.writeframes(frames)
    return buf.getvalue()


# =============================================================================
# TASK 8.4: ELEVENLABS TTS PROVIDER TESTS
# =============================================================================

def test_elevenlabs_supported_voices():
    provider = ElevenLabsTTSProvider()
    voices = provider.get_supported_voices()
    assert "eleven-adam" in voices
    assert "eleven-rachel" in voices
    assert "eleven-antoni" in voices
    assert provider._resolve_voice_id("eleven-adam") == "pNInz6obpgDQGcFmaJgB"
    assert provider._resolve_voice_id("custom-voice") == "custom-voice"


@pytest.mark.asyncio
async def test_elevenlabs_fallback_when_no_api_key():
    """Khi không có API key, ElevenLabs provider tự động ủy thác sang fallback provider."""
    mock_fallback = AsyncMock()
    mock_result = TTSAudioResult(
        audio_bytes=b"fallback_bytes",
        duration=2.5,
        duration_ms=2500,
        format="mp3",
        sample_rate=24000,
        voice_config=VoiceConfig(voice_id="vi-VN-HoaiMyNeural"),
    )
    mock_fallback.generate.return_value = mock_result

    provider = ElevenLabsTTSProvider(api_key="", fallback_provider=mock_fallback)
    result = await provider.generate("Xin chào bạn", VoiceConfig(voice_id="eleven-rachel"))

    assert result == mock_result
    assert mock_fallback.generate.called


@pytest.mark.asyncio
async def test_elevenlabs_generate_with_mocked_api():
    """Khi có API key, ElevenLabs provider gọi HTTP POST với đúng headers và payload."""
    test_wav = _create_synthetic_wav_bytes(duration_sec=1.5)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = test_wav

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch("core.tts.elevenlabs.httpx.AsyncClient", return_value=mock_client):
        provider = ElevenLabsTTSProvider(api_key="test_xi_key_123")
        result = await provider.generate("Thử nghiệm giọng đọc biểu cảm", VoiceConfig(voice_id="eleven-adam", speed=1.0))


        assert result.audio_bytes == test_wav
        assert result.format == "mp3"
        assert result.duration > 0.5
        assert result.timing is not None

        # Kiểm tra call arguments
        call_args = mock_client.post.call_args
        assert "pNInz6obpgDQGcFmaJgB" in call_args[0][0]
        assert call_args[1]["headers"]["xi-api-key"] == "test_xi_key_123"
        payload = call_args[1]["json"]
        assert payload["model_id"] == "eleven_multilingual_v2"
        assert "voice_settings" in payload


# =============================================================================
# TASK 8.3: AUDIO TRIMMER & MIXER TESTS
# =============================================================================

def test_bgm_trimmer_and_offset():
    """Kiểm tra cắt đoạn bắt đầu theo start_offset_sec và áp dụng fade-in/fade-out."""
    mixer = AudioMixer(sample_rate=1000)  # Dùng 1kHz cho test nhanh
    
    # Tạo bản nhạc BGM dài 10 giây (10,000 samples)
    t = np.linspace(0, 10, 10000, dtype=np.float32)
    bgm_raw = np.tile(np.sin(2 * np.pi * 5 * t), (2, 1))

    # Cắt bắt đầu từ giây thứ 2.0 (2,000 samples) và fit vào 4.0 giây video (4,000 samples)
    fitted = mixer.loop_and_fit_bgm(
        bgm_arr=bgm_raw,
        target_samples=4000,
        start_offset_sec=2.0,
        fade_in_sec=0.5,
        fade_out_sec=1.0,
    )

    assert fitted.shape == (2, 4000)
    # Tại thời điểm t=0 của video (mẫu đầu tiên), âm lượng đã được fade-in nên tiến về 0
    assert abs(fitted[0, 0]) < 0.05
    # Tại thời điểm cuối video (mẫu cuối cùng), âm lượng đã được fade-out nên tiến về 0
    assert abs(fitted[0, -1]) < 0.05


def test_mix_multi_track_with_trimmer():
    """Kiểm tra trộn đa luồng có tham số trimmer không gây lỗi và bảo toàn sample count."""
    mixer = AudioMixer(sample_rate=1000)
    speech = np.ones((2, 3000), dtype=np.float32) * 0.5
    bgm = np.ones((2, 6000), dtype=np.float32) * 0.4
    sfx = np.ones((2, 1000), dtype=np.float32) * 0.2

    mixed = mixer.mix_multi_track(
        speech_arr=speech,
        bgm_arr=bgm,
        sfx_arr=sfx,
        bgm_volume=0.15,
        sfx_volume=0.20,
        enable_ducking=True,
        bgm_start_offset=1.0,
        bgm_fade_in_sec=0.2,
        bgm_fade_out_sec=0.5,
    )

    assert mixed.shape == (2, 3000)
    assert not np.isnan(mixed).any()
    # Kiểm tra Soft-limiter bảo vệ peak
    assert np.max(np.abs(mixed)) <= 0.98


# =============================================================================
# TASK 8.2: CUSTOM VOICE & AUDIO UPLOAD ENDPOINT TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_upload_custom_audio_endpoint(tmp_path):
    """Kiểm tra upload file thu âm từ trình duyệt hoặc micro dưới dạng base64."""
    wav_bytes = _create_synthetic_wav_bytes(duration_sec=1.2)
    b64_str = f"data:audio/wav;base64,{base64.b64encode(wav_bytes).decode('utf-8')}"

    req = UploadCustomAudioRequest(
        project_id="test_phase8_proj",
        scene_id="sc_mic_1",
        scene_index=1,
        audio_data_base64=b64_str,
        filename="my_recording.wav",
        text="Xin chào các bạn đây là giọng thu âm thật",
    )

    resp = await upload_custom_audio(req)
    assert resp.scene_id == "sc_mic_1"
    assert resp.scene_index == 1
    assert resp.voice_id == "custom_upload"
    assert resp.status == "completed"
    assert resp.duration_sec >= 1.0
    assert "/media/storyboard/test_phase8_proj/" in resp.audio_url


# =============================================================================
# TASK 8.3: CUSTOM BGM UPLOAD ENDPOINT TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_upload_custom_bgm_endpoint():
    """Kiểm tra upload bài nhạc nền MP3 cá nhân và tự động cập nhật catalog."""
    wav_bytes = _create_synthetic_wav_bytes(duration_sec=2.0)
    b64_str = base64.b64encode(wav_bytes).decode("utf-8")

    req = UploadCustomBgmRequest(
        title="Bản Nhạc Nền Riêng Cho Video",
        audio_data_base64=b64_str,
        mood="Hứng Khởi",
        genre="Acoustic",
        recommended_volume=0.18,
    )

    track = await upload_custom_bgm(req)
    assert track.title == "Bản Nhạc Nền Riêng Cho Video"
    assert track.id.startswith("custom_")
    assert track.duration_sec >= 1
    assert track.preview_url == f"/music/{track.id}/preview"
    # Kiểm tra bài nhạc mới được chèn vào catalog
    assert any(m.id == track.id for m in MUSIC_CATALOG)


# =============================================================================
# TASK 8.1: MULTI-SPEAKER MODELS & VOICES CATALOG TESTS
# =============================================================================

def test_voices_catalog_contains_phase8_voices():
    """Kiểm tra catalog chứa cả giọng ElevenLabs biểu cảm cao cấp và EdgeTTS."""
    voice_ids = [v.id for v in VOICES_CATALOG]
    assert "eleven-rachel" in voice_ids
    assert "eleven-adam" in voice_ids
    assert "eleven-antoni" in voice_ids
    assert "vi-VN-HoaiMyNeural" in voice_ids
    assert "vi-VN-NamMinhNeural" in voice_ids


def test_export_request_with_multi_speaker_and_trimmer():
    """Kiểm tra model RenderExportRequest hỗ trợ voice_id riêng cho từng phân cảnh và BGM trimmer."""
    req = RenderExportRequest(
        project_id="p1",
        title="Multi-Speaker Story",
        scenes=[
            ExportSceneItem(
                id="s1",
                scene_index=1,
                text="[Nam]: Chào mừng bạn!",
                voice_id="vi-VN-NamMinhNeural",
                speed=1.0,
            ),
            ExportSceneItem(
                id="s2",
                scene_index=2,
                text="[Nữ]: Cảm ơn anh đã mời tôi.",
                voice_id="vi-VN-HoaiMyNeural",
                speed=1.1,
            ),
            ExportSceneItem(
                id="s3",
                scene_index=3,
                text="[Dẫn chuyện]: Câu chuyện bắt đầu từ đây...",
                voice_id="eleven-adam",
                speed=0.9,
            ),
        ],
        voice_id="vi-VN-Standard-B",
        speed=1.0,
        music_id="acoustic_uplift",
        music_volume=0.15,
        music_start_offset=4.5,
        music_fade_duration=2.5,
    )

    assert len(req.scenes) == 3
    assert req.scenes[0].voice_id == "vi-VN-NamMinhNeural"
    assert req.scenes[1].voice_id == "vi-VN-HoaiMyNeural"
    assert req.scenes[2].voice_id == "eleven-adam"
    assert req.music_start_offset == 4.5
    assert req.music_fade_duration == 2.5
