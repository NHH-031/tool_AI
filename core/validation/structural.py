from __future__ import annotations

from typing import List, Optional, Set
from pydantic import BaseModel, Field

from core.schemas.annotation import CanvasSchema
from core.schemas.project import Asset, Project, Scene
from core.schemas.scene_graph import SceneGraph, VisualEntity, VisualRelationship


class StructuralValidationResult(BaseModel):
    """Kết quả kiểm tra tính hợp lệ về cấu trúc dữ liệu."""
    is_valid: bool = Field(description="Dữ liệu có hợp lệ hay không")
    errors: List[str] = Field(default_factory=list, description="Danh sách các lỗi bắt buộc phải sửa")
    warnings: List[str] = Field(default_factory=list, description="Danh sách cảnh báo khuyến nghị")


class StructuralValidator:
    """Bộ kiểm tra tính toàn vẹn cấu trúc: ID, tọa độ, thời gian, tham chiếu quan hệ và asset."""

    @staticmethod
    def validate_entity_coordinates(entity: VisualEntity, canvas: CanvasSchema) -> List[str]:
        """
        Kiểm tra tọa độ đối tượng có nằm trọn vẹn trong biên giới hạn của Canvas hay không.
        Ví dụ: nếu canvas 1920x1080 thì x + width > 1920 hoặc y + height > 1080 sẽ bị từ chối.
        """
        errors = []
        pos = entity.position

        if pos.x < 0:
            errors.append(f"Entity '{entity.id}' tọa độ x ({pos.x}) bị âm (< 0)")
        if pos.y < 0:
            errors.append(f"Entity '{entity.id}' tọa độ y ({pos.y}) bị âm (< 0)")
        if pos.width <= 0:
            errors.append(f"Entity '{entity.id}' chiều rộng width ({pos.width}) phải > 0")
        if pos.height <= 0:
            errors.append(f"Entity '{entity.id}' chiều cao height ({pos.height}) phải > 0")

        # Kiểm tra vượt biên Canvas
        if pos.x + pos.width > canvas.width:
            errors.append(
                f"Entity '{entity.id}' vượt quá chiều rộng canvas: "
                f"x({pos.x}) + width({pos.width}) = {pos.x + pos.width} > canvas.width({canvas.width})"
            )
        if pos.y + pos.height > canvas.height:
            errors.append(
                f"Entity '{entity.id}' vượt quá chiều cao canvas: "
                f"y({pos.y}) + height({pos.height}) = {pos.y + pos.height} > canvas.height({canvas.height})"
            )

        return errors

    @classmethod
    def validate_scene_graph(cls, scene_graph: SceneGraph, canvas: CanvasSchema) -> List[str]:
        """Kiểm tra toàn bộ Scene Graph: ID trùng, liên kết quan hệ và biên tọa độ."""
        errors: List[str] = []
        entity_ids: Set[str] = set()

        # 1. Kiểm tra Entity IDs và tọa độ
        for entity in scene_graph.entities:
            if entity.id in entity_ids:
                errors.append(f"Trùng lặp Entity ID '{entity.id}' trong cùng một SceneGraph")
            entity_ids.add(entity.id)

            errors.extend(cls.validate_entity_coordinates(entity, canvas))

            if entity.duration_ms <= 0:
                errors.append(f"Entity '{entity.id}' duration_ms ({entity.duration_ms}) phải > 0")

        # 2. Kiểm tra Relationship references
        rel_ids: Set[str] = set()
        for rel in scene_graph.relationships:
            if rel.id in rel_ids:
                errors.append(f"Trùng lặp Relationship ID '{rel.id}'")
            rel_ids.add(rel.id)

            if rel.source_id not in entity_ids:
                errors.append(
                    f"Relationship '{rel.id}' tham chiếu source_id không tồn tại: '{rel.source_id}'"
                )
            if rel.target_id not in entity_ids:
                errors.append(
                    f"Relationship '{rel.id}' tham chiếu target_id không tồn tại: '{rel.target_id}'"
                )
            if rel.source_id == rel.target_id:
                errors.append(
                    f"Relationship '{rel.id}' có source_id và target_id trùng nhau: '{rel.source_id}'"
                )

        return errors

    @classmethod
    def validate_scene(
        cls, scene: Scene, project_assets: Optional[List[Asset]] = None
    ) -> StructuralValidationResult:
        """Kiểm tra tính nhất quán toàn diện của một phân cảnh."""
        errors: List[str] = []
        warnings: List[str] = []

        if scene.duration_ms <= 0:
            errors.append(f"Scene '{scene.id}' duration_ms ({scene.duration_ms}) phải > 0")

        # Kiểm tra scene graph
        errors.extend(cls.validate_scene_graph(scene.scene_graph, scene.canvas))

        # Kiểm tra tham chiếu Asset nếu có danh sách assets của dự án
        if project_assets is not None:
            valid_asset_ids = {a.id for a in project_assets}
            for entity in scene.scene_graph.entities:
                if entity.asset_id and entity.asset_id not in valid_asset_ids:
                    errors.append(
                        f"Entity '{entity.id}' tham chiếu asset_id không tồn tại: '{entity.asset_id}'"
                    )

            for track in scene.audio_tracks:
                if track.asset_id not in valid_asset_ids:
                    errors.append(
                        f"AudioTrack '{track.id}' tham chiếu asset_id không tồn tại: '{track.asset_id}'"
                    )

        # Kiểm tra tính nhất quán của Timeline Events
        event_ids: Set[str] = set()
        for evt in scene.timeline_events:
            if evt.id in event_ids:
                errors.append(f"Trùng lặp TimelineEvent ID '{evt.id}' trong Scene '{scene.id}'")
            event_ids.add(evt.id)

            if evt.start_ms < 0:
                errors.append(f"TimelineEvent '{evt.id}' start_ms ({evt.start_ms}) < 0")
            if evt.end_ms < evt.start_ms:
                errors.append(
                    f"TimelineEvent '{evt.id}' end_ms ({evt.end_ms}) nhỏ hơn start_ms ({evt.start_ms})"
                )
            if evt.end_ms > scene.duration_ms:
                warnings.append(
                    f"TimelineEvent '{evt.id}' kết thúc ở {evt.end_ms}ms vượt quá scene.duration_ms ({scene.duration_ms}ms)"
                )

        # Kiểm tra drawing actions
        for act in scene.drawing_actions:
            if act.duration_ms <= 0:
                errors.append(f"DrawingAction '{act.id}' duration_ms ({act.duration_ms}) phải > 0")
            if act.start_ms + act.duration_ms > scene.duration_ms:
                warnings.append(
                    f"DrawingAction '{act.id}' kết thúc ở {act.start_ms + act.duration_ms}ms vượt quá thời lượng cảnh ({scene.duration_ms}ms)"
                )

        return StructuralValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    @classmethod
    def validate_project(cls, project: Project) -> StructuralValidationResult:
        """Kiểm tra toàn bộ Project gồm nhiều phân cảnh và tài nguyên tập trung."""
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Kiểm tra Asset IDs
        asset_ids: Set[str] = set()
        for asset in project.assets:
            if asset.id in asset_ids:
                errors.append(f"Trùng lặp Asset ID '{asset.id}' trong Project '{project.id}'")
            asset_ids.add(asset.id)

        # 2. Kiểm tra Scene IDs và Sequence
        scene_ids: Set[str] = set()
        indices: List[int] = []
        for scene in project.scenes:
            if scene.id in scene_ids:
                errors.append(f"Trùng lặp Scene ID '{scene.id}' trong Project '{project.id}'")
            scene_ids.add(scene.id)
            indices.append(scene.scene_index)

            # Validate từng scene
            scene_res = cls.validate_scene(scene, project_assets=project.assets)
            errors.extend(scene_res.errors)
            warnings.extend(scene_res.warnings)

        # Kiểm tra thứ tự sequence của scene
        sorted_indices = sorted(indices)
        if sorted_indices and sorted_indices != list(range(1, len(indices) + 1)):
            warnings.append(
                f"Chỉ số scene_index không liên tục từ 1..N: hiện tại là {indices}"
            )

        return StructuralValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
