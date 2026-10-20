"""
Core Subtitles Package for AI Whiteboard Video Studio.
Provides SRT/VTT generation and subtitle burn-in rendering (Classic and TikTok Karaoke styles).
"""

from .models import SubtitleSegment, SubtitleWord
from .srt_generator import SubtitleGenerator
from .burner import SubtitleBurner

__all__ = [
    "SubtitleSegment",
    "SubtitleWord",
    "SubtitleGenerator",
    "SubtitleBurner",
]
