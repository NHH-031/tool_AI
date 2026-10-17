from __future__ import annotations

import logging
import uuid
import re
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.artwork.gemini_director import GeminiScriptDirector, StoryboardScene

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scripts", tags=["Scripts"])


class AnalyzeScriptRequest(BaseModel):
    text: str = Field(min_length=1, description="Văn bản hoặc phụ đề SRT cần phân tích")
    input_mode: str = Field(default="TEXT", description="'TEXT' hoặc 'SRT'")
    target_scenes: Optional[int] = Field(default=None, description="Số phân cảnh mong muốn")
    target_duration_sec: Optional[float] = Field(default=60.0, description="Thời lượng tổng (giây)")
    has_color: bool = Field(default=True, description="Vẽ có màu hay nét mực đơn sắc")


class SceneResponse(BaseModel):
    id: str
    scene_index: int
    title: str
    text: str
    prompt: str
    duration_sec: float
    image_status: str = "idle"
    audio_status: str = "idle"


class AnalyzeScriptResponse(BaseModel):
    title: str
    scenes: List[SceneResponse]


def _parse_srt_to_scenes(srt_text: str) -> List[SceneResponse]:
    """Parse text formatted as SRT into separate scenes."""
    blocks = re.split(r"\n\s*\n", srt_text.strip())
    scenes: List[SceneResponse] = []
    idx = 1
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        # Check if line 0 is a number
        start_idx = 1 if lines[0].isdigit() and len(lines) > 1 else 0
        if start_idx < len(lines) and "-->" in lines[start_idx]:
            # Has timing
            timing_line = lines[start_idx]
            content = " ".join(lines[start_idx + 1:])
            # Estimate duration from srt timing if possible
            match = re.search(r"(\d+):(\d+):(\d+)[,\.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,\.](\d+)", timing_line)
            if match:
                s_h, s_m, s_s, s_ms = map(int, match.groups()[:4])
                e_h, e_m, e_s, e_ms = map(int, match.groups()[4:])
                start_sec = s_h * 3600 + s_m * 60 + s_s + s_ms / 1000.0
                end_sec = e_h * 3600 + e_m * 60 + e_s + e_ms / 1000.0
                dur = max(2.0, round(end_sec - start_sec, 2))
            else:
                dur = max(3.0, round(len(content.split()) / 2.6, 1))
        else:
            content = " ".join(lines)
            dur = max(3.0, round(len(content.split()) / 2.6, 1))

        if content:
            prompt = (
                f"Whiteboard doodle illustration of {content[:60]}, "
                f"crisp clean dark ink contour outlines on warm vintage cream paper #F5EBD7, "
                f"high detail, masterpiece quality, 1080p widescreen, no text"
            )
            scenes.append(
                SceneResponse(
                    id=f"scene-{idx}",
                    scene_index=idx,
                    title=f"Cảnh {idx}",
                    text=content,
                    prompt=prompt,
                    duration_sec=dur,
                )
            )
            idx += 1
    return scenes


