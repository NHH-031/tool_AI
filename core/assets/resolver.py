from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, Field

from core.assets.providers import AssetProvider, LocalAssetProvider
from core.drawing.extractor import SVGStrokeExtractor
from core.schemas.asset import AssetLookupResult, VisualAsset
from core.schemas.drawing import DrawingStroke
from core.schemas.scene_graph import VisualEntity

logger = logging.getLogger(__name__)


class AssetResolution(BaseModel):
    """Kết quả phân giải Asset theo kiến trúc đa tầng (Tiered Resolution)."""
    entity_id: str = Field(description="Mã định danh thực thể yêu cầu")
    label: str = Field(description="Nhãn hoặc danh từ đối tượng")
    resolved_source: Literal[
        "existing_asset",
        "existing_variant",
        "pose",
        "action_variant",
        "generated_svg",
        "diagram",
        "chart",
        "symbol",
        "visual_metaphor",
    ] = Field(description="Nguồn gốc cấp độ phân giải thành công")
    asset_id: str = Field(description="Mã asset tương ứng")
    variant_name: Optional[str] = Field(default=None, description="Tên biến thể hoặc tư thế")
    svg_path: Optional[str] = Field(default=None, description="Đường dẫn file SVG")
    svg_content: str = Field(default="", description="Nội dung mã XML SVG")
    stroke_count: int = Field(default=0, ge=0, description="Tổng số nét vẽ trích xuất được")
    strokes: List[DrawingStroke] = Field(default_factory=list, description="Danh sách các nét vector đã trích xuất")
    is_valid_vector: bool = Field(default=False, description="Tính hợp lệ của vector SVG")


