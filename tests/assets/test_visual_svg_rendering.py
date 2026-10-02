from pathlib import Path
import xml.etree.ElementTree as ET
import pytest


def test_visual_svg_monkey_standing():
    """Kiểm tra file SVG thực tế của monkey_standing.svg."""
    path = Path("assets/library/svg/monkey_standing.svg")
    assert path.exists(), "File monkey_standing.svg phải tồn tại"
    tree = ET.parse(path)
    root = tree.getroot()
    assert root.tag.endswith("svg")
    assert "viewBox" in root.attrib
    assert root.attrib["viewBox"] == "0 0 500 500"
    # Kiểm tra có chứa các thẻ path và circle biểu diễn hình vẽ
    paths = list(root.iter("{http://www.w3.org/2000/svg}path")) + list(root.iter("path"))
    assert len(paths) >= 5, "Monkey standing phải có ít nhất 5 paths nét vẽ"


def test_visual_svg_monkey_climbing():
    """Kiểm tra file SVG thực tế của monkey_climbing.svg."""
    path = Path("assets/library/svg/monkey_climbing.svg")
    assert path.exists(), "File monkey_climbing.svg phải tồn tại"
    tree = ET.parse(path)
    root = tree.getroot()
    assert root.tag.endswith("svg")
    assert "viewBox" in root.attrib
    paths = list(root.iter("{http://www.w3.org/2000/svg}path")) + list(root.iter("path"))
    assert len(paths) >= 5, "Monkey climbing phải có nét vẽ chi tiết bám thân cây"


def test_visual_svg_tree():
    """Kiểm tra file SVG thực tế của tree_palm.svg."""
    path = Path("assets/library/svg/tree_palm.svg")
    assert path.exists(), "File tree_palm.svg phải tồn tại"
    tree = ET.parse(path)
    root = tree.getroot()
    assert root.tag.endswith("svg")
    assert root.attrib["viewBox"] == "0 0 600 800"
    paths = list(root.iter("{http://www.w3.org/2000/svg}path")) + list(root.iter("path"))
    assert len(paths) >= 8, "Cây dừa phải có đầy đủ thân cây và các nhánh lá tỏa rộng"


def test_visual_svg_banana():
    """Kiểm tra file SVG thực tế của banana_single.svg và banana_bunch.svg."""
    path_single = Path("assets/library/svg/banana_single.svg")
    assert path_single.exists()
    root_single = ET.parse(path_single).getroot()
    assert root_single.attrib["viewBox"] == "0 0 300 300"

    path_bunch = Path("assets/library/svg/banana_bunch.svg")
    assert path_bunch.exists()
    root_bunch = ET.parse(path_bunch).getroot()
    assert root_bunch.attrib["viewBox"] == "0 0 400 400"


def test_composite_scene_structure():
    """
    Kiểm tra tính nhất quán của phối cảnh kết hợp (Composite Scene):
    Monkey Climbing + Tree + Banana.
    """
    preview_file = Path("assets/library_preview.html")
    assert preview_file.exists(), "File preview.html cho visual test phải tồn tại"
    content = preview_file.read_text(encoding="utf-8")
    assert "stage-tree" in content
    assert "stage-monkey" in content
    assert "stage-banana" in content
    assert "monkey_climbing.svg" in content
    assert "tree_palm.svg" in content