def _fallback_local_split(text: str, target_scenes: Optional[int] = None) -> List[SceneResponse]:
    """Phân chia kịch bản bằng logic câu/đoạn tự nhiên và tự động dịch prompt tiếng Anh chuẩn SKILL.md."""
    # 1. Kiểm tra xem văn bản có phân theo đoạn văn (paragraphs) rõ ràng không
    paragraphs = [p.strip() for p in text.splitlines() if len(p.strip()) > 30]
    if len(paragraphs) in [2, 3, 4, 5, 6, 7] and not target_scenes:
        raw_chunks = paragraphs
    else:
        # Tách câu theo dấu chấm, chấm hỏi, chấm than
        sentences = [s.strip() for s in re.split(r"[.!?\n]+", text) if s.strip()]
        if not sentences:
            sentences = [text.strip()]

        total_sentences = len(sentences)
        if target_scenes and target_scenes > 0:
            count = min(target_scenes, total_sentences)
        else:
            # Nhóm 2-3 câu mỗi cảnh
            count = max(1, (total_sentences + 1) // 2)

        chunk_size = max(1, (total_sentences + count - 1) // count)
        raw_chunks = []
        for i in range(count):
            chunk = sentences[i * chunk_size : (i + 1) * chunk_size]
            if chunk:
                raw_chunks.append(". ".join(chunk) + ".")

    scenes: List[SceneResponse] = []
    for i, scene_text in enumerate(raw_chunks, 1):
        dur = max(3.5, round(len(scene_text.split()) / 2.6, 1))

        # 2. Tạo prompt tiếng Anh chuẩn Notion/Storybook thay vì để nguyên tiếng Việt thô
        prompt_en = None
        try:
            from core.artwork.gemini_director import GeminiScriptDirector
            if GeminiScriptDirector.is_available():
                prompt_en = GeminiScriptDirector.create_single_scene_prompt(scene_text)
        except Exception as e_p:
            logger.warning(f"[_fallback_local_split] Could not translate scene {i} via Gemini: {e_p}")

        if not prompt_en:
            prompt_en = (
                f"Masterpiece storybook watercolor and ink illustration, crisp expressive dark ink contours "
                f"and rich vibrant harmonious colors on warm vintage cream paper #F5EBD7. "
                f"Whiteboard doodle line art representing narrative scene {i}. "
                f"Clear distinct contour lines, smooth connected ink outlines, rich watercolor fills, high detail, 1080p widescreen, no text"
            )

        scenes.append(
            SceneResponse(
                id=f"scene-{i}",
                scene_index=i,
                title=f"Phân cảnh {i}",
                text=scene_text,
                prompt=prompt_en,
                duration_sec=dur,
            )
        )

    return scenes


@router.post("/analyze", response_model=AnalyzeScriptResponse)
async def analyze_script(req: AnalyzeScriptRequest) -> AnalyzeScriptResponse:
    """
    Phân tích kịch bản nhập vào:
    1. Hỗ trợ SRT (tách theo timestamp)
    2. Hỗ trợ LLM Director (Gemini hoặc Ollama Local)
    3. Tự động gắn prompt chuẩn SKILL.md (#F5EBD7, dark ink)
    """
    raw = req.text.strip()
    if not raw:
        raise HTTPException(status_code=400, detail="Vui lòng nhập nội dung kịch bản")

    # Mode 1: SRT
    if req.input_mode.upper() == "SRT" or ("-->" in raw and any(line.isdigit() for line in raw.splitlines()[:3])):
        scenes = _parse_srt_to_scenes(raw)
        title = scenes[0].text[:30] + "..." if scenes else "Kịch bản SRT"
        return AnalyzeScriptResponse(title=title, scenes=scenes)

    # Mode 2: Check director (Gemini hoặc local Ollama)
    try:
        # Thử kiểm tra Ollama Director trước nếu cài đặt, nếu không dùng GeminiDirector
        scenes_data: List[StoryboardScene] = []
        try:
            from core.artwork.ollama_director import OllamaDirector
            if OllamaDirector.is_available():
                scenes_data = OllamaDirector.create_storyboard(
                    raw,
                    target_scenes=req.target_scenes,
                    target_duration_sec=req.target_duration_sec or 60.0,
                    has_color=req.has_color,
                )
        except ImportError:
            pass

        if not scenes_data and GeminiScriptDirector.is_available():
            scenes_data = GeminiScriptDirector.create_storyboard(
                raw,
                target_scenes=req.target_scenes,
                target_duration_sec=req.target_duration_sec or 60.0,
                has_color=req.has_color,
            )

        if scenes_data:
            formatted_scenes = [
                SceneResponse(
                    id=f"scene-{s.scene_index}",
                    scene_index=s.scene_index,
                    title=s.title,
                    text=s.narration,
                    prompt=s.visual_prompt,
                    duration_sec=s.estimated_duration_sec,
                )
                for s in scenes_data
            ]
            return AnalyzeScriptResponse(title=raw[:30] + "...", scenes=formatted_scenes)
    except Exception as e:
        logger.warning(f"[analyze_script] Director error: {e}. Using local heuristic splitter.")

    # Fallback: Heuristic sentence splitter (2-3 sentences/scene)
    scenes = _fallback_local_split(raw, target_scenes=req.target_scenes)
    return AnalyzeScriptResponse(title=raw[:30] + "...", scenes=scenes)
