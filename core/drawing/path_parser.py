from __future__ import annotations

import math
import re
from typing import List, Tuple


def shape_to_path_d(tag: str, attrib: dict) -> str:
    """Chuyển đổi các hình học cơ bản của SVG sang thuộc tính d của path."""
    tag_clean = tag.split("}")[-1] if "}" in tag else tag

    if tag_clean == "rect":
        x = float(attrib.get("x", 0))
        y = float(attrib.get("y", 0))
        w = float(attrib.get("width", 0))
        h = float(attrib.get("height", 0))
        rx = float(attrib.get("rx", 0))
        ry = float(attrib.get("ry", rx))
        if rx > 0 or ry > 0:
            rx = min(rx, w / 2)
            ry = min(ry, h / 2)
            return (
                f"M {x + rx} {y} L {x + w - rx} {y} "
                f"A {rx} {ry} 0 0 1 {x + w} {y + ry} "
                f"L {x + w} {y + h - ry} "
                f"A {rx} {ry} 0 0 1 {x + w - rx} {y + h} "
                f"L {x + rx} {y + h} "
                f"A {rx} {ry} 0 0 1 {x} {y + h - ry} "
                f"L {x} {y + ry} "
                f"A {rx} {ry} 0 0 1 {x + rx} {y} Z"
            )
        return f"M {x} {y} L {x + w} {y} L {x + w} {y + h} L {x} {y + h} Z"

    elif tag_clean == "circle":
        cx = float(attrib.get("cx", 0))
        cy = float(attrib.get("cy", 0))
        r = float(attrib.get("r", 0))
        k = r * 0.5522847498
        return (
            f"M {cx} {cy - r} "
            f"C {cx + k} {cy - r}, {cx + r} {cy - k}, {cx + r} {cy} "
            f"C {cx + r} {cy + k}, {cx + k} {cy + r}, {cx} {cy + r} "
            f"C {cx - k} {cy + r}, {cx - r} {cy + k}, {cx - r} {cy} "
            f"C {cx - r} {cy - k}, {cx - k} {cy - r}, {cx} {cy - r} Z"
        )

    elif tag_clean == "ellipse":
        cx = float(attrib.get("cx", 0))
        cy = float(attrib.get("cy", 0))
        rx = float(attrib.get("rx", 0))
        ry = float(attrib.get("ry", 0))
        kx = rx * 0.5522847498
        ky = ry * 0.5522847498
        return (
            f"M {cx} {cy - ry} "
            f"C {cx + kx} {cy - ry}, {cx + rx} {cy - ky}, {cx + rx} {cy} "
            f"C {cx + rx} {cy + ky}, {cx + kx} {cy + ry}, {cx} {cy + ry} "
            f"C {cx - kx} {cy + ry}, {cx - rx} {cy + ky}, {cx - rx} {cy} "
            f"C {cx - rx} {cy - ky}, {cx - kx} {cy - ry}, {cx} {cy - ry} Z"
        )

    elif tag_clean == "line":
        x1 = float(attrib.get("x1", 0))
        y1 = float(attrib.get("y1", 0))
        x2 = float(attrib.get("x2", 0))
        y2 = float(attrib.get("y2", 0))
        return f"M {x1} {y1} L {x2} {y2}"

    elif tag_clean in ("polyline", "polygon"):
        pts_str = attrib.get("points", "").strip()
        coords = [float(c) for c in re.split(r"[,\s]+", pts_str) if c]
        if not coords or len(coords) < 2:
            return ""
        d_parts = [f"M {coords[0]} {coords[1]}"]
        for i in range(2, len(coords), 2):
            if i + 1 < len(coords):
                d_parts.append(f"L {coords[i]} {coords[i+1]}")
        if tag_clean == "polygon":
            d_parts.append("Z")
        return " ".join(d_parts)

    return ""


def tokenize_path(d: str) -> List[str]:
    """Phân tách chuỗi path thành danh sách lệnh và số."""
    pattern = r"([MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?)"
    return re.findall(pattern, d)


def sample_cubic_bezier(
    p0: Tuple[float, float],
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    p3: Tuple[float, float],
    num_samples: int = 15,
) -> List[Tuple[float, float]]:
    """Lấy mẫu các điểm trên đường cong Bezier bậc 3."""
    pts = []
    for i in range(num_samples + 1):
        t = i / num_samples
        u = 1 - t
        x = u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1]
        pts.append((round(x, 2), round(y, 2)))
    return pts


def sample_quadratic_bezier(
    p0: Tuple[float, float],
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    num_samples: int = 12,
) -> List[Tuple[float, float]]:
    """Lấy mẫu các điểm trên đường cong Bezier bậc 2."""
    pts = []
    for i in range(num_samples + 1):
        t = i / num_samples
        u = 1 - t
        x = u**2 * p0[0] + 2 * u * t * p1[0] + t**2 * p2[0]
        y = u**2 * p0[1] + 2 * u * t * p1[1] + t**2 * p2[1]
        pts.append((round(x, 2), round(y, 2)))
    return pts


