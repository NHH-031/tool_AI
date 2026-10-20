"""
Core Audio Engine for AI Whiteboard Video Studio.
Provides high-fidelity audio mixing, auto-ducking, BGM looping, and drawing SFX synchronization.
"""

from .mixer import AudioMixer, mix_audio_with_bgm
from .sfx_sync import DrawingSFXSynchronizer, generate_drawing_sfx_track

__all__ = [
    "AudioMixer",
    "mix_audio_with_bgm",
    "DrawingSFXSynchronizer",
    "generate_drawing_sfx_track",
]
