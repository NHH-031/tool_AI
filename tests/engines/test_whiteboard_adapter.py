from pathlib import Path
from engines.whiteboard.adapter import WhiteboardEngineAdapter, WhiteboardRenderConfig


def test_whiteboard_adapter_instantiation():
    adapter = WhiteboardEngineAdapter()
    assert adapter.scripts_dir.exists()
    assert (adapter.scripts_dir / "render_stream_whiteboard.py").exists()
    assert (adapter.scripts_dir / "merge_scenes.py").exists()
    assert adapter.python_exe.exists()

    cfg = WhiteboardRenderConfig(ink_path="skeleton", color_fill="brush")
    assert cfg.ink_path == "skeleton"
    assert cfg.color_fill == "brush"
