from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from pydantic import ValidationError

from ..base import AgentContext, AgentResult, BaseProductionAgent
from core.providers.base import LLMMessage, LLMProvider
from core.providers.gemini import LLMProviderError, LLMStructuredOutputError
from core.schemas.annotation import CanvasSchema
from core.schemas.script import ScriptOutput, ScriptSegment
from core.schemas.visual_plan import SceneVisualPlan, VisualPlanOutput
from core.validation.semantic import SemanticValidator
from core.validation.structural import StructuralValidator

logger = logging.getLogger(__name__)


class VisualPlannerAgent(BaseProductionAgent):
    """
    Agent phụ trách thiết kế bố cục hình ảnh và lập đồ thị cảnh trực quan (Visual Scene Graph).
    Đảm bảo tuyệt đối nguyên tắc 'Show Don't Write', hợp lệ cấu trúc và đúng logic ngữ nghĩa.
    """

    SYSTEM_PROMPT = """Bạn là Giám đốc Nghệ thuật & Kiến trúc sư Thị giác (Visual Art Director) cho video Whiteboard.
Nhiệm vụ của bạn là nhận kịch bản và các phân đoạn thoại, sau đó thiết kế Visual Scene Graph hoàn chỉnh cho từng phân cảnh.

NGUYÊN TẮC CỐT LÕI:
1. "SHOW DON'T WRITE" (Hình ảnh hóa, không viết chữ thuần túy):
   - Mọi thực thể chính (primary entities) PHẢI là hình minh họa trực quan:
     * Nhân vật (character)
     * Đồ vật/công cụ (object)
     * Biểu đồ/sơ đồ (diagram)
     * Hình ảnh ẩn dụ (metaphor)
   - TUYỆT ĐỐI KHÔNG xuất các thực thể chính dạng text (ví dụ: cấm tạo visual_type='text' với nhãn 'CON KHỈ' hay 'CÂY' thay vì vẽ hình).
   - Với các khái niệm trừu tượng (như lạm phát, nhiệt độ, chuyển động), bắt buộc dùng visual metaphor hoặc diagram (ví dụ: mũi tên vận tốc, giỏ hàng ít đồ, nhãn giá tăng cao).

2. TỌA ĐỘ VÀ KÍCH THƯỚC CANVAS:
   - Canvas chuẩn: 1920x1080.
   - Toàn bộ tọa độ (x, y) và kích thước (width, height) phải nằm trọn trong canvas:
     0 <= x, width > 0, x + width <= 1920
     0 <= y, height > 0, y + height <= 1080

3. ĐỒ THỊ CẢNH ĐẦY ĐỦ (SCENE GRAPH):
   - Phải xác định rõ ràng:
     * entities: id, label, category, visual_type, importance, drawing_intent, position, layer, start_ms, duration_ms, actions.
     * relationships: id, source_id, target_id, relation_type, action, description.
     * Các cạnh quan hệ phải kết nối chính xác giữa các entity_id hiện hữu.

4. ĐẦU RA CÓ CẤU TRÚC:
   - Trả về đúng Pydantic schema VisualPlanOutput.
"""

    def __init__(self, llm: LLMProvider, max_retries: int = 2):
        super().__init__(name="VisualPlannerAgent")
        self.llm = llm
        self.max_retries = max_retries

    async def plan_visuals(
        self,
        script: str,
        segments: List[ScriptSegment],
        canvas: Optional[CanvasSchema] = None,
    ) -> AgentResult:
        """
        Lập kế hoạch thị giác từ kịch bản và phân đoạn với kiểm định đa tầng
        (Structural + Semantic + Show Don't Write) và cơ chế tự động sửa lỗi (repair loop).
        """
        if not segments and not script:
            return AgentResult(
                success=False,
                error_message="Kịch bản và danh sách phân đoạn không được rỗng.",
                data={"error_type": "empty_input"},
            )

        canvas_schema = canvas or CanvasSchema(width=1920, height=1080)

        # Xây dựng prompt người dùng mô tả kịch bản
        segments_text = "\n".join([
            f"Segment {s.cue_index}: '{s.text}' (thời lượng: {s.estimated_duration_sec}s, ý nghĩa: {s.semantic_meaning})"
            for s in segments
        ])
        user_prompt = (
            f"Toàn bộ kịch bản:\n{script}\n\n"
            f"Các phân đoạn chi tiết:\n{segments_text}\n\n"
            f"Kích thước Canvas: {canvas_schema.width} x {canvas_schema.height}.\n"
            "Hãy thiết kế Visual Scene Graph và kế hoạch vẽ chi tiết cho các phân cảnh."
        )

        messages = [
            LLMMessage(role="system", content=self.SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_prompt),
        ]

        attempt = 0
        last_errors: List[str] = []

        while attempt <= self.max_retries:
            try:
                # 1. Gọi LLM sinh dữ liệu có cấu trúc
                visual_output: VisualPlanOutput = await self.llm.generate_structured(
                    messages=messages,
                    response_schema=VisualPlanOutput,
                    temperature=0.2,
                )

                if not visual_output.scenes:
                    raise ValueError("Kế hoạch thị giác không chứa scene nào (empty scenes).")

                # 2. Kiểm định từng phân cảnh (Structural + Semantic)
                scene_errors: List[str] = []
                for scene_plan in visual_output.scenes:
                    # Gán canvas cho scene plan nếu chưa có
                    scene_plan.canvas = canvas_schema

                    # 2.1 Kiểm định Cấu trúc & Tọa độ
                    struct_errors = StructuralValidator.validate_scene_graph(
                        scene_plan.scene_graph, canvas_schema
                    )
                    if struct_errors:
                        scene_errors.extend(struct_errors)

                    # 2.2 Kiểm định Ngữ nghĩa & Show Don't Write
                    # Lấy text narration tương ứng
                    narration = scene_plan.narration_text or script
                    sem_res = SemanticValidator.validate_narration_against_graph(
                        narration, scene_plan.scene_graph
                    )
                    if not sem_res.is_valid:
                        scene_errors.extend(sem_res.errors)

                # Nếu không có bất kỳ lỗi nào, trả về thành công ngay
                if not scene_errors:
                    logger.info(
                        f"[VisualPlannerAgent] Lập kế hoạch thị giác thành công sau {attempt} lần sửa đổi "
                        f"cho {len(visual_output.scenes)} cảnh."
                    )
                    return AgentResult(
                        success=True,
                        data={
                            "visual_plan": visual_output.model_dump(),
                            "scenes_count": len(visual_output.scenes),
                            "retries": attempt,
                        },
                    )

                # Nếu có lỗi kiểm định, chuẩn bị thông tin để retry/repair
                attempt += 1
                last_errors = scene_errors
                logger.warning(
                    f"[VisualPlannerAgent] Phát hiện lỗi kế hoạch thị giác (lần thử {attempt}/{self.max_retries + 1}): "
                    f"{'; '.join(scene_errors[:3])}"
                )

                if attempt <= self.max_retries:
                    # Tạo repair prompt với chỉ dẫn chi tiết về lỗi
                    error_feedback = (
                        "Kế hoạch thị giác vừa sinh không vượt qua khâu kiểm định chất lượng:\n"
                        + "\n".join([f"- {err}" for err in scene_errors])
                        + "\n\nHÃY SỬA LẠI: Đảm bảo đầy đủ các thực thể và quan hệ cần thiết, "
                          "tọa độ nằm hoàn toàn trong canvas 1920x1080, "
                          "và tuân thủ triệt để nguyên tắc Show Don't Write (vẽ minh họa, không dùng text làm hình vẽ chính)."
                    )
                    messages.append(LLMMessage(role="user", content=error_feedback))

            except (LLMStructuredOutputError, LLMProviderError, ValidationError, ValueError) as err:
                attempt += 1
                last_errors = [str(err)]
                logger.warning(
                    f"[VisualPlannerAgent] Lỗi cấu trúc/kết nối (lần thử {attempt}/{self.max_retries + 1}): {err}"
                )
                if attempt <= self.max_retries:
                    messages.append(
                        LLMMessage(
                            role="user",
                            content=f"Đầu ra JSON bị lỗi cú pháp hoặc schema không khớp: {err}. "
                                    f"Vui lòng tạo lại đối tượng VisualPlanOutput hợp lệ.",
                        )
                    )

        # Hết số lần retry mà vẫn không hợp lệ -> Trả về lỗi có cấu trúc, không crash hệ thống
        return AgentResult(
            success=False,
            error_message=(
                f"Không thể lập kế hoạch thị giác hợp lệ sau {self.max_retries + 1} lần thử. "
                f"Lỗi cuối: {'; '.join(last_errors[:3])}"
            ),
            data={
                "error_type": "visual_planning_validation_exhausted",
                "validation_errors": last_errors,
                "retries": self.max_retries,
            },
        )

    async def run(self, context: AgentContext) -> AgentResult:
        """Thực thi tác vụ trong pipeline chung."""
        script_output_dict = context.shared_state.get("script_output")
        script = context.shared_state.get("script", "")
        segments: List[ScriptSegment] = []

        if script_output_dict and "segments" in script_output_dict:
            segments = [ScriptSegment.model_validate(s) for s in script_output_dict["segments"]]
        elif script:
            segments = [ScriptSegment(text=script, estimated_duration_sec=10.0, semantic_meaning=script)]

        result = await self.plan_visuals(script=script, segments=segments)
        if result.success and "visual_plan" in result.data:
            context.shared_state["visual_plan"] = result.data["visual_plan"]

        return result
