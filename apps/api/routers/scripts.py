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
    aspect_ratio: str = Field(default="16:9", description="Tỷ lệ khung hình: 16:9 hoặc 9:16")


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


def _parse_structured_scenes(text: str, target_scenes: Optional[int] = None, aspect_ratio: str = "16:9") -> List[SceneResponse]:
    """
    Phát hiện và phân tách kịch bản đã có sẵn cấu trúc phân cảnh:
    - PHÂN CẢNH 1: [Tiêu đề], PHÂN CẢNH 2: ...
    - CẢNH 1:, Cảnh 2:, SCENE 1:, Scene 1:, Hồi 1, Đoạn 1...
    """
    from core.artwork.translator import create_whiteboard_art_prompt

    pattern = re.compile(
        r"(?:^|\n)\s*(?:PHÂN\s+CẢNH|Phân\s+cảnh|CẢNH|Cảnh|SCENE|Scene|HỒI|Hồi|ĐOẠN|Đoạn)\s*(\d+)[\s:.-]*([^\n]*)\n?(.*?)(?=(?:\n\s*(?:PHÂN\s+CẢNH|Phân\s+cảnh|CẢNH|Cảnh|SCENE|Scene|HỒI|Hồi|ĐOẠN|Đoạn)\s*\d+[\s:.-]*)|\Z)",
        re.IGNORECASE | re.DOTALL,
    )
    matches = list(pattern.finditer(text.strip()))
    if not matches:
        return []

    scenes: List[SceneResponse] = []
    for i, m in enumerate(matches, 1):
        scene_num_str = m.group(1)
        scene_idx = int(scene_num_str) if scene_num_str.isdigit() else i
        raw_title = m.group(2).strip()
        body = m.group(3).strip()

        # Tách các dòng chỉ đạo bối cảnh/hình ảnh và lời thoại thuyết minh thực tế
        lines = [line.strip() for line in body.splitlines() if line.strip()]
        visual_cues: List[str] = []
        narration_lines: List[str] = []

        for line in lines:
            lower = line.lower()
            if any(lower.startswith(k) for k in ["bối cảnh:", "hình ảnh:", "mô tả:", "visual:", "setting:", "prompt:"]):
                cleaned_cue = re.sub(r"^(bối cảnh|hình ảnh|mô tả|visual|setting|prompt):\s*", "", line, flags=re.IGNORECASE)
                if cleaned_cue:
                    visual_cues.append(cleaned_cue)
            else:
                cleaned_narr = re.sub(r"^(lời thoại|thuyết minh|thoại|narration|audio):\s*", "", line, flags=re.IGNORECASE)
                if cleaned_narr:
                    narration_lines.append(cleaned_narr)

        narr_text = " ".join(narration_lines) if narration_lines else (" ".join(lines) if lines else f"Phân cảnh {scene_idx}")
        title_str = f"Phân cảnh {scene_idx}: {raw_title}" if raw_title else f"Phân cảnh {scene_idx}"

        prompt_context = f"{raw_title}. " if raw_title else ""
        if visual_cues:
            prompt_context += " ".join(visual_cues) + ". "
        prompt_context += narr_text

        prompt_en = create_whiteboard_art_prompt(prompt_context, scene_index=i, aspect_ratio=aspect_ratio)
        dur = max(3.5, round(len(narr_text.split()) / 2.6, 1))

        scenes.append(
            SceneResponse(
                id=f"scene-{i}",
                scene_index=i,
                title=title_str,
                text=narr_text,
                prompt=prompt_en,
                duration_sec=dur,
            )
        )
    return scenes