def sample_arc(
    x1: float,
    y1: float,
    rx: float,
    ry: float,
    phi_deg: float,
    large_arc: int,
    sweep: int,
    x2: float,
    y2: float,
    sample_step: float = 8.0,
) -> List[Tuple[float, float]]:
    """
    Lấy mẫu đường cong Elip SVG (A / a) theo chuẩn W3C SVG Specification (Annex F.6).
    Chuyển đổi từ biểu diễn điểm mút (endpoint parameterization) sang biểu diễn tâm (center parameterization).
    """
    if x1 == x2 and y1 == y2:
        return [(round(x1, 2), round(y1, 2))]
    rx = abs(rx)
    ry = abs(ry)
    if rx == 0 or ry == 0:
        dist = math.hypot(x2 - x1, y2 - y1)
        num_steps = max(2, int(dist / sample_step))
        return [
            (round(x1 + s / num_steps * (x2 - x1), 2), round(y1 + s / num_steps * (y2 - y1), 2))
            for s in range(num_steps + 1)
        ]

    phi = math.radians(phi_deg % 360.0)
    cos_phi = math.cos(phi)
    sin_phi = math.sin(phi)

    # Bước 1: Tính (x1', y1')
    dx = (x1 - x2) / 2.0
    dy = (y1 - y2) / 2.0
    x1_prime = cos_phi * dx + sin_phi * dy
    y1_prime = -sin_phi * dx + cos_phi * dy

    # Điều chỉnh bán kính rx, ry nếu khoảng cách giữa 2 điểm lớn hơn bán kính
    lambda_rad = (x1_prime**2) / (rx**2) + (y1_prime**2) / (ry**2)
    if lambda_rad > 1.0:
        scale = math.sqrt(lambda_rad)
        rx *= scale
        ry *= scale

    # Bước 2: Tính (cx', cy')
    denom = (rx**2) * (y1_prime**2) + (ry**2) * (x1_prime**2)
    num = (rx**2) * (ry**2) - denom
    radicand = max(0.0, num / denom) if denom > 0 else 0.0
    factor = math.sqrt(radicand)
    if large_arc == sweep:
        factor = -factor
    cx_prime = factor * ((rx * y1_prime) / ry)
    cy_prime = factor * (-(ry * x1_prime) / rx)

    # Bước 3: Tính tâm (cx, cy)
    cx = cos_phi * cx_prime - sin_phi * cy_prime + (x1 + x2) / 2.0
    cy = sin_phi * cx_prime + cos_phi * cy_prime + (y1 + y2) / 2.0

    # Bước 4: Tính góc bắt đầu theta1 và delta_theta
    def vector_angle(ux: float, uy: float, vx: float, vy: float) -> float:
        dot = ux * vx + uy * vy
        len_u = math.hypot(ux, uy)
        len_v = math.hypot(vx, vy)
        if len_u == 0 or len_v == 0:
            return 0.0
        val = max(-1.0, min(1.0, dot / (len_u * len_v)))
        ang = math.acos(val)
        if (ux * vy - uy * vx) < 0:
            ang = -ang
        return ang

    v1x = (x1_prime - cx_prime) / rx
    v1y = (y1_prime - cy_prime) / ry
    v2x = (-x1_prime - cx_prime) / rx
    v2y = (-y1_prime - cy_prime) / ry

    theta1 = vector_angle(1.0, 0.0, v1x, v1y)
    d_theta = vector_angle(v1x, v1y, v2x, v2y)

    if sweep == 0 and d_theta > 0:
        d_theta -= 2.0 * math.pi
    elif sweep == 1 and d_theta < 0:
        d_theta += 2.0 * math.pi

    # Lấy mẫu dọc theo cung tròn
    approx_r = (rx + ry) / 2.0
    arc_len = abs(d_theta) * approx_r
    num_steps = max(2, int(arc_len / sample_step))

    pts: List[Tuple[float, float]] = []
    for s in range(num_steps + 1):
        th = theta1 + (s / num_steps) * d_theta
        ex = rx * math.cos(th)
        ey = ry * math.sin(th)
        px = cos_phi * ex - sin_phi * ey + cx
        py = sin_phi * ex + cos_phi * ey + cy
        pts.append((round(px, 2), round(py, 2)))
    return pts


