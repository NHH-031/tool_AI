"""
Core Annotation: Semantic Auto-Segmentation and Multi-Region Layout Planner for Whiteboard Video.
"""

from .auto_segment import auto_segment_image, SceneElementSchema

__all__ = ["auto_segment_image", "SceneElementSchema"]
