from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from core.schemas.annotation import (
    AnnotationSchema,
    CanvasSchema,
    ElementSchema,
    HandPathSchema,
    RegionSchema,
    RevealSchema,
)
from core.schemas.scene_graph import SceneGraph
from core.schemas.timeline import DrawingTimeline


@dataclass
class WhiteboardRenderConfig:
    ink_path: str = "grid"  # "grid" | "skeleton"
    color_fill: str = "contour-wipe"  # "contour-wipe" | "brush"
    fps: int = 60
    cap_long_edge: int = 1080
    bare_tip: bool = False
    custom_hand_path: Optional[Path] = None
    total_ms: Optional[int] = None


class WhiteboardEngineAdapter:
    """
    Adapter đóng gói Media Engine (geeklee/srt-whiteboard-animation).
    Cung cấp giao diện kết nối giữa AI Studio data model và định dạng render của Whiteboard Engine:
    1. Chuẩn bị artifacts: Render composite line-art image và sinh file annotation.json theo đúng SceneGraph & DrawingTimeline.
    2. Gọi renderer: Thực thi scripts/render_stream_whiteboard.py trong tiến trình độc lập hỗ trợ đầy đủ UTF-8.
    3. Ghép kênh âm thanh: Hợp nhất luồng video và thuyết minh TTS thành file MP4 hoàn chỉnh bằng PyAV.
    """

    def __init__(self, root_dir: Optional[Path] = None, python_exe: Optional[Path] = None):
        self.root_dir = root_dir or Path(__file__).resolve().parent.parent.parent
        self.scripts_dir = self.root_dir / "scripts"
        self.assets_dir = self.root_dir / "assets"

        # Xác định python interpreter của virtualenv
        if python_exe:
            self.python_exe = python_exe
        else:
            venv_py = (
                self.root_dir
                / ".venv"
                / ("Scripts" if sys.platform.startswith("win") else "bin")
                / ("python.exe" if sys.platform.startswith("win") else "python")
            )
            self.python_exe = venv_py if venv_py.exists() else Path(sys.executable)

    def prepare_scene_artifacts(
        self,
        scene_graph: SceneGraph,
        timeline: DrawingTimeline,
        output_dir: Path,
    ) -> Tuple[Path, Path]:
        """
        Chuyển đổi SceneGraph và DrawingTimeline của AI Studio thành dữ liệu đầu vào cho Whiteboard Engine:
        1. scene_composition.png: Line-art tổng thể với tất cả nét vẽ trên canvas 1920x1080.
        2. scene_annotation.json: File đặc tả vùng vẽ (regions), thứ tự (sequence), mốc thời gian (reveal),
           và các vùng bảo vệ (protectedRegions) nhằm ngăn ngừa tình trạng lộ nét vẽ sớm (no early reveal).
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        scene_id = scene_graph.scene_id or "scene_default"
        image_path = output_dir / f"{scene_id}.png"
        annotation_path = output_dir / f"{scene_id}.annotation.json"

        # 1. Vẽ composite line-art image lên nền trắng
        canvas = np.full((timeline.canvas_height, timeline.canvas_width, 3), 255, dtype=np.uint8)
        for ev in timeline.events:
            if ev.action == "draw" and ev.points and len(ev.points) >= 2:
                pts = np.array(ev.points, dtype=np.int32).reshape((-1, 1, 2))
                cv2.polylines(
                    canvas,
                    [pts],
                    isClosed=False,
                    color=(26, 26, 26),
                    thickness=4,
                    lineType=cv2.LINE_AA,
                )

        cv2.imwrite(str(image_path), canvas)

        # 2. Xây dựng annotation schema cho các thực thể
        sched = timeline.entities_schedule
        ordered_entities = sorted(
            [e for e in scene_graph.entities if e.id in sched],
            key=lambda e: sched[e.id][0],
        )

        elements = []
        for idx, entity in enumerate(ordered_entities):
            st, et = sched[entity.id]
            pos = entity.position

            # Tính tọa độ bắt đầu và kết thúc của nét vẽ cho entity này
            ent_draw_events = [
                ev for ev in timeline.events if ev.entity_id == entity.id and ev.action == "draw"
            ]
            first_pt = (
                ent_draw_events[0].points[0]
                if ent_draw_events and ent_draw_events[0].points
                else (pos.x, pos.y)
            )
            last_pt = (
                ent_draw_events[-1].points[-1]
                if ent_draw_events and ent_draw_events[-1].points
                else (pos.x + pos.width, pos.y + pos.height)
            )

            # Các vùng bảo vệ: Tất cả các thực thể xuất hiện sau thực thể này (bảo vệ khỏi việc lộ nét trước)
            protected_regions = [
                RegionSchema(
                    x=int(oe.position.x),
                    y=int(oe.position.y),
                    width=int(oe.position.width),
                    height=int(oe.position.height),
                )
                for oe in ordered_entities[idx + 1 :]
            ]

            elements.append(
                ElementSchema(
                    id=entity.id,
                    label=entity.name or entity.label,
                    sequence=idx + 1,
                    narrativeRole="main" if entity.name == "monkey" else "context",
                    subtitle=entity.name or entity.label,
                    type=entity.visual_type
                    or (
                        "character"
                        if entity.name == "monkey"
                        else "structure"
                        if entity.name == "tree"
                        else "object"
                    ),
                    region=RegionSchema(
                        x=int(pos.x),
                        y=int(pos.y),
                        width=int(pos.width),
                        height=int(pos.height),
                    ),
                    reveal=RevealSchema(
                        direction="top_to_bottom",
                        startMs=int(round(st * 1000)),
                        durationMs=int(round((et - st) * 1000)),
                        maskPaddingPx=22,
                        protectedRegions=protected_regions,
                    ),
                    handPath=HandPathSchema(
                        start=(int(first_pt[0]), int(first_pt[1])),
                        end=(int(last_pt[0]), int(last_pt[1])),
                        easing="easeInOut",
                    ),
                )
            )

        ann = AnnotationSchema(
            sceneId=scene_id,
            canvas=CanvasSchema(width=timeline.canvas_width, height=timeline.canvas_height),
            storyBasis=timeline.narration_text,
            sceneDurationMs=int(round(timeline.total_duration * 1000)),
            elements=elements,
        )

        with open(annotation_path, "w", encoding="utf-8") as f:
            json.dump(ann.model_dump(by_alias=True), f, indent=2, ensure_ascii=False)

        return image_path, annotation_path

    def render_scene(
        self,
        image_path: Path,
        annotation_path: Path,
        output_path: Path,
        config: Optional[WhiteboardRenderConfig] = None,
    ) -> Path:
        """Thực thi kết xuất một phân cảnh thành file MP4."""
        cfg = config or WhiteboardRenderConfig()
        hand_path = cfg.custom_hand_path or (self.assets_dir / "drawing-hand.png")

        script_path = self.scripts_dir / "render_stream_whiteboard.py"
        cmd = [
            str(self.python_exe),
            str(script_path),
            str(image_path),
            str(annotation_path),
            str(output_path),
            str(hand_path),
            "--ink-path",
            cfg.ink_path,
            "--color-fill",
            cfg.color_fill,
            "--fps",
            str(cfg.fps),
            "--cap-long-edge",
            str(cfg.cap_long_edge),
        ]
        if cfg.total_ms is not None:
            cmd.extend(["--total-ms", str(cfg.total_ms)])
        if cfg.bare_tip:
            cmd.append("--bare-tip")

        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        if res.returncode != 0:
            raise RuntimeError(f"Whiteboard rendering failed (code {res.returncode}): {res.stderr}")
        return output_path

    def mux_audio_video(self, video_path: Path, audio_path: Path, output_path: Path) -> Path:
        """
        Ghép kênh (multiplex) luồng video và luồng audio thành file MP4 hoàn chỉnh bằng PyAV.
        Tự động mã hóa audio sang chuẩn AAC tương thích tối đa với mọi trình phát.
        """
        import av

        v_in = av.open(str(video_path))
        a_in = av.open(str(audio_path))
        out = av.open(str(output_path), mode="w")

        # Thiết lập luồng video dựa trên template của video đầu vào
        out_v = out.add_stream_from_template(v_in.streams.video[0])

        # Thiết lập luồng audio với codec AAC
        in_a = a_in.streams.audio[0]
        sample_rate = in_a.rate or 24000
        out_layout = "mono" if (getattr(in_a, "channels", 1) == 1 or (in_a.layout and in_a.layout.channels == 1)) else "stereo"

        out_a = out.add_stream("aac", rate=sample_rate)
        out_a.format = "fltp"
        out_a.layout = out_layout
        out_a.codec_context.open()

        resampler = av.AudioResampler(
            format="fltp", layout=out_layout, rate=sample_rate
        )

        # Mux Video packets
        for packet in v_in.demux(v_in.streams.video[0]):
            if packet.dts is not None:
                packet.stream = out_v
                out.mux(packet)

        # Decode audio và encode sang AAC
        for frame in a_in.decode(audio=0):
            for r in resampler.resample(frame):
                for packet in out_a.encode(r):
                    out.mux(packet)

        for packet in out_a.encode():
            out.mux(packet)

        out.close()
        v_in.close()
        a_in.close()
        return output_path

    def merge_scenes(self, input_mp4s: List[Path], output_mp4: Path) -> Path:
        """Ghép nối danh sách các phân cảnh MP4 thành video hoàn chỉnh."""
        script_path = self.scripts_dir / "merge_scenes.py"
        cmd = [
            str(self.python_exe),
            str(script_path),
            "--inputs",
            *[str(p) for p in input_mp4s],
            "--output",
            str(output_mp4),
        ]
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        if res.returncode != 0:
            raise RuntimeError(f"Scene merging failed (code {res.returncode}): {res.stderr}")
        return output_mp4