def parse_and_sample_path(d: str, sample_step: float = 8.0) -> List[Tuple[float, float]]:
    """
    Phân tích chuỗi path SVG d và lấy mẫu danh sách tọa độ (x, y) liên tục.
    Tính toán độ dài và thứ tự đi của nét bút.
    """
    tokens = tokenize_path(d)
    if not tokens:
        return []

    points: List[Tuple[float, float]] = []
    cur_x, cur_y = 0.0, 0.0
    start_x, start_y = 0.0, 0.0
    idx = 0
    cmd = ""

    while idx < len(tokens):
        tok = tokens[idx]
        if tok.isalpha():
            cmd = tok
            idx += 1
        # Nếu tiếp tục là tham số của lệnh trước đó

        if cmd in ("M", "m"):
            x = float(tokens[idx])
            y = float(tokens[idx + 1])
            idx += 2
            if cmd == "m":
                x += cur_x
                y += cur_y
            cur_x, cur_y = x, y
            start_x, start_y = cur_x, cur_y
            points.append((cur_x, cur_y))
            cmd = "L" if cmd == "M" else "l"

        elif cmd in ("L", "l"):
            x = float(tokens[idx])
            y = float(tokens[idx + 1])
            idx += 2
            if cmd == "l":
                x += cur_x
                y += cur_y
            # Lấy mẫu đoạn thẳng
            dist = math.hypot(x - cur_x, y - cur_y)
            num_steps = max(2, int(dist / sample_step))
            for s in range(1, num_steps + 1):
                t = s / num_steps
                points.append((round(cur_x + t * (x - cur_x), 2), round(cur_y + t * (y - cur_y), 2)))
            cur_x, cur_y = x, y

        elif cmd in ("H", "h"):
            x = float(tokens[idx])
            idx += 1
            if cmd == "h":
                x += cur_x
            dist = abs(x - cur_x)
            num_steps = max(2, int(dist / sample_step))
            for s in range(1, num_steps + 1):
                t = s / num_steps
                points.append((round(cur_x + t * (x - cur_x), 2), cur_y))
            cur_x = x

        elif cmd in ("V", "v"):
            y = float(tokens[idx])
            idx += 1
            if cmd == "v":
                y += cur_y
            dist = abs(y - cur_y)
            num_steps = max(2, int(dist / sample_step))
            for s in range(1, num_steps + 1):
                t = s / num_steps
                points.append((cur_x, round(cur_y + t * (y - cur_y), 2)))
            cur_y = y

        elif cmd in ("C", "c"):
            x1 = float(tokens[idx])
            y1 = float(tokens[idx + 1])
            x2 = float(tokens[idx + 2])
            y2 = float(tokens[idx + 3])
            x = float(tokens[idx + 4])
            y = float(tokens[idx + 5])
            idx += 6
            if cmd == "c":
                x1 += cur_x
                y1 += cur_y
                x2 += cur_x
                y2 += cur_y
                x += cur_x
                y += cur_y
            sample_pts = sample_cubic_bezier((cur_x, cur_y), (x1, y1), (x2, y2), (x, y))
            points.extend(sample_pts[1:])
            cur_x, cur_y = x, y

        elif cmd in ("Q", "q"):
            x1 = float(tokens[idx])
            y1 = float(tokens[idx + 1])
            x = float(tokens[idx + 2])
            y = float(tokens[idx + 3])
            idx += 4
            if cmd == "q":
                x1 += cur_x
                y1 += cur_y
                x += cur_x
                y += cur_y
            sample_pts = sample_quadratic_bezier((cur_x, cur_y), (x1, y1), (x, y))
            points.extend(sample_pts[1:])
            cur_x, cur_y = x, y

        elif cmd in ("A", "a"):
            rx = float(tokens[idx])
            ry = float(tokens[idx + 1])
            rot = float(tokens[idx + 2])
            large_arc = int(float(tokens[idx + 3]))
            sweep = int(float(tokens[idx + 4]))
            x = float(tokens[idx + 5])
            y = float(tokens[idx + 6])
            idx += 7
            if cmd == "a":
                x += cur_x
                y += cur_y
            sample_pts = sample_arc(cur_x, cur_y, rx, ry, rot, large_arc, sweep, x, y, sample_step)
            if sample_pts:
                points.extend(sample_pts[1:])
            cur_x, cur_y = x, y

        elif cmd in ("Z", "z"):
            if cur_x != start_x or cur_y != start_y:
                points.append((start_x, start_y))
                cur_x, cur_y = start_x, start_y
            # lệnh Z không cần thêm tham số
            if idx < len(tokens) and tokens[idx].isalpha():
                pass
            else:
                idx += 1

        else:
            # Lệnh khác hoặc A/S/T đơn giản hóa: bỏ qua số tiếp theo để tránh lặp vô hạn
            idx += 1

    return points


def calculate_polyline_length(points: List[Tuple[float, float]]) -> float:
    """Tính toán chiều dài hình học liên tục của nét vẽ."""
    if len(points) < 2:
        return 0.0
    total = 0.0
    for i in range(len(points) - 1):
        total += math.hypot(points[i + 1][0] - points[i][0], points[i + 1][1] - points[i][1])
    return round(total, 2)
