from __future__ import annotations

from ..base import AgentContext, AgentResult, BaseProductionAgent
from core.providers.base import TTSProvider


class NarrationAgent(BaseProductionAgent):
    """Agent phụ trách tạo giọng lồng tiếng (Voiceover) và đo lường thời lượng audio chính xác."""

    def __init__(self, tts: TTSProvider):
        super().__init__(name="NarrationAgent")
        self.tts = tts

    async def run(self, context: AgentContext) -> AgentResult:
        return AgentResult(
            success=True,
            data={"status": "initialized", "agent": self.name}
        )
