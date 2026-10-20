"""
Data models for Subtitles (SRT / VTT / Word Timing).
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class SubtitleWord(BaseModel):
    word: str
    start_sec: float
    end_sec: float
    duration: float = 0.0


class SubtitleSegment(BaseModel):
    index: int
    start_sec: float
    end_sec: float
    text: str
    words: List[SubtitleWord] = Field(default_factory=list)

    @property
    def duration_sec(self) -> float:
        return max(0.1, self.end_sec - self.start_sec)
