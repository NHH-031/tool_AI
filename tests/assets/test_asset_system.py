from pathlib import Path
import pytest

from core.assets.providers import (
    CompositeAssetProvider,
    GeneratedAssetProvider,
    LocalAssetProvider,
)
from core.schemas.asset import (
    AssetLookupQuery,
    AssetPose,
    VisualAsset,
)


@pytest.fixture
def local_provider():
    return LocalAssetProvider(library_dir=Path("assets/library"))


@pytest.mark.asyncio
async def test_asset_lookup_by_name_and_tags(local_provider):
    """Kiểm tra tra cứu asset theo name và từ khóa đồng nghĩa tiếng Việt/tiếng Anh."""
    # 1. Tra cứu theo tên chuẩn tiếng Anh
    res_monkey = await local_provider.lookup(AssetLookupQuery(label="monkey"))
    assert res_monkey.found is True
    assert res_monkey.asset.name == "monkey"
    assert res_monkey.asset.category == "character"

    # 2. Tra cứu theo từ khóa tiếng Việt 'khỉ'
    res_vi = await local_provider.lookup(AssetLookupQuery(label="chú khỉ"))
    assert res_vi.found is True
    assert res_vi.asset.id == "asset_monkey"

    # 3. Tra cứu 'tree' / 'cây'
    res_tree = await local_provider.lookup(AssetLookupQuery(label="cây dừa"))
    assert res_tree.found is True
    assert res_tree.asset.name == "tree"

    # 4. Tra cứu 'banana' / 'chuối'
    res_banana = await local_provider.lookup(AssetLookupQuery(label="quả chuối"))
    assert res_banana.found is True
    assert res_banana.asset.name == "banana"


@pytest.mark.asyncio
async def test_missing_asset_returns_not_found(local_provider):
    """Kiểm tra tra cứu thực thể không tồn tại trả về ASSET_NOT_FOUND, không crash."""
    res = await local_provider.lookup(AssetLookupQuery(label="tau_vu_tru_alien_spaceship"))
    assert res.found is False
    assert res.error_code == "ASSET_NOT_FOUND"
    assert "Không tìm thấy" in res.message


@pytest.mark.asyncio
async def test_invalid_asset_handling(local_provider, tmp_path):
    """Kiểm tra xử lý file SVG bị hỏng hoặc lỗi cú pháp XML, trả về INVALID_ASSET không crash."""
    corrupt_svg = tmp_path / "corrupt.svg"
    corrupt_svg.write_text("<svg><unclosed_tag_syntax", encoding="utf-8")

    bad_asset = VisualAsset(
        id="bad_asset_01",
        name="bad_asset",
        format="svg",
        path=str(corrupt_svg),
        poses={
            "default": AssetPose(
                name="default",
                file_path=str(corrupt_svg),
                view_box="0 0 100 100",
            )
        },
    )
    local_provider.register_asset(bad_asset)

    res = await local_provider.lookup(AssetLookupQuery(label="bad_asset"))
    assert res.found is False
    assert res.error_code == "INVALID_ASSET"
    assert "Lỗi cú pháp XML" in res.message


@pytest.mark.asyncio
async def test_pose_selection(local_provider):
    """Kiểm tra lựa chọn đúng tư thế (pose) theo yêu cầu."""
    # Yêu cầu pose 'climbing'
    res_climb = await local_provider.lookup(
        AssetLookupQuery(label="monkey", pose="climbing")
    )
    assert res_climb.found is True
    assert res_climb.selected_pose == "climbing"
    assert "monkey_climbing.svg" in res_climb.resolved_path

    # Yêu cầu pose 'eating'
    res_eat = await local_provider.lookup(
        AssetLookupQuery(label="monkey", pose="eating")
    )
    assert res_eat.found is True
    assert res_eat.selected_pose == "eating"
    assert "monkey_eating.svg" in res_eat.resolved_path

    # Yêu cầu pose không tồn tại -> fallback sang default / standing
    res_fallback = await local_provider.lookup(
        AssetLookupQuery(label="monkey", pose="flying_on_wings")
    )
    assert res_fallback.found is True
    assert res_fallback.selected_pose == "standing"


@pytest.mark.asyncio
async def test_action_selection(local_provider):
    """Kiểm tra tự động suy diễn pose từ action trong Visual Scene Graph."""
    # Visual Planner yêu cầu action 'climbing'
    res = await local_provider.lookup(
        AssetLookupQuery(label="monkey", action="climbing")
    )
    assert res.found is True
    assert res.selected_pose == "climbing"

    # Action 'eating'
    res_eat = await local_provider.lookup(
        AssetLookupQuery(label="monkey", action="eating")
    )
    assert res_eat.found is True
    assert res_eat.selected_pose == "eating"


@pytest.mark.asyncio
async def test_svg_loading_validity(local_provider):
    """Kiểm tra hàm load_svg tải đúng nội dung XML hợp lệ của các asset cốt lõi."""
    for asset_id in ["asset_monkey", "asset_tree", "asset_banana"]:
        svg_content = await local_provider.load_svg(asset_id)
        assert svg_content is not None
        assert "<svg" in svg_content
        assert "</svg>" in svg_content
        assert "viewBox" in svg_content


@pytest.mark.asyncio
async def test_asset_metadata(local_provider):
    """Kiểm tra metadata của asset được nạp đúng."""
    monkey = await local_provider.get_asset("asset_monkey")
    assert monkey is not None
    assert monkey.name == "monkey"
    assert "standing" in monkey.poses
    assert "climbing" in monkey.poses
    assert "eating" in monkey.poses
    assert monkey.metadata.get("style") == "clean_lineart"


@pytest.mark.asyncio
async def test_composite_asset_provider_fallback(local_provider):
    """Kiểm tra CompositeAssetProvider fallback sang GeneratedAssetProvider khi không có asset tĩnh."""
    gen_provider = GeneratedAssetProvider()
    composite = CompositeAssetProvider(
        local_provider=local_provider, fallback_provider=gen_provider
    )

    # 1. Tìm asset có sẵn -> lấy từ local
    res_local = await composite.lookup(AssetLookupQuery(label="monkey"))
    assert res_local.found is True
    assert "assets/library" in res_local.resolved_path.replace("\\", "/")

    # 2. Tìm asset chưa có (ví dụ: 'kangaroo') -> tự động sinh động
    res_gen = await composite.lookup(AssetLookupQuery(label="kangaroo"))
    assert res_gen.found is True
    assert res_gen.asset.name == "kangaroo"
    assert "<svg" in res_gen.svg_content
