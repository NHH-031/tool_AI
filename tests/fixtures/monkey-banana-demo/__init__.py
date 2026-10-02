from __future__ import annotations

import json
from pathlib import Path
from core.schemas.project import Project, Scene, VideoTemplate


FIXTURE_DIR = Path(__file__).resolve().parent
SCENE_JSON_PATH = FIXTURE_DIR / "scene.json"


def load_monkey_banana_scene() -> Scene:
    """Tải fixture scene mẫu khỉ - cây - chuối."""
    raw = json.loads(SCENE_JSON_PATH.read_text(encoding="utf-8"))
    # Bỏ text_required nếu model Scene không có trường này trực tiếp (nó thuộc VideoTemplate)
    text_required = raw.pop("text_required", False)
    scene = Scene.model_validate(raw)
    return scene


def load_monkey_banana_project() -> Project:
    """Tải fixture project hoàn chỉnh chứa scene và template text_required=False."""
    scene = load_monkey_banana_scene()
    template = VideoTemplate(
        id="monkey_template",
        name="Monkey Banana Demo Template",
        canvas=scene.canvas,
        text_required=False,
    )
    return Project(
        id="project-monkey-banana",
        title="Dự án Chú Khỉ và Quả Chuối",
        description="Demo visual scene graph & semantic validation",
        template=template,
        scenes=[scene],
    )
