from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from pydantic import ValidationError

from ..base import AgentContext, AgentResult, BaseProductionAgent
from core.providers.base import LLMMessage, LLMProvider
from core.providers.gemini import LLMProviderError, LLMStructuredOutputError
from core.schemas.script import ScriptOutput, ScriptSegment

logger = logging.getLogger(__name__)


class ScriptAgent(BaseProductionAgent):
    """
    Agent phụ trách chuyển đổi ý tưởng video thành kịch bản phân cảnh có cấu trúc,
    chia nhỏ thành các phân đoạn lời dẫn (Narration Segments) kèm ước tính thời lượng và ngữ nghĩa.
    """

    SYSTEM_PROMPT = """Bạn là Chuyên gia Biên kịch Video Bảng trắng (Whiteboard Animation Scriptwriter) hàng đầu.
Nhiệm vụ của bạn là chuyển đổi ý tưởng thô của người dùng thành một kịch bản video bảng trắng hấp dẫn, trực quan và cô đọng.

Quy tắc biên kịch:
1. Nguyên tắc "Show Don't Write": Viết câu từ gợi mở hình ảnh chuyển động và hành động tương tác thay vì chỉ giải thích lý thuyết khô khan.
2. Phân đoạn rõ ràng: Chia kịch bản thành từng câu ngắn gọn (segments), mỗi phân đoạn dài từ 3 đến 8 giây.
3. Đo lường thời lượng: Ước lượng chính xác thời gian đọc (khoảng 3.5 - 4 từ mỗi giây đối với tiếng Việt/tiếng Anh).
4. Ngữ nghĩa cốt lõi: Với mỗi phân đoạn, chỉ ra rõ thông điệp chính (semantic_meaning), các thực thể mấu chốt (key_entities) và các hành động (suggested_actions).
5. Đầu ra có cấu trúc: Tuân thủ tuyệt đối Pydantic schema ScriptOutput.
"""

    def __init__(self, llm: LLMProvider, max_retries: int = 2):
        super().__init__(name="ScriptAgent")
        self.llm = llm
        self.max_retries = max_retries

    async def generate_script(
        self,
        idea: str,
        language: str = "vi",
        target_duration_sec: int = 30,
        style: str = "educational",
    ) -> AgentResult:
        """
        Sinh kịch bản có cấu trúc từ ý tưởng với cơ chế thử lại có giới hạn (bounded retry).
        """
        if not idea or not idea.strip():
            return AgentResult(
                success=False,
                error_message="Ý tưởng video (idea) không được để trống.",
                data={"error_type": "empty_idea"},
            )

        user_prompt = (
            f"Ý tưởng video: {idea.strip()}\n"
            f"Ngôn ngữ: {language}\n"
            f"Thời lượng mục tiêu: {target_duration_sec} giây\n"
            f"Phong cách thể hiện: {style}\n\n"
            "Hãy xây dựng kịch bản hoàn chỉnh và chia nhỏ thành các phân đoạn lời dẫn chi tiết."
        )

        messages = [
            LLMMessage(role="system", content=self.SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_prompt),
        ]

        attempt = 0
        last_error = ""

        while attempt <= self.max_retries:
            try:
                script_output: ScriptOutput = await self.llm.generate_structured(
                    messages=messages,
                    response_schema=ScriptOutput,
                    temperature=0.3,
                )

                # Kiểm tra tính hợp lệ cơ bản
                if not script_output.segments:
                    raise ValueError("Kịch bản sinh ra không có phân đoạn lời dẫn nào (empty segments).")

                # Cập nhật thông tin ngôn ngữ và thời lượng nếu cần
                script_output.language = language
                script_output.target_duration_sec = target_duration_sec
                script_output.style = style

                logger.info(
                    f"[ScriptAgent] Sinh kịch bản thành công: '{script_output.title}' với {len(script_output.segments)} segments."
                )

                return AgentResult(
                    success=True,
                    data={
                        "script_output": script_output.model_dump(),
                        "title": script_output.title,
                        "script": script_output.script,
                        "segments_count": len(script_output.segments),
                        "retries": attempt,
                    },
                )

            except (LLMStructuredOutputError, LLMProviderError, ValidationError, ValueError) as err:
                attempt += 1
                last_error = str(err)
                logger.warning(
                    f"[ScriptAgent] Lỗi sinh kịch bản (lần thử {attempt}/{self.max_retries + 1}): {last_error}"
                )

                if attempt <= self.max_retries:
                    # Gửi phản hồi lỗi để mô hình sửa chữa
                    messages.append(
                        LLMMessage(
                            role="user",
                            content=f"Đầu ra trước đó không hợp lệ hoặc cấu trúc JSON bị lỗi: {last_error}. "
                                    f"Vui lòng tạo lại ScriptOutput tuân thủ đúng định dạng và có ít nhất 1 phân đoạn.",
                        )
                    )

        return AgentResult(
            success=False,
            error_message=f"Thất bại khi sinh kịch bản sau {self.max_retries + 1} lần thử: {last_error}",
            data={"error_type": "script_generation_exhausted", "retries": self.max_retries},
        )

    async def run(self, context: AgentContext) -> AgentResult:
        """Thực thi tác vụ trong pipeline chung của hệ thống."""
        idea = context.prompt or context.shared_state.get("idea", "")
        language = context.shared_state.get("language", "vi")
        duration = context.shared_state.get("duration", 30)
        style = context.shared_state.get("style", "educational")

        result = await self.generate_script(
            idea=idea,
            language=language,
            target_duration_sec=duration,
            style=style,
        )

        if result.success and "script_output" in result.data:
            context.shared_state["script_output"] = result.data["script_output"]
            context.shared_state["script"] = result.data["script"]
            context.shared_state["title"] = result.data["title"]

        return result
