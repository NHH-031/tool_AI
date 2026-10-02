import json
from pathlib import Path
from core.schemas.annotation import AnnotationSchema


def test_validate_example_annotation():
    ann_path = Path("examples/scene-01-monkey-mountain-banana.annotation.json")
    assert ann_path.exists()
    raw = json.loads(ann_path.read_text(encoding="utf-8"))
    
    parsed = AnnotationSchema.model_validate(raw)
    assert parsed.sceneId == "scene-01"
    assert parsed.canvas.width == 1672
    assert parsed.canvas.height == 941
    assert len(parsed.elements) == 3
    assert parsed.elements[0].label == "左侧场景"
    assert parsed.elements[0].reveal.durationMs == 2600
    assert parsed.elements[0].handPath.start == (290, 130)
