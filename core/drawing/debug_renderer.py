from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from core.schemas.drawing import DrawingStroke
from .hand_path import HandPathPlanner


class DebugRenderer:
    """
    Trình xuất bản kết quả kiểm định nét vẽ đa chế độ (5 Debug Modes):
    - Mode A: Original SVG
    - Mode B: Stroke order (gán nhãn số thứ tự và phân tầng màu sắc)
    - Mode C: Animated stroke drawing (nét vẽ xuất hiện dần bằng stroke-dashoffset)
    - Mode D: Hand following stroke (bàn tay cầm bút dạ bám sát ngòi bút theo thời gian)
    - Mode E: Final drawing (kết quả tranh hoàn thiện)
    """

    BG_COLOR = "#F6F1E3"
    PEN_COLOR = "#1A1A1A"

    @classmethod
    def render_mode_a(cls, original_svg: str) -> str:
        """Mode A: Nguyên bản file SVG ban đầu."""
        return original_svg

    @classmethod
    def render_mode_b(cls, strokes: List[DrawingStroke], view_box: str = "0 0 500 500") -> str:
        """Mode B: Trực quan hóa thứ tự vẽ tuần tự kèm nhãn số và mã màu theo tiến độ."""
        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}" width="100%" height="100%">',
            f'  <rect width="100%" height="100%" fill="{cls.BG_COLOR}" />',
            '  <!-- Mode B: Stroke Order Visualization -->',
            '  <g id="strokes_layer" stroke-linecap="round" stroke-linejoin="round" fill="none">',
        ]

        # Bảng màu cầu vồng để phân biệt thứ tự vẽ nét
        num_strokes = max(1, len(strokes))
        for stroke in strokes:
            # Màu hue chuyển từ 0 (đỏ) đến 270 (tím)
            hue = int((stroke.order - 1) / num_strokes * 270)
            color = f"hsl({hue}, 85%, 45%)"

            svg_parts.append(
                f'    <path d="{stroke.path}" stroke="{color}" stroke-width="{stroke.stroke_width}" opacity="0.9" />'
            )

        svg_parts.append('  </g>')

        # Lớp nhãn số thứ tự (badges) đặt tại start_point
        svg_parts.append('  <g id="badges_layer" font-family="sans-serif" font-size="12" font-weight="bold">')
        for stroke in strokes:
            sx, sy = stroke.start_point
            hue = int((stroke.order - 1) / num_strokes * 270)
            color = f"hsl({hue}, 85%, 45%)"
            svg_parts.append(
                f'    <g transform="translate({sx}, {sy})">'
                f'      <circle cx="0" cy="0" r="11" fill="{color}" stroke="#FFFFFF" stroke-width="2" />'
                f'      <text x="0" y="4" text-anchor="middle" fill="#FFFFFF">{stroke.order}</text>'
                f'    </g>'
            )
        svg_parts.append('  </g>')
        svg_parts.append('</svg>')
        return "\n".join(svg_parts)

    @classmethod
    def render_mode_c(
        cls,
        strokes: List[DrawingStroke],
        view_box: str = "0 0 500 500",
        total_duration_sec: float = 3.0,
    ) -> str:
        """
        Mode C: Hoạt họa nét vẽ tuần tự bằng kỹ thuật CSS stroke-dashoffset.
        Nét vẽ xuất hiện dần dần theo thời gian, không bao giờ lộ toàn bộ ngay từ đầu.
        """
        planner = HandPathPlanner(strokes)
        total_dur = planner.total_duration_sec or total_duration_sec

        css_lines = [
            "<style>",
            "  @keyframes drawAnim {",
            "    0% { stroke-dashoffset: var(--stroke-len); opacity: 0; }",
            "    1% { opacity: 1; }",
            "    100% { stroke-dashoffset: 0; opacity: 1; }",
            "  }",
            "  .anim-stroke {",
            "    fill: none !important;",
            "    stroke-dasharray: var(--stroke-len);",
            "    stroke-dashoffset: var(--stroke-len);",
            "    animation: drawAnim var(--dur) linear forwards;",
            "    animation-delay: var(--delay);",
            "  }",
            "</style>",
        ]

        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}" width="100%" height="100%">',
            "\n".join(css_lines),
            f'  <rect width="100%" height="100%" fill="{cls.BG_COLOR}" />',
            '  <!-- Mode C: Progressive Animated Strokes -->',
            '  <g stroke-linecap="round" stroke-linejoin="round">',
        ]

        curr_time = 0.0
        for stroke in strokes:
            dur = max(0.05, stroke.duration)
            length = max(1.0, stroke.length)
            svg_parts.append(
                f'    <path d="{stroke.path}" stroke="{stroke.color_hex}" stroke-width="{stroke.stroke_width}" '
                f'class="anim-stroke" style="--stroke-len: {length:.1f}; --dur: {dur:.2f}s; --delay: {curr_time:.2f}s;" />'
            )
            curr_time += dur + planner.travel_duration_sec

        svg_parts.append('  </g>')
        svg_parts.append('</svg>')
        return "\n".join(svg_parts)

    @classmethod
    def render_mode_d(
        cls,
        strokes: List[DrawingStroke],
        view_box: str = "0 0 500 500",
        total_duration_sec: float = 3.0,
    ) -> str:
        """
        Mode D: Bàn tay di chuyển bám sát đầu ngòi bút trong khi nét vẽ xuất hiện.
        """
        planner = HandPathPlanner(strokes)
        total_dur = planner.total_duration_sec or total_duration_sec

        # Tạo chuỗi keyframes chuyển động cho hand
        samples = planner.sample_trajectory(fps=20)
        keyframes = []
        for i, s in enumerate(samples):
            pct = round((i / max(1, len(samples) - 1)) * 100, 2)
            # Ngòi bút nằm ở góc trên bên trái của hand
            keyframes.append(f"    {pct}% {{ transform: translate({s.x}px, {s.y}px); }}")

        css_lines = [
            "<style>",
            "  @keyframes drawAnim {",
            "    0% { stroke-dashoffset: var(--stroke-len); opacity: 0; }",
            "    1% { opacity: 1; }",
            "    100% { stroke-dashoffset: 0; opacity: 1; }",
            "  }",
            f"  @keyframes handMotion {{ \n" + "\n".join(keyframes) + "\n  }",
            "  .anim-stroke {",
            "    fill: none !important;",
            "    stroke-dasharray: var(--stroke-len);",
            "    stroke-dashoffset: var(--stroke-len);",
            "    animation: drawAnim var(--dur) linear forwards;",
            "    animation-delay: var(--delay);",
            "  }",
            "  .drawing-hand {",
            f"    animation: handMotion {total_dur:.2f}s linear forwards;",
            "    pointer-events: none;",
            "  }",
            "</style>",
        ]

        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}" width="100%" height="100%">',
            "\n".join(css_lines),
            f'  <rect width="100%" height="100%" fill="{cls.BG_COLOR}" />',
            '  <!-- Mode D: Strokes with Synchronized Hand -->',
            '  <g stroke-linecap="round" stroke-linejoin="round">',
        ]

        curr_time = 0.0
        for stroke in strokes:
            dur = max(0.05, stroke.duration)
            length = max(1.0, stroke.length)
            svg_parts.append(
                f'    <path d="{stroke.path}" stroke="{stroke.color_hex}" stroke-width="{stroke.stroke_width}" '
                f'class="anim-stroke" style="--stroke-len: {length:.1f}; --dur: {dur:.2f}s; --delay: {curr_time:.2f}s;" />'
            )
            curr_time += dur + planner.travel_duration_sec

        svg_parts.append('  </g>')

        # Lớp biểu diễn ngòi bút / bàn tay vẽ
        first_pt = strokes[0].start_point if strokes else (0, 0)
        svg_parts.append(
            '  <g id="hand_layer" class="drawing-hand">'
            '    <!-- Pen Nib Pointer Indicator -->'
            '    <circle cx="0" cy="0" r="6" fill="#E53E3E" stroke="#FFFFFF" stroke-width="2" />'
            '    <!-- Stylized Drawing Hand Outline -->'
            '    <path d="M 0 0 L 15 35 L 45 45 L 80 140 L 40 160 L 0 50 Z" fill="#D69E2E" opacity="0.75" stroke="#744210" stroke-width="2" />'
            '    <path d="M 0 0 L 10 20 L 5 25 Z" fill="#1A1A1A" />'
            '  </g>'
        )

        svg_parts.append('</svg>')
        return "\n".join(svg_parts)

    @classmethod
    def render_mode_e(cls, strokes: List[DrawingStroke], view_box: str = "0 0 500 500") -> str:
        """Mode E: Kết quả tranh vẽ hoàn chỉnh sau khi tất cả nét đã hoàn tất."""
        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}" width="100%" height="100%">',
            f'  <rect width="100%" height="100%" fill="{cls.BG_COLOR}" />',
            '  <!-- Mode E: Final Completed Drawing -->',
            '  <g stroke-linecap="round" stroke-linejoin="round" fill="none">',
        ]
        for stroke in strokes:
            svg_parts.append(
                f'    <path d="{stroke.path}" stroke="{stroke.color_hex}" stroke-width="{stroke.stroke_width}" />'
            )
        svg_parts.append('  </g>')
        svg_parts.append('</svg>')
        return "\n".join(svg_parts)
