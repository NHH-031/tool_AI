from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncGenerator
from ..jobs.models import ProductionJob


class ProductionOrchestrator(ABC):
    """Giao diện điều phối quy trình sản xuất video từ kịch bản tới video cuối cùng."""

    @abstractmethod
    async def run_job(self, job: ProductionJob) -> ProductionJob:
        """Thực thi toàn bộ pipeline sản xuất cho một job."""
        pass

    @abstractmethod
    async def stream_job_progress(self, job_id: str) -> AsyncGenerator[ProductionJob, None]:
        """Luồng phát tín hiệu tiến độ của job phục vụ SSE hoặc WebSocket."""
        pass
