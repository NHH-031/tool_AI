from __future__ import annotations

from ..base import AgentContext, AgentResult, BaseProductionAgent
from core.providers.base import LLMProvider


class VisualPlannerAgent(BaseProductionAgent):
    """Agent phụ trách thiết kế bố cục hình ảnh và phân bổ các phân vùng đối tượng."""

    def __init__(self, llm: LLMProvider):
        super().__init__(name="VisualPlannerAgent")
        self.llm = llm

    async def run(self, context: AgentContext) -> AgentResult:
        return AgentResult(
            success=True,
            data={"status": "initialized", "agent": self.name}
        )
