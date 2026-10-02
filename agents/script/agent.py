from __future__ import annotations

from ..base import AgentContext, AgentResult, BaseProductionAgent
from core.providers.base import LLMProvider


class ScriptAgent(BaseProductionAgent):
    """Agent phụ trách phân tích ý tưởng người dùng và xây dựng kịch bản phân cảnh (Storyboard Script)."""

    def __init__(self, llm: LLMProvider):
        super().__init__(name="ScriptAgent")
        self.llm = llm

    async def run(self, context: AgentContext) -> AgentResult:
        # Stub logic cho Phase 2 (chưa gọi LLM thật)
        return AgentResult(
            success=True,
            data={"status": "initialized", "agent": self.name}
        )
