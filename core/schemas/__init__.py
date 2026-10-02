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
from .script import ProductionScript, SceneScript, ScriptOutput, ScriptSegment, SubtitleCue
from .visual_plan import SceneVisualPlan, VisualPlanOutput
from .asset import AssetLookupQuery, AssetLookupResult, AssetPose, VisualAsset
from .tts import NarrationTiming, SentenceTiming, TTSAudioResult, VoiceConfig, WordTiming

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
    # Phase 04 additions
    "ScriptSegment",
    "ScriptOutput",
    "SceneVisualPlan",
    "VisualPlanOutput",
    # Phase 05 additions
    "VisualAsset",
    "AssetPose",
    "AssetLookupQuery",
    "AssetLookupResult",
    # Phase 07 additions
    "VoiceConfig",
    "WordTiming",
    "SentenceTiming",
    "NarrationTiming",
    "TTSAudioResult",
]
