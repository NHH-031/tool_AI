from __future__ import annotations

import datetime
from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..config import settings

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Trạng thái dịch vụ: ok | degraded | unhealthy")
    service: str = Field(default=settings.app_name)
    version: str = Field(default=settings.app_version)
    timestamp: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    environment: str = Field(default=settings.app_env)


@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """Kiểm tra tình trạng sống của API server."""
    return HealthResponse()
