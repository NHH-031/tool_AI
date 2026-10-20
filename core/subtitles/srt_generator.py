"""
Subtitle Generator: SRT and WebVTT format generator from WordBoundary and narration timing.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
from .models import SubtitleSegment, SubtitleWord


class SubtitleGenerator:
    """Bộ tạo phụ đề chuẩn SRT và WebVTT cho video Whiteboard."""

    @staticmethod
    def format_timestamp(seconds: float, vtt: bool = False) -> str:
        """Định dạng giây sang HH:MM:SS,mmm (SRT) hoặc HH:MM:SS.mmm (VTT)."""
        seconds = max(0.0, float(seconds))
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int(round((seconds - int(seconds)) * 1000))
        if millis >= 1000:
            millis = 999

        sep = "." if vtt else ","
        return f"{hours:02d}:{minutes:02d}:{secs:02d}{sep}{millis:03d}"

    @classmethod
    def create_segments_from_scene(
        cls,
        text: str,
        duration_sec: float,
        offset_sec: float = 0.0,
        words_timing: Optional[List[Any]] = None,
        max_words_per_segment: int = 7,
        start_index: int = 1,
    ) -> List[SubtitleSegment]:
        """
        Chia nhỏ lời thoại của một cảnh thành các đoạn phụ đề ngắn gọn (5-7 từ)
        với mốc thời gian chính xác theo từ (WordBoundary) hoặc nội suy thời gian.
        """
        clean_text = text.strip()
        if not clean_text:
            return []

        words_list: List[SubtitleWord] = []

        # 1. Trích xuất mốc thời gian từ words_timing nếu có
        if words_timing and len(words_timing) > 0:
            for w in words_timing:
                w_text = getattr(w, "word", None) or (w.get("word") if isinstance(w, dict) else str(w))
                w_start = getattr(w, "start_time", None) or (w.get("start_time") if isinstance(w, dict) else 0.0)
                w_end = getattr(w, "end_time", None) or (w.get("end_time") if isinstance(w, dict) else 0.0)
                dur = getattr(w, "duration", None) or (w.get("duration") if isinstance(w, dict) else (w_end - w_start))

                words_list.append(
                    SubtitleWord(
                        word=str(w_text).strip(),
                        start_sec=round(offset_sec + float(w_start), 3),
                        end_sec=round(offset_sec + float(w_end), 3),
                        duration=round(float(dur), 3),
                    )
                )

        # 2. Fallback nếu không có words_timing: tự chia đều theo số từ
        if not words_list:
            raw_tokens = clean_text.split()
            if not raw_tokens:
                return []
            per_word_sec = duration_sec / max(1, len(raw_tokens))
            for i, token in enumerate(raw_tokens):
                w_st = offset_sec + i * per_word_sec
                w_et = offset_sec + (i + 1) * per_word_sec
                words_list.append(
                    SubtitleWord(
                        word=token,
                        start_sec=round(w_st, 3),
                        end_sec=round(w_et, 3),
                        duration=round(per_word_sec, 3),
                    )
                )

        # 3. Gom nhóm từ thành các cụm phụ đề ngắn gọn dễ đọc
        segments: List[SubtitleSegment] = []
        cur_idx = start_index

        for i in range(0, len(words_list), max_words_per_segment):
            chunk = words_list[i : i + max_words_per_segment]
            if not chunk:
                continue

            seg_text = " ".join(w.word for w in chunk)
            seg_start = chunk[0].start_sec
            seg_end = chunk[-1].end_sec

            segments.append(
                SubtitleSegment(
                    index=cur_idx,
                    start_sec=seg_start,
                    end_sec=seg_end,
                    text=seg_text,
                    words=chunk,
                )
            )
            cur_idx += 1

        return segments

    @classmethod
    def generate_project_subtitles(
        cls,
        scenes_data: List[Dict[str, Any]],
        max_words_per_segment: int = 7,
    ) -> List[SubtitleSegment]:
        """
        Tổng hợp danh sách SubtitleSegment cho toàn bộ các phân cảnh trong video.
        """
        all_segments: List[SubtitleSegment] = []
        cur_offset = 0.0
        cur_index = 1

        for sc in scenes_data:
            text = sc.get("text", "")
            dur_sec = float(sc.get("duration_sec", 4.0))
            words_timing = sc.get("words_timing") or sc.get("timing", {}).get("words")

            sc_segments = cls.create_segments_from_scene(
                text=text,
                duration_sec=dur_sec,
                offset_sec=cur_offset,
                words_timing=words_timing,
                max_words_per_segment=max_words_per_segment,
                start_index=cur_index,
            )

            all_segments.extend(sc_segments)
            cur_index += len(sc_segments)
            cur_offset += dur_sec

        return all_segments

    @classmethod
    def to_srt(cls, segments: List[SubtitleSegment]) -> str:
        """Xuất danh sách phân đoạn sang định dạng file SubRip (.srt)."""
        lines = []
        for seg in segments:
            lines.append(str(seg.index))
            t_start = cls.format_timestamp(seg.start_sec, vtt=False)
            t_end = cls.format_timestamp(seg.end_sec, vtt=False)
            lines.append(f"{t_start} --> {t_end}")
            lines.append(seg.text)
            lines.append("")  # Blank line separator
        return "\n".join(lines)

    @classmethod
    def to_vtt(cls, segments: List[SubtitleSegment]) -> str:
        """Xuất danh sách phân đoạn sang định dạng WebVTT (.vtt)."""
        lines = ["WEBVTT", ""]
        for seg in segments:
            lines.append(str(seg.index))
            t_start = cls.format_timestamp(seg.start_sec, vtt=True)
            t_end = cls.format_timestamp(seg.end_sec, vtt=True)
            lines.append(f"{t_start} --> {t_end}")
            lines.append(seg.text)
            lines.append("")
        return "\n".join(lines)
