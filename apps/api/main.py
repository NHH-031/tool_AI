from __future__ import annotations

import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Đảm bảo root project nằm trong sys.path để import core, engines, agents
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import time
import uuid
from fastapi import Request
from fastapi.responses import JSONResponse
from apps.api.config import settings
from core.logger import setup_logging, request_id_var
from core.rate_limiter import general_limiter

# Khởi tạo structured logging
setup_logging()

from apps.api.routers import (
    health_router,
    jobs_router,
    templates_router,
    assets_router,
    voices_router,
    music_router,
    projects_router,
    scripts_router,
    storyboard_router,
    export_router,
    archive_router,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Backend API cho AI Whiteboard Video Production Studio",
        debug=settings.debug,
    )

    # Request ID, Logging & Rate Limiting Middleware
    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        req_id = request.headers.get("X-Request-ID", f"req-{uuid.uuid4().hex[:8]}")
        token = request_id_var.set(req_id)

        # Rate Limiting cho API endpoints (bỏ qua static files và health)
        path = request.url.path
        if path.startswith(("/export", "/scripts", "/storyboard", "/jobs", "/assets", "/voices")):
            client_ip = request.client.host if request.client else "127.0.0.1"
            if not general_limiter.is_allowed(client_ip):
                retry_after = general_limiter.get_retry_after(client_ip)
                return JSONResponse(
                    status_code=429,
                    content={"detail": f"Quá giới hạn tần suất yêu cầu. Vui lòng thử lại sau {retry_after} giây."},
                    headers={"Retry-After": str(retry_after)},
                )

        start_time = time.time()
        try:
            response = await call_next(request)
            duration_ms = round((time.time() - start_time) * 1000, 2)
            response.headers["X-Request-ID"] = req_id
            response.headers["X-Response-Time"] = f"{duration_ms}ms"
            return response
        finally:
            request_id_var.reset(token)

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static media directories
    output_dir = PROJECT_ROOT / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/media", StaticFiles(directory=str(output_dir)), name="media")
    app.mount("/output", StaticFiles(directory=str(output_dir)), name="output")

    assets_dir = PROJECT_ROOT / "assets"
    if assets_dir.exists():
        app.mount("/assets-static", StaticFiles(directory=str(assets_dir)), name="assets-static")
        artwork_dir = assets_dir / "artwork"
        if artwork_dir.exists():
            app.mount("/assets/artwork", StaticFiles(directory=str(artwork_dir)), name="assets-artwork")
        library_dir = assets_dir / "library"
        if library_dir.exists():
            app.mount("/assets/library", StaticFiles(directory=str(library_dir)), name="assets-library")

    examples_dir = PROJECT_ROOT / "examples"
    if examples_dir.exists():
        app.mount("/examples", StaticFiles(directory=str(examples_dir)), name="examples-static")

    # Register Routers
    app.include_router(health_router)
    app.include_router(jobs_router)
    app.include_router(templates_router)
    app.include_router(assets_router)
    app.include_router(voices_router)
    app.include_router(music_router)
    app.include_router(projects_router)
    app.include_router(scripts_router)
    app.include_router(storyboard_router)
    app.include_router(export_router)
    app.include_router(archive_router)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.api.main:app", host=settings.host, port=settings.port, reload=True)
