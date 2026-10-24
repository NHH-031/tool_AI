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

# Từ điển ánh xạ từ vựng khoa học / quân sự / phổ biến làm fallback ngoại tuyến
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
    "tầng tầng lớp lớp binh lính": "battalions of infantry soldier troops deployed across the terrain",
    "binh lính": "infantry soldiers",
    "chiếc dù": "military parachutes descending from the sky",
    "nhảy dù": "paratroopers descending with parachutes",
    "pháo đài": "military fortress outpost with soldiers",
    "dây thép gai": "barbed wire entanglements",
    "vũ khí": "military weapons and crates",
    "máy bay": "military transport airplanes",
    "làm rơi cốc nước": "person accidentally dropping a glass of water spilling droplets",
}


def _clean_text_for_prompt(text: str) -> str:
    """Loại bỏ ký tự đặc biệt thừa, chuẩn hóa khoảng trắng."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned


def auto_translate_vi_to_en(text: str, max_chars: int = 500) -> str:
    """
    Dịch tự động văn bản tiếng Việt sang tiếng Anh cho việc sinh hình ảnh Whiteboard.
    Hoàn toàn an toàn, không bao giờ ném Exception, tự động chuyển tầng fallback.
    Tier 1: Google Gemini (thấu hiểu ngữ cảnh, trích xuất đầy đủ đạo cụ/binh lính/chi tiết)
    Tier 2: deep-translator (MyMemory & Google Translator)
    Tier 3: Dictionary & Pattern-based Fallback ngoại tuyến
    """
    if not text or not text.strip():
        return ""

    text = _clean_text_for_prompt(text)[:max_chars]

    # Kiểm tra cache
    if text in _TRANSLATION_CACHE:
        return _TRANSLATION_CACHE[text]

    # 1. Tier 1: Thử Gemini nếu có API key (Hiểu sâu câu chuyện, không bỏ sót đồ vật hay binh lính)
    try:
        from core.artwork.gemini_director import GeminiScriptDirector
        if GeminiScriptDirector.is_available():
            # Chỉ dịch trích xuất nội dung thực thể
            from google import genai
            client = genai.Client(api_key=GeminiScriptDirector.get_api_key())
            prompt = (
                "Translate and extract visual narrative details from this Vietnamese scene into English for a 2D manga drawing. "
                "CRITICAL: Do NOT omit any characters, soldiers, objects, weapons, or actions mentioned. "
                "Output ONLY the English descriptive scene context, nothing else.\n"
                f"Vietnamese: {text}"
            )
            for m in GeminiScriptDirector.CANDIDATE_MODELS:
                try:
                    resp = client.models.generate_content(model=m, contents=prompt)
                    if resp and resp.text:
                        translated = _clean_text_for_prompt(resp.text)
                        if len(translated) > 5:
                            _TRANSLATION_CACHE[text] = translated
                            return translated
                except Exception:
                    continue
    except Exception as e_gemini:
        logger.debug(f"[Translator] Gemini pass: {e_gemini}")

    # 2. Tier 2a: Thử qua deep-translator MyMemory (nhanh, miễn phí, không cần API key)
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

    # 2. Tier 2b: Thử qua deep-translator GoogleTranslator
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

    # 3. Fallback ngoại tuyến: Tra cứu từ điển nội bộ và trích xuất thực thể
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
    Tạo prompt hình ảnh hoàn chỉnh với phong cách 2D Manga Whiteboard từ kịch bản tiếng Việt,
    sử dụng GeminiScriptDirector nếu có để bảo tồn 100% mọi chi tiết nhỏ (cốc nước rơi, binh lính, dù...).
    """
    try:
        from core.artwork.gemini_director import GeminiScriptDirector
        if GeminiScriptDirector.is_available():
            full_prompt = GeminiScriptDirector.create_single_scene_prompt(scene_text_vi)
            if full_prompt and len(full_prompt) > 20:
                if aspect_ratio == "9:16" and "9:16" not in full_prompt:
                    full_prompt = full_prompt.replace("1080p widescreen", "vertical 9:16 portrait composition for mobile display")
                return full_prompt
    except Exception as e:
        logger.debug(f"[create_whiteboard_art_prompt] Gemini director pass: {e}")

    translated_subject = auto_translate_vi_to_en(scene_text_vi)
    aspect_desc = "9:16 vertical composition for mobile" if aspect_ratio == "9:16" else "16:9 widescreen composition"

    prompt = (
        f"Masterpiece 2D Japanese manga illustration of {translated_subject}, {aspect_desc}. "
        f"Bold crisp black ink outlines with variable brush stroke thickness, clean flat cel-shaded coloring with muted earthy watercolor tones, "
        f"screentone-style halftone shading on warm vintage cream paper #F5EBD7. Traditional hand-drawn 2D manga panel art, "
        f"strictly 2D flat art, NO 3D render, NO CGI, NO plastic sheen, NO volumetric lighting, no text, no speech bubbles, no watermark."
    )
    return prompt