def _fallback_local_split(text: str, target_scenes: Optional[int] = None, aspect_ratio: str = "16:9") -> List[SceneResponse]:
    """
    Phân chia kịch bản bằng logic câu/đoạn tự nhiên và tự động dịch prompt tiếng Anh chuẩn SKILL.md.
    Đảm bảo đáp ứng chính xác target_scenes bằng thuật toán phân phối đều (bucket distribution).
    """
    from core.artwork.translator import create_whiteboard_art_prompt

    # Tách câu theo dấu chấm, chấm hỏi, chấm than hoặc dòng
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]
    if not sentences:
        sentences = [text.strip()]

    total_sentences = len(sentences)

    if target_scenes and target_scenes > 0:
        desired_count = target_scenes
    else:
        desired_count = max(1, (total_sentences + 1) // 2)

    # Nếu số câu ít hơn số cảnh mong muốn, chia nhỏ câu theo mệnh đề (dấu phẩy, chấm phẩy, liên từ)
    if total_sentences < desired_count:
        expanded_parts: List[str] = []
        for s in sentences:
            clauses = [c.strip() for c in re.split(r"[,;–—]\s+|(?:\s+(?:và|nhưng|sau đó|rồi|khi|đến khi)\s+)", s) if len(c.strip()) > 8]
            if len(clauses) > 1:
                expanded_parts.extend(clauses)
            else:
                expanded_parts.append(s)
        if len(expanded_parts) > total_sentences:
            sentences = expanded_parts
            total_sentences = len(sentences)

    # Chia đều sentences thành desired_count phân đoạn bằng bucket distribution
    count = min(desired_count, total_sentences)
    raw_chunks: List[str] = []
    for i in range(count):
        start_idx = (i * total_sentences) // count
        end_idx = ((i + 1) * total_sentences) // count
        chunk = sentences[start_idx:end_idx]
        if chunk:
            joined = " ".join(chunk).rstrip(".") + "."
            raw_chunks.append(joined)

    scenes: List[SceneResponse] = []
    for i, scene_text in enumerate(raw_chunks, 1):
        dur = max(3.5, round(len(scene_text.split()) / 2.6, 1))
        prompt_en = create_whiteboard_art_prompt(scene_text, scene_index=i, aspect_ratio=aspect_ratio)
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
    1. Hỗ trợ SRT (tách theo timestamp).
    2. Hỗ trợ nhận diện phân cảnh có cấu trúc sẵn (PHÂN CẢNH 1, CẢNH 1, SCENE 1...).
    3. Hỗ trợ LLM Director (Gemini hoặc Ollama Local) chia cảnh chuẩn xác theo target_scenes.
    4. Smart Local Splitter dự phòng đảm bảo luôn tạo đủ số cảnh mong muốn.
    """
    raw = req.text.strip()
    if not raw:
        raise HTTPException(status_code=400, detail="Vui lòng nhập nội dung kịch bản")

    # Mode 1: SRT
    if req.input_mode.upper() == "SRT" or ("-->" in raw and any(line.isdigit() for line in raw.splitlines()[:3])):
        scenes = _parse_srt_to_scenes(raw)
        title = scenes[0].text[:30].strip().replace("\n", " ") + "..." if scenes else "Kịch bản SRT"
        return AnalyzeScriptResponse(title=title, scenes=scenes)

    # Mode 2: Kiểm tra kịch bản có sẵn cấu trúc phân cảnh (PHÂN CẢNH 1, CẢNH 1, SCENE 1...)
    structured_scenes = _parse_structured_scenes(raw, target_scenes=req.target_scenes, aspect_ratio=req.aspect_ratio)
    if len(structured_scenes) >= 2:
        logger.info(f"[analyze_script] Detected {len(structured_scenes)} structured scenes directly from script.")
        title = raw[:30].strip().replace("\n", " ") + "..."
        return AnalyzeScriptResponse(title=title, scenes=structured_scenes)

    # Mode 3: LLM Director (Gemini hoặc local Ollama)
    try:
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

        # Kiểm tra nếu LLM sinh được số cảnh hợp lý (tránh trường hợp trả về 1 cảnh gộp toàn bộ kịch bản dài)
        min_expected = req.target_scenes if (req.target_scenes and req.target_scenes > 1) else 2
        is_sufficient = len(scenes_data) >= min_expected or (len(scenes_data) >= 1 and len(raw.split()) < 30)

        if scenes_data and is_sufficient:
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
            title = raw[:30].strip().replace("\n", " ") + "..."
            return AnalyzeScriptResponse(title=title, scenes=formatted_scenes)
        elif scenes_data:
            logger.warning(
                f"[analyze_script] Director returned only {len(scenes_data)} scenes while target is {req.target_scenes}. "
                "Falling back to smart local splitter."
            )
    except Exception as e:
        logger.warning(f"[analyze_script] Director error: {e}. Using local heuristic splitter.")

    # Fallback: Heuristic sentence splitter (phân chia đều theo target_scenes)
    scenes = _fallback_local_split(raw, target_scenes=req.target_scenes, aspect_ratio=req.aspect_ratio)
    title = raw[:30].strip().replace("\n", " ") + "..."
    return AnalyzeScriptResponse(title=title, scenes=scenes)