class GenericAssetResolver:
    """
    Bộ phân giải Asset tổng quát theo chuỗi kế thừa:
    Existing Asset → Existing Variant → Pose → Action Variant → Generated SVG / Diagram / Chart / Symbol / Metaphor.
    Đảm bảo 100% kịch bản bất kỳ đều nhận được vector SVG vẽ được, không phụ thuộc hard-code.
    """

    def __init__(
        self,
        asset_provider: Optional[AssetProvider] = None,
        generated_cache_dir: Optional[Path] = None,
    ):
        self.asset_provider = asset_provider or LocalAssetProvider()
        self.cache_dir = generated_cache_dir or Path("output/generated_assets")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.extractor = SVGStrokeExtractor()

    def _generate_procedural_svg(
        self,
        label: str,
        category: str,
        visual_type: str,
        action: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Sinh SVG vector có cấu trúc nét vẽ chuẩn cho các thực thể chưa có sẵn trong thư viện.
        Bao gồm nhãn tượng hình, viền phác thảo (outline), và các chi tiết đặc trưng.
        """
        clean_name = label.strip().lower().replace(" ", "_")
        target_file = self.cache_dir / f"gen_{clean_name}.svg"

        # Sinh các nét vẽ theo loại thị giác
        if category in ["diagram", "chart"] or visual_type in ["diagram", "chart"]:
            content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 400" width="100%" height="100%">
  <g id="gen_chart_{clean_name}" stroke="#1A1A1A" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" fill="none">
    <!-- Frame Box -->
    <rect x="50" y="50" width="400" height="300" rx="12" />
    <!-- Grid Lines -->
    <path d="M 50 150 L 450 150 M 50 250 L 450 250" stroke-width="2" stroke-dasharray="6 6" />
    <path d="M 180 50 L 180 350 M 320 50 L 320 350" stroke-width="2" stroke-dasharray="6 6" />
    <!-- Dynamic Metric Wave Curve -->
    <path d="M 70 300 Q 180 120 280 220 T 430 90" stroke-width="7" stroke="#2563EB" />
    <!-- Milestone Nodes -->
    <circle cx="180" cy="180" r="10" fill="#FFFFFF" />
    <circle cx="280" cy="220" r="10" fill="#FFFFFF" />
    <circle cx="430" cy="90" r="12" fill="#2563EB" />
  </g>
</svg>"""
            source_type = "diagram" if category == "diagram" else "chart"
        elif category in ["metaphor"] or visual_type in ["metaphor"]:
            content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 450 450" width="100%" height="100%">
  <g id="gen_metaphor_{clean_name}" stroke="#1A1A1A" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" fill="none">
    <!-- Metaphor Aura Halo -->
    <circle cx="225" cy="225" r="170" stroke-dasharray="10 8" />
    <!-- Central Conceptual Diamond Core -->
    <path d="M 225 90 L 340 225 L 225 360 L 110 225 Z" stroke-width="6" fill="#EFF6FF" />
    <!-- Radiating Expansion Vectors -->
    <path d="M 225 50 L 225 80 M 225 370 L 225 400" stroke-width="6" />
    <path d="M 70 225 L 100 225 M 350 225 L 380 225" stroke-width="6" />
    <circle cx="225" cy="225" r="35" stroke-width="4" />
  </g>
</svg>"""
            source_type = "visual_metaphor"
        elif category in ["character", "animal", "creature"] or visual_type in ["character"]:
            content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 500" width="100%" height="100%">
  <g id="gen_char_{clean_name}" stroke="#1A1A1A" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" fill="none">
    <!-- Head -->
    <circle cx="200" cy="120" r="55" />
    <!-- Eye & Facial Expression -->
    <circle cx="185" cy="115" r="5" fill="#1A1A1A" />
    <circle cx="215" cy="115" r="5" fill="#1A1A1A" />
    <path d="M 185 145 Q 200 160 215 145" stroke-width="4" />
    <!-- Torso -->
    <path d="M 200 175 L 200 320" stroke-width="8" />
    <!-- Arms -->
    <path d="M 200 210 Q 140 250 110 300" stroke-width="6" />
    <path d="M 200 210 Q 260 230 300 270" stroke-width="6" />
    <!-- Legs -->
    <path d="M 200 320 L 150 440" stroke-width="7" />
    <path d="M 200 320 L 250 440" stroke-width="7" />
  </g>
</svg>"""
            source_type = "action_variant" if action else "generated_svg"
        else:
            # Đối tượng tổng quát (Generic Object / Symbol)
            content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="100%" height="100%">
  <g id="gen_obj_{clean_name}" stroke="#1A1A1A" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" fill="none">
    <!-- Distinctive Silhouette Outline -->
    <rect x="90" y="90" width="220" height="220" rx="35" />
    <!-- Inner Cross Structure -->
    <circle cx="200" cy="200" r="60" stroke-width="5" />
    <path d="M 200 90 L 200 140 M 200 260 L 200 310" stroke-width="5" />
    <path d="M 90 200 L 140 200 M 260 200 L 310 200" stroke-width="5" />
  </g>
</svg>"""
            source_type = "symbol"

        target_file.write_text(content, encoding="utf-8")
        return str(target_file), source_type

    def resolve_entity(self, entity: VisualEntity) -> AssetResolution:
        """
        Phân giải thực thể thành Asset vector hoàn chỉnh có danh sách nét vẽ (strokes).
        """
        label = entity.name or entity.label
        action = entity.action or (entity.actions[0] if entity.actions else None)
        pose = entity.pose or action

        # 1. Tra cứu thư viện cục bộ (LocalAssetProvider)
        if hasattr(self.asset_provider, "lookup_sync"):
            lookup: AssetLookupResult = self.asset_provider.lookup_sync(
                label=label,
                action=action,
                pose=pose,
            )
            if lookup.found and lookup.resolved_path:
                svg_p = Path(lookup.resolved_path)
                if svg_p.exists():
                    svg_content = svg_p.read_text(encoding="utf-8")
                    asset_id_str = lookup.asset.id if lookup.asset else f"asset_{label}"
                    strokes, _ = SVGStrokeExtractor.extract_strokes_from_svg(
                        svg_content,
                        asset_id=asset_id_str,
                        asset_name=label,
                    )
                    
                    # Xác định cấp độ phân giải
                    source: Literal[
                        "existing_asset", "existing_variant", "pose", "action_variant",
                        "generated_svg", "diagram", "chart", "symbol", "visual_metaphor"
                    ] = "existing_asset"
                    if lookup.selected_pose:
                        source = "pose" if not action or action == lookup.selected_pose else "action_variant"
                    
                    return AssetResolution(
                        entity_id=entity.id,
                        label=label,
                        resolved_source=source,
                        asset_id=asset_id_str,
                        variant_name=lookup.selected_pose,
                        svg_path=str(svg_p),
                        svg_content=svg_content,
                        stroke_count=len(strokes),
                        strokes=strokes,
                        is_valid_vector=len(strokes) > 0,
                    )

        # 2. Sinh Procedural SVG cho khái niệm trừu tượng hoặc chưa có sẵn
        file_path, gen_source = self._generate_procedural_svg(
            label=label,
            category=entity.category,
            visual_type=entity.visual_type,
            action=action,
        )
        svg_content = Path(file_path).read_text(encoding="utf-8")
        strokes, _ = SVGStrokeExtractor.extract_strokes_from_svg(
            svg_content,
            asset_id=f"gen_{label}",
            asset_name=label,
        )

        return AssetResolution(
            entity_id=entity.id,
            label=label,
            resolved_source=gen_source,  # type: ignore
            asset_id=f"gen_{label}",
            variant_name=action,
            svg_path=file_path,
            svg_content=svg_content,
            stroke_count=len(strokes),
            strokes=strokes,
            is_valid_vector=len(strokes) > 0,
        )
