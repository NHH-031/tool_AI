from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict
from pydantic import BaseModel, Field


class AgentContext(BaseModel):
    project_id: str
    project_title: str
    prompt: str = ""
    shared_state: Dict[str, Any] = Field(default_factory=dict)


class AgentResult(BaseModel):
    success: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    error_message: str = ""


class BaseProductionAgent(ABC):
    """Lớp cơ sở cho toàn bộ các tác nhân chuyên biệt trong xưởng sản xuất video."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def run(self, context: AgentContext) -> AgentResult:
        """Thực thi nhiệm vụ chuyên trách của agent."""
        pass
