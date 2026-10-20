"""
Auto-Translator: Dịch kịch bản tiếng Việt sang tiếng Anh tự động không cần API key.
Hỗ trợ đa tầng fallback:
1. Gemini Director (nếu có GEMINI_API_KEY)
2. deep-translator (MyMemory / Google Web Translator miễn phí)
3. Dictionary & Pattern-based Fallback ngoại tuyến
"""

from __future__ import annotations

import logging
import re
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Cache nội bộ tránh gọi dịch lại nhiều lần cùng một câu
_TRANSLATION_CACHE: Dict[str, str] = {}

# Từ điển ánh xạ từ vựng khoa học / phổ biến làm fallback ngoại tuyến
_OFFLINE_VI_EN_DICT: Dict[str, str] = {
    "pin năng lượng mặt trời": "solar panels",
    "mặt trời": "sun",
    "ánh sáng": "sunlight",
    "ngôi nhà": "house",
    "robot": "robot",
    "tinh thể silic": "silicon crystals",
    "electron": "electrons",
    "dòng điện": "electrical current",
    "biến tần": "inverter",
    "dòng điện xoay chiều": "alternating current",
    "dòng điện một chiều": "direct current",
    "con người": "person",
    "họa sĩ": "artist",
    "bảng trắng": "whiteboard",
    "trường học": "school classroom",
    "học sinh": "students",
    "thầy giáo": "teacher",
    "cây cối": "trees and nature",
    "thành phố": "modern city",
    "vũ trụ": "outer space and stars",
}


def _clean_text_for_prompt(text: str) -> str:
    """Loại bỏ ký tự đặc biệt thừa, chuẩn hóa khoảng trắng."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned


def auto_translate_vi_to_en(text: str, max_chars: int = 500) -> str:
    """
    Dịch tự động văn bản tiếng Việt sang tiếng Anh cho việc sinh hình ảnh Whiteboard.
    Hoàn toàn an toàn, không bao giờ ném Exception, tự động chuyển tầng fallback.
    """
    if not text or not text.strip():
        return ""

    text = _clean_text_for_prompt(text)[:max_chars]

    # Kiểm tra cache
    if text in _TRANSLATION_CACHE:
        return _TRANSLATION_CACHE[text]

    # 1. Thử qua deep-translator MyMemory (nhanh, miễn phí, không cần API key)
    try:
        from deep_translator import MyMemoryTranslator
        translator = MyMemoryTranslator(source="vi-VN", target="en-GB")
        res = translator.translate(text)
        if res and isinstance(res, str) and len(res.strip()) > 0:
            cleaned = _clean_text_for_prompt(res)
            if "MYMEMORY WARNING" not in cleaned.upper() and len(cleaned) > 2:
                _TRANSLATION_CACHE[text] = cleaned
                return cleaned
    except Exception as e_mymemory:
        logger.debug(f"[Translator] MyMemory pass: {e_mymemory}")

    # 2. Thử qua deep-translator GoogleTranslator
    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source="vi", target="en")
        res = translator.translate(text)
        if res and isinstance(res, str) and len(res.strip()) > 0:
            cleaned = _clean_text_for_prompt(res)
            _TRANSLATION_CACHE[text] = cleaned
            return cleaned
    except Exception as e_google:
        logger.debug(f"[Translator] GoogleTranslator pass: {e_google}")

    # 3. Thử Gemini nếu có API key
    try:
        from core.artwork.gemini_director import GeminiScriptDirector
        if GeminiScriptDirector.is_available():
            translated = GeminiScriptDirector.create_single_scene_prompt(text)
            if translated and len(translated.strip()) > 10:
                _TRANSLATION_CACHE[text] = translated
                return translated
    except Exception as e_gemini:
        logger.debug(f"[Translator] Gemini pass: {e_gemini}")

    # 4. Fallback ngoại tuyến: Tra cứu từ điển nội bộ và trích xuất thực thể
    text_lower = text.lower()
    matched_terms = []
    for vi_term, en_term in _OFFLINE_VI_EN_DICT.items():
        if vi_term in text_lower:
            matched_terms.append(en_term)

    if matched_terms:
        fallback_translated = f"narrative concept depicting {', '.join(matched_terms)}"
    else:
        # Nếu không có từ khóa nào khớp, tạo mô tả ngữ cảnh khái quát
        fallback_translated = "detailed conceptual visualization of the narrative story"

    _TRANSLATION_CACHE[text] = fallback_translated
    return fallback_translated


def create_whiteboard_art_prompt(scene_text_vi: str, scene_index: int = 1, aspect_ratio: str = "16:9") -> str:
    """
    Tạo prompt hình ảnh hoàn chỉnh với phong cách Comic Doodle Whiteboard từ kịch bản tiếng Việt,
    sử dụng auto_translate_vi_to_en để diễn đạt chính xác nội dung phân cảnh.
    """
    translated_subject = auto_translate_vi_to_en(scene_text_vi)
    
    aspect_desc = "9:16 vertical composition for mobile" if aspect_ratio == "9:16" else "16:9 widescreen composition"

    prompt = (
        f"Masterpiece storybook watercolor and ink illustration of {translated_subject}, {aspect_desc}. "
        f"Crisp expressive dark ink contours, smooth connected outlines, and rich vibrant harmonious watercolor fills "
        f"on warm vintage cream paper #F5EBD7. Traditional 2D vintage comic book and whiteboard doodle illustration, "
        f"strictly 2D flat art, no 3D render, no CGI, no text, no speech bubbles, no watermark."
    )
    return prompt
