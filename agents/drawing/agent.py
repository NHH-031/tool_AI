from __future__ import annotations

from ..base import AgentContext, AgentResult, BaseProductionAgent
from engines.whiteboard.adapter import WhiteboardEngineAdapter


class DrawingAgent(BaseProductionAgent):
    """Agent điều phối kết xuất nét vẽ Whiteboard thông qua WhiteboardEngineAdapter."""

    def __init__(self, engine_adapter: WhiteboardEngineAdapter):
        super().__init__(name="DrawingAgent")
        self.engine_adapter = engine_adapter

    async def run(self, context: AgentContext) -> AgentResult:
        return AgentResult(
            success=True,
            data={"status": "initialized", "agent": self.name}
        )
