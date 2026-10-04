from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.schemas.drawing import DrawingStroke
from .path_parser import calculate_polyline_length, parse_and_sample_path, shape_to_path_d


class SVGStrokeExtractor:
    """
    Trích xuất toàn bộ các nét vẽ vector (DrawingStrokes) từ file SVG,
    chuẩn hóa đường đi, tính toán độ dài, tọa độ điểm đầu/cuối và phân loại ngữ nghĩa.
    """

    SEMANTIC_KEYWORDS: Dict[str, List[str]] = {
        # Tree hierarchy
        "trunk": ["trunk", "ground", "mound", "root", "flare", "base", "stem_main"],
        "branches": ["branch", "texture", "segment", "ring", "bark"],
        "leaves": ["leaf", "leaves", "frond", "canopy"],
        "fruits": ["fruit", "coconut", "banana_cluster", "hanging"],
        # Monkey hierarchy
        "body": ["body", "torso", "belly", "tummy", "chest"],
        "head": ["head", "ear", "mask", "skull"],
        "face": ["eye", "snout", "mouth", "nose", "cheek", "face", "smile"],
        "arms": ["arm", "hand", "finger", "reaching", "holding"],
        "legs": ["leg", "foot", "feet", "knee", "toe", "climbing_knee"],
        "tail": ["tail", "curled", "motion_lines"],
        # Banana hierarchy
        "banana_body": ["banana_body", "outer_curve", "inner_curve", "banana", "middle"],
        "stem": ["stem", "stalk", "cap"],
        "tip": ["tip", "facet", "ridge"],
    }

    @classmethod
    def infer_semantic_purpose(cls, element_id: str, parent_id: str, asset_name: str) -> str:
        """Suy luận ý nghĩa ngữ nghĩa (semantic purpose) của nét vẽ từ ID và ngữ cảnh."""
        combined_text = f"{element_id} {parent_id}".lower()
        asset_lower = asset_name.lower()

        # 1. Ưu tiên kiểm tra theo domain của asset
        domain_priority = []
        if "tree" in asset_lower:
            domain_priority = ["trunk", "branches", "leaves", "fruits"]
        elif "monkey" in asset_lower:
            domain_priority = ["body", "head", "face", "arms", "legs", "tail"]
        elif "tiger" in asset_lower:
            domain_priority = ["body", "head", "face", "legs", "tail"]
        elif "rabbit" in asset_lower:
            domain_priority = ["body", "head", "face", "legs", "tail"]
        elif "forest" in asset_lower:
            domain_priority = ["trunk", "branches", "leaves"]
        elif "banana" in asset_lower:
            domain_priority = ["banana_body", "stem", "tip"]

        for purpose in domain_priority:
            keywords = sorted(cls.SEMANTIC_KEYWORDS.get(purpose, []), key=len, reverse=True)
            for kw in keywords:
                if kw in combined_text:
                    return purpose

        # 2. So khớp toàn cục (ưu tiên từ khóa dài hơn trước để tránh collision substring)
        all_items = []
        for purpose, keywords in cls.SEMANTIC_KEYWORDS.items():
            for kw in keywords:
                all_items.append((kw, purpose))
        all_items.sort(key=lambda x: len(x[0]), reverse=True)

        for kw, purpose in all_items:
            if kw in combined_text:
                return purpose

        # 3. Heuristics fallback theo tên asset
        if "tree" in asset_lower or "forest" in asset_lower:
            return "leaves"
        elif "monkey" in asset_lower or "tiger" in asset_lower or "rabbit" in asset_lower or "dog" in asset_lower:
            return "body"
        elif "banana" in asset_lower:
            return "banana_body"

        return "outline"

    @classmethod
    def extract_strokes_from_svg(
        cls,
        svg_content_or_path: str | Path,
        asset_id: str = "asset",
        asset_name: str = "",
    ) -> Tuple[List[DrawingStroke], str]:
        """
        Trích xuất danh sách DrawingStroke từ SVG.
        Trả về (danh sách strokes, viewBox).
        """
        if isinstance(svg_content_or_path, Path) or (
            isinstance(svg_content_or_path, str) and not svg_content_or_path.strip().startswith("<")
        ):
            p = Path(svg_content_or_path)
            content = p.read_text(encoding="utf-8")
        else:
            content = svg_content_or_path

        root = ET.fromstring(content)
        view_box = root.attrib.get("viewBox", "0 0 500 500")

        strokes: List[DrawingStroke] = []
        stroke_counter = 0

        # Hàm đệ quy duyệt qua các node
        def traverse(node: ET.Element, current_group_id: str = ""):
            nonlocal stroke_counter
            node_tag = node.tag.split("}")[-1] if "}" in node.tag else node.tag
            node_id = node.attrib.get("id", "")
            group_id = node_id if node_tag == "g" and node_id else current_group_id

            path_d = ""
            if node_tag == "path":
                path_d = node.attrib.get("d", "")
            elif node_tag in ("rect", "circle", "ellipse", "line", "polyline", "polygon"):
                path_d = shape_to_path_d(node_tag, node.attrib)

            if path_d:
                points = parse_and_sample_path(path_d)
                if len(points) >= 2:
                    stroke_counter += 1
                    stroke_id = node_id or f"stroke_{asset_id}_{stroke_counter}"
                    length = calculate_polyline_length(points)
                    color = node.attrib.get("stroke", "#1A1A1A")
                    width = float(node.attrib.get("stroke-width", 6.0))
                    purpose = cls.infer_semantic_purpose(node_id, group_id, asset_name or asset_id)

                    stroke = DrawingStroke(
                        id=stroke_id,
                        asset_id=asset_id,
                        path=path_d,
                        order=stroke_counter,
                        duration=max(0.1, round(length / 300.0, 2)),
                        start_point=points[0],
                        end_point=points[-1],
                        semantic_purpose=purpose,
                        points=points,
                        length=length,
                        color_hex=color,
                        stroke_width=width,
                    )
                    strokes.append(stroke)

            for child in node:
                traverse(child, group_id)

        traverse(root)
        return strokes, view_box
