from __future__ import annotations

import json
from pathlib import Path
from core.schemas.project import Project, Scene, VideoTemplate

FIXTURE_PATH = Path(__file__).resolve().parent / "monkey-banana-demo" / "scene.json"


def load_monkey_banana_scene() -> Scene:
    raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    raw.pop("text_required", None)
    return Scene.model_validate(raw)


def load_monkey_banana_project() -> Project:
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
