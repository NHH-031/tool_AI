from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class WhiteboardRenderConfig:
    ink_path: str = "grid"  # "grid" | "skeleton"
    color_fill: str = "contour-wipe"  # "contour-wipe" | "brush"
    fps: int = 60
    cap_long_edge: int = 1080
    bare_tip: bool = False
    custom_hand_path: Optional[Path] = None


class WhiteboardEngineAdapter:
    """
    Adapter đóng gói Media Engine hiện tại (scripts/render_stream_whiteboard.py và scripts/merge_scenes.py).
    Cung cấp giao diện gọi kiểu hàm Python có kiểu dữ liệu rõ ràng, chạy qua subprocess cách ly.
    """

    def __init__(self, root_dir: Optional[Path] = None, python_exe: Optional[Path] = None):
        self.root_dir = root_dir or Path(__file__).resolve().parent.parent.parent
        self.scripts_dir = self.root_dir / "scripts"
        self.assets_dir = self.root_dir / "assets"
        
        # Xác định python interpreter của virtualenv
        if python_exe:
            self.python_exe = python_exe
        else:
            venv_py = self.root_dir / ".venv" / ("Scripts" if sys.platform.startswith("win") else "bin") / ("python.exe" if sys.platform.startswith("win") else "python")
            self.python_exe = venv_py if venv_py.exists() else Path(sys.executable)

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
            "--ink-path", cfg.ink_path,
            "--color-fill", cfg.color_fill,
            "--fps", str(cfg.fps),
            "--cap-long-edge", str(cfg.cap_long_edge),
        ]
        if cfg.bare_tip:
            cmd.append("--bare-tip")

        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        res = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if res.returncode != 0:
            raise RuntimeError(f"Whiteboard rendering failed (code {res.returncode}): {res.stderr}")
        return output_path

    def merge_scenes(self, input_mp4s: List[Path], output_mp4: Path) -> Path:
        """Ghép nối danh sách các phân cảnh MP4 thành video hoàn chỉnh."""
        script_path = self.scripts_dir / "merge_scenes.py"
        cmd = [
            str(self.python_exe),
            str(script_path),
            "--inputs", *[str(p) for p in input_mp4s],
            "--output", str(output_mp4),
        ]
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        res = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if res.returncode != 0:
            raise RuntimeError(f"Scene merging failed (code {res.returncode}): {res.stderr}")
        return output_mp4
