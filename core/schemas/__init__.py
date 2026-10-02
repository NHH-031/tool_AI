"""Core domain schemas for Whiteboard Studio."""
from .annotation import (
    AnnotationSchema,
    CanvasSchema,
    ElementSchema,
    HandPathSchema,
    RegionSchema,
    RevealSchema,
)
from .audio import AudioTrack, NarrationSegment
from .drawing import DrawingAction, DrawingStroke
from .project import (
    Asset,
    Project,
    QAResult,
    RenderArtifact,
    Scene,
    VideoTemplate,
)
from .scene_graph import (
    Position,
    SceneGraph,
    VisualEntity,
    VisualRelationship,
)
from .script import ProductionScript, SceneScript, SubtitleCue

__all__ = [
    # Baseline compatibility
    "CanvasSchema",
    "RegionSchema",
    "RevealSchema",
    "HandPathSchema",
    "ElementSchema",
    "AnnotationSchema",
    "SubtitleCue",
    "SceneScript",
    "ProductionScript",
    # Phase 03 additions
    "Position",
    "VisualEntity",
    "VisualRelationship",
    "SceneGraph",
    "DrawingStroke",
    "DrawingAction",
    "NarrationSegment",
    "AudioTrack",
    "Asset",
    "VideoTemplate",
    "Scene",
    "Project",
    "RenderArtifact",
    "QAResult",
]
