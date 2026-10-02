from __future__ import annotations

from ..base import AgentContext, AgentResult, BaseProductionAgent
from core.providers.base import ImageProvider


class AssetAgent(BaseProductionAgent):
    """Agent phụ trách tạo và kiểm định hình ảnh line-art theo đúng visual style guideline."""

    def __init__(self, image_provider: ImageProvider):
        super().__init__(name="AssetAgent")
        self.image_provider = image_provider

    async def run(self, context: AgentContext) -> AgentResult:
        return AgentResult(
            success=True,
            data={"status": "initialized", "agent": self.name}
        )
