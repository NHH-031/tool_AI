from __future__ import annotations

import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Đảm bảo root project nằm trong sys.path để import core, engines, agents
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from apps.api.config import settings
from apps.api.routers import health_router, jobs_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Backend API cho AI Whiteboard Video Production Studio",
        debug=settings.debug,
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register Routers
    app.include_router(health_router)
    app.include_router(jobs_router)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.api.main:app", host=settings.host, port=settings.port, reload=True)
