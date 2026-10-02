from .health import router as health_router
from .jobs import router as jobs_router
from .templates import router as templates_router
from .assets import router as assets_router
from .voices import router as voices_router
from .music import router as music_router
from .projects import router as projects_router

__all__ = [
    "health_router",
    "jobs_router",
    "templates_router",
    "assets_router",
    "voices_router",
    "music_router",
    "projects_router",
]
