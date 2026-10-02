from __future__ import annotations

import re
from typing import List, Optional
from core.schemas.tts import NarrationTiming, SentenceTiming, WordTiming


class TimingEstimator:
    """
    Ước lượng thời điểm phát âm từng câu và từng từ khi provider không hỗ trợ native word-level alignment.
    Đảm bảo quy tắc:
    - Bắt buộc đánh dấu is_fallback = True
    - Đặt timing_level = 'fallback_estimated' hoặc 'sentence' / 'segment'
    - Tuyệt đối không giả vờ là timing chính xác
    """

    @classmethod
    def estimate_timing(
        cls,
        text: str,
        total_duration: float,
        start_offset: float = 0.0,
        timing_level: str = "fallback_estimated",
        fallback_reason: Optional[str] = "Provider does not provide native word-level alignment; calculated via weighted acoustic estimation.",
    ) -> NarrationTiming:
        """
        Ước lượng mốc thời gian chi tiết cho từng câu và từng từ dựa trên trọng số độ dài và dấu câu.
        """
        clean_text = text.strip()
        if not clean_text or total_duration <= 0:
            return NarrationTiming(
                text=clean_text,
                duration=max(0.0, total_duration),
                timing_level="fallback_estimated",
                is_fallback=True,
                fallback_reason=fallback_reason or "Empty text or zero duration",
                words=[],
                sentences=[],
            )

        # 1. Tách văn bản thành các câu
        raw_sentences = re.split(r"(?<=[.!?;\n])\s+", clean_text)
        raw_sentences = [s.strip() for s in raw_sentences if s.strip()]
        if not raw_sentences:
            raw_sentences = [clean_text]

        # 2. Tính trọng số cho từng câu và từng từ
        # Trọng số dựa trên số ký tự + phụ phí ngắt nghỉ của dấu câu
        sentence_weights: List[float] = []
        sentence_word_lists: List[List[str]] = []

        for s in raw_sentences:
            words = [w for w in re.split(r"\s+", s) if w]
            sentence_word_lists.append(words)
            # Trọng số độ dài từ + thời gian ngắt câu
            char_count = sum(len(w) for w in words)
            pause_penalty = 8.0 if any(s.endswith(p) for p in [".", "!", "?", "\n"]) else 4.0
            weight = max(1.0, char_count + pause_penalty)
            sentence_weights.append(weight)

        total_weight = sum(sentence_weights)
        if total_weight <= 0:
            total_weight = 1.0

        # 3. Phân bổ thời lượng cho từng câu
        sentences_timing: List[SentenceTiming] = []
        all_words_timing: List[WordTiming] = []

        current_time = start_offset
        for i, s in enumerate(raw_sentences):
            s_weight = sentence_weights[i]
            s_duration = total_duration * (s_weight / total_weight)
            s_start = current_time
            s_end = s_start + s_duration

            words = sentence_word_lists[i]
            s_words_timing: List[WordTiming] = []

            if words:
                # Phân bổ thời lượng các từ trong câu dựa trên số ký tự
                word_weights = [max(1.0, float(len(w))) for w in words]
                # Thêm pause weight cho từ có dấu phẩy hoặc chấm
                for idx, w in enumerate(words):
                    if w.endswith(",") or w.endswith(";"):
                        word_weights[idx] += 3.0

                w_total_weight = sum(word_weights)
                w_current_time = s_start

                for idx, w in enumerate(words):
                    w_weight = word_weights[idx]
                    w_duration = s_duration * (w_weight / w_total_weight)
                    w_start = w_current_time
                    w_end = w_start + w_duration

                    wt = WordTiming(
                        word=w,
                        start_time=round(w_start, 3),
                        end_time=round(w_end, 3),
                        duration=round(w_duration, 3),
                        confidence=0.5,  # 0.5 phản ánh tính chất ước lượng
                    )
                    s_words_timing.append(wt)
                    all_words_timing.append(wt)
                    w_current_time = w_end

            st = SentenceTiming(
                sentence=s,
                start_time=round(s_start, 3),
                end_time=round(s_end, 3),
                duration=round(s_duration, 3),
                words=s_words_timing,
            )
            sentences_timing.append(st)
            current_time = s_end

        return NarrationTiming(
            text=clean_text,
            duration=round(total_duration, 3),
            timing_level=timing_level if timing_level in ["word", "sentence", "segment", "fallback_estimated"] else "fallback_estimated",
            is_fallback=True,
            fallback_reason=fallback_reason,
            words=all_words_timing,
            sentences=sentences_timing,
        )
