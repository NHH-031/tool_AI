"""Core domain schemas for Whiteboard Studio."""
from .annotation import (
    AnnotationSchema,
    CanvasSchema,
    ElementSchema,
    HandPathSchema,
    RegionSchema,
    RevealSchema,
)
from .script import ProductionScript, SceneScript, SubtitleCue

__all__ = [
    "CanvasSchema",
    "RegionSchema",
    "RevealSchema",
    "HandPathSchema",
    "ElementSchema",
    "AnnotationSchema",
    "SubtitleCue",
    "SceneScript",
    "ProductionScript",
]
