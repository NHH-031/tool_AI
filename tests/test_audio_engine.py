"""
Unit tests for Core Audio Engine (Phase 1).
Tests AudioMixer, Auto-Ducking envelope computation, and DrawingSFXSynchronizer.
"""

from pathlib import Path
import numpy as np
import pytest

from core.audio.mixer import AudioMixer, mix_audio_with_bgm
from core.audio.sfx_sync import DrawingSFXSynchronizer, generate_drawing_sfx_track


def test_audio_mixer_ducking_envelope():
    sr = 44100
    mixer = AudioMixer(sample_rate=sr)

    # 4 seconds total:
    # 0s - 1s: Speech active (sine 400Hz, amp 0.5)
    # 1s - 2.5s: Silence
    # 2.5s - 3.5s: Speech active
    # 3.5s - 4.0s: Silence
    dur = 4.0
    total_samples = int(dur * sr)
    speech = np.zeros((2, total_samples), dtype=np.float32)

    t1 = np.linspace(0, 1.0, int(1.0 * sr), endpoint=False)
    sig1 = np.sin(2 * np.pi * 400 * t1).astype(np.float32) * 0.5
    speech[:, : len(sig1)] = sig1

    idx2_start = int(2.5 * sr)
    idx2_end = int(3.5 * sr)
    t2 = np.linspace(0, 1.0, idx2_end - idx2_start, endpoint=False)
    sig2 = np.sin(2 * np.pi * 400 * t2).astype(np.float32) * 0.5
    speech[:, idx2_start:idx2_end] = sig2

    duck_ratio = 0.35
    envelope = mixer.compute_ducking_envelope(speech, duck_ratio=duck_ratio)

    assert len(envelope) == total_samples
    assert np.all(envelope >= duck_ratio - 0.05)
    assert np.all(envelope <= 1.05)

    # During speech active (at 0.5s), gain should be ducked near duck_ratio
    sample_at_05s = int(0.5 * sr)
    assert envelope[sample_at_05s] < 0.55

    # During silence (at 2.0s), gain should have recovered near 1.0
    sample_at_20s = int(2.0 * sr)
    assert envelope[sample_at_20s] > 0.85


def test_audio_mixer_loop_and_fit_bgm():
    sr = 44100
    mixer = AudioMixer(sample_rate=sr)

    # BGM is 2 seconds
    bgm = np.ones((2, 2 * sr), dtype=np.float32) * 0.5

    # Target is 5 seconds (requires looping)
    target_samples = 5 * sr
    fitted = mixer.loop_and_fit_bgm(bgm, target_samples, fade_out_sec=1.0)

    assert fitted.shape == (2, target_samples)
    # End should be faded to 0
    assert abs(fitted[0, -1]) < 0.05


def test_drawing_sfx_synchronizer():
    sr = 44100
    syncer = DrawingSFXSynchronizer(sample_rate=sr)

    scenes = [
        {"duration_sec": 4.0},
        {"duration_sec": 6.0},
    ]
    total_dur = 10.0
    track = syncer.generate_sfx_track_for_scenes(
        scenes_timing=scenes,
        total_duration_sec=total_dur,
        sfx_name="marker_draw",
        draw_ratio=0.85,
    )

    assert track.shape == (2, int(total_dur * sr))

    # At 3.0s (within scene 1 drawing interval 0-3.4s), SFX should be active (non-zero)
    idx_draw = int(2.0 * sr)
    assert np.max(np.abs(track[:, idx_draw : idx_draw + 1000])) > 0.0001

    # At 3.8s (during scene 1 pause interval 3.4s - 4.0s), SFX should be silent
    idx_pause = int(3.8 * sr)
    assert np.max(np.abs(track[:, idx_pause : idx_pause + 500])) < 0.01


def test_full_mix_pipeline(tmp_path: Path):
    sr = 44100
    mixer = AudioMixer(sample_rate=sr)

    speech_file = tmp_path / "speech.wav"
    bgm_file = tmp_path / "bgm.wav"
    out_file = tmp_path / "master_mix.aac"

    # Create dummy speech & BGM
    t = np.linspace(0, 3.0, 3 * sr, endpoint=False)
    s_sig = np.sin(2 * np.pi * 300 * t).astype(np.float32) * 0.6
    b_sig = np.sin(2 * np.pi * 600 * t).astype(np.float32) * 0.4

    mixer.write_audio(np.vstack([s_sig, s_sig]), speech_file)
    mixer.write_audio(np.vstack([b_sig, b_sig]), bgm_file)

    mix_audio_with_bgm(
        speech_path=speech_file,
        bgm_path=bgm_file,
        output_path=out_file,
        bgm_volume=0.2,
        ducking=True,
    )

    assert out_file.exists()
    assert out_file.stat().st_size > 1000

    read_back, r_sr = mixer.read_audio(out_file)
    assert read_back.shape[0] == 2
    assert read_back.shape[1] > 0
    assert np.max(np.abs(read_back)) <= 1.0
