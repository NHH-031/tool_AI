from pathlib import Path
import pytest
from PIL import Image

from core.artwork.generator import HighFidelityArtProvider
from core.artwork.prompt_builder import IllustrationPromptBuilder, StructuredIllustrationPrompt
from core.pipeline.semantic_planner import SemanticVisualPlanner
from core.schemas.scene_graph import SceneGraph
from core.validation.semantic import SemanticValidator


def test_boy_giving_flowers_girl_semantic_understanding():
    """
    Kiểm tra AI hiểu chính xác kịch bản chàng trai tặng hoa cho cô gái:
    1. Trích xuất đúng các thực thể: 'man', 'woman', 'flower'.
    2. Nhận diện hành động và mối quan hệ trao tặng 'giving' / 'giving_to'.
    3. Tạo đủ 3 thực thể (người tặng bên trái, hoa ở giữa, người nhận bên phải).
    4. Prompt builder phản ánh đúng ngữ cảnh và hành động tặng hoa.
    """
    script = "một người con trai tặng hoa cho người con gái"

    # 1. Semantic Validator
    entities = SemanticValidator.extract_required_entities(script)
    assert "man" in entities, f"FAIL: Phải trích xuất 'man' cho người con trai: {entities}"
    assert "woman" in entities, f"FAIL: Phải trích xuất 'woman' cho người con gái: {entities}"
    assert "flower" in entities, f"FAIL: Phải trích xuất 'flower' cho hoa: {entities}"

    rels = SemanticValidator.extract_required_relationships(script, entities)
    assert any(r[1] in ["giving", "giving_to"] for r in rels), f"FAIL: Phải có quan hệ giving, nhưng nhận được: {rels}"

    # 2. Dynamic Semantic Planning
    plan = SemanticVisualPlanner.plan_from_script(script)
    assert len(plan.scenes) >= 1
    sg: SceneGraph = plan.scenes[0].scene_graph

    assert len(sg.entities) >= 3, f"FAIL: Cần ít nhất 3 thực thể (man, flower, woman): {[e.id for e in sg.entities]}"
    giver = next((e for e in sg.entities if "man" in e.id or e.label == "man"), None)
    flower = next((e for e in sg.entities if "flower" in e.id or e.label == "flower"), None)
    receiver = next((e for e in sg.entities if "woman" in e.id or e.label == "woman"), None)

    assert giver is not None, "FAIL: Thiếu thực thể người con trai tặng hoa"
    assert flower is not None, "FAIL: Thiếu thực thể bó hoa"
    assert receiver is not None, "FAIL: Thiếu thực thể người con gái nhận hoa"

    # Kiểm tra vị trí không gian: người tặng bên trái, hoa ở giữa, người nhận bên phải
    assert giver.position.x < flower.position.x < receiver.position.x, (
        f"FAIL: Bố cục không đúng: giver x={giver.position.x}, flower x={flower.position.x}, receiver x={receiver.position.x}"
    )

    # Kiểm tra hành động
    assert "giving" in giver.actions
    assert "receiving" in receiver.actions

    # Kiểm tra relationship
    giving_rels = [r for r in sg.relationships if r.relation_type in ["giving_to", "giving"]]
    assert len(giving_rels) >= 1, "FAIL: Phải có quan hệ giving_to giữa chàng trai và cô gái"

    # 3. Prompt Builder Structure
    prompt_obj = IllustrationPromptBuilder.build_from_scene_graph(sg)
    assert prompt_obj.scene_context == script
    assert "man" in prompt_obj.subject.lower()
    assert "woman" in prompt_obj.subject.lower()
    assert "flower" in prompt_obj.subject.lower()


@pytest.mark.asyncio
async def test_high_fidelity_art_provider_giving_flowers(tmp_path):
    """Kiểm tra HighFidelityArtProvider chọn đúng ảnh giving_flowers và KHÔNG rơi vào astronaut."""
    provider = HighFidelityArtProvider()
    prompt = StructuredIllustrationPrompt(
        subject="A young man and a young woman",
        action="man is actively giving flowers to woman",
        relationship="giving flowers to",
        composition="16:9",
        pose="giving",
        line_style="clean line art",
        whiteboard_style="Notion doodle",
        background="#F5EBD7",
        negative_constraints="no text",
        full_prompt="Một người con trai tặng hoa cho người con gái",
        scene_context="một người con trai tặng hoa cho người con gái",
    )
    out_file = tmp_path / "giving_flowers_test.png"
    result = await provider.generate_artwork(prompt, out_file)
    assert result.exists()

    with Image.open(result) as img:
        assert img.size == (1920, 1080)

    # Đảm bảo file được chọn là giving_flowers.png chứ không phải astronaut_mars.png
    curated_dir = Path("assets/artwork/generated")
    astro_bytes = (curated_dir / "astronaut_mars.png").read_bytes()
    result_bytes = result.read_bytes()
    assert result_bytes != astro_bytes, "CRITICAL FAIL: Ảnh sinh ra không được là astronaut_mars.png!"
