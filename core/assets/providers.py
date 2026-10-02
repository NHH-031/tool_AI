from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET

from core.schemas.asset import (
    AssetLookupQuery,
    AssetLookupResult,
    AssetPose,
    VisualAsset,
)

logger = logging.getLogger(__name__)


class AssetProvider(ABC):
    """Giao diện trừu tượng cho hệ thống cung ứng Visual Assets."""

    @abstractmethod
    async def lookup(self, query: AssetLookupQuery) -> AssetLookupResult:
        """Tra cứu asset phù hợp với nhãn, thể loại, hành động và tư thế."""
        pass

    @abstractmethod
    async def get_asset(self, asset_id: str) -> Optional[VisualAsset]:
        """Lấy thông tin metadata của asset theo ID."""
        pass

    @abstractmethod
    async def load_svg(self, asset_id: str, pose: Optional[str] = None) -> Optional[str]:
        """Tải chuỗi nội dung XML SVG của asset theo pose."""
        pass


class LocalAssetProvider(AssetProvider):
    """
    Nhà cung ứng Asset từ thư viện file cục bộ (SVG Library).
    Hỗ trợ nạp manifest.json, tra cứu từ khóa song ngữ, chọn pose/action,
    và kiểm định toàn vẹn cú pháp vector SVG.
    """

    def __init__(self, library_dir: Optional[Path] = None):
        self.library_dir = library_dir or Path("assets/library")
        self.assets_by_id: Dict[str, VisualAsset] = {}
        self.load_library()

    def load_library(self) -> None:
        """Nạp danh mục asset từ manifest.json nếu có."""
        self.assets_by_id.clear()
        manifest_path = self.library_dir / "manifest.json"
        if manifest_path.exists():
            try:
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
                for item in data.get("assets", []):
                    asset = VisualAsset.model_validate(item)
                    self.assets_by_id[asset.id] = asset
                logger.info(f"[LocalAssetProvider] Đã nạp {len(self.assets_by_id)} assets từ {manifest_path}")
            except Exception as e:
                logger.error(f"[LocalAssetProvider] Lỗi khi nạp {manifest_path}: {e}")

    def register_asset(self, asset: VisualAsset) -> None:
        """Đăng ký thêm asset vào bộ nhớ cục bộ."""
        self.assets_by_id[asset.id] = asset

    def _resolve_file_path(self, relative_path: str) -> Path:
        """Chuyển đổi relative path trong manifest thành Path hợp lệ."""
        p = Path(relative_path)
        if p.is_absolute():
            return p
        return self.library_dir / relative_path

    def _validate_svg_content(self, file_path: Path) -> tuple[bool, Optional[str], str]:
        """
        Kiểm tra tính hợp lệ của file SVG:
        - Tồn tại trên đĩa
        - Dung lượng > 0
        - Cú pháp XML chuẩn (parsable bằng ElementTree)
        - Thẻ gốc là <svg>
        """
        if not file_path.exists():
            return False, None, f"File SVG không tồn tại: {file_path}"
        try:
            content = file_path.read_text(encoding="utf-8")
            if not content.strip():
                return False, None, f"File SVG rỗng: {file_path}"
            root = ET.fromstring(content)
            # Tag root phải kết thúc bằng 'svg' (bỏ qua xml namespace nếu có)
            if not root.tag.endswith("svg"):
                return False, None, f"Thẻ gốc không phải là <svg>: {root.tag}"
            return True, content, ""
        except ET.ParseError as err:
            return False, None, f"Lỗi cú pháp XML trong file SVG: {err}"
        except Exception as err:
            return False, None, f"Lỗi đọc file SVG: {err}"

    async def get_asset(self, asset_id: str) -> Optional[VisualAsset]:
        return self.assets_by_id.get(asset_id)

    async def load_svg(self, asset_id: str, pose: Optional[str] = None) -> Optional[str]:
        asset = await self.get_asset(asset_id)
        if not asset:
            return None
        pose_obj = asset.get_pose(pose)
        rel_path = pose_obj.file_path if pose_obj else asset.path
        target_path = self._resolve_file_path(rel_path)
        valid, content, _ = self._validate_svg_content(target_path)
        return content if valid else None

    async def lookup(self, query: AssetLookupQuery) -> AssetLookupResult:
        """
        Tra cứu asset theo nhãn, tag, category, action và chọn pose phù hợp.
        Tuyệt đối không crash khi không tìm thấy, trả về error_code='ASSET_NOT_FOUND'.
        """
        label_lower = query.label.strip().lower()
        if not label_lower:
            return AssetLookupResult(
                found=False,
                error_code="INVALID_QUERY",
                message="Query label không được để trống.",
            )

        matched_asset: Optional[VisualAsset] = None

        # 1. Tìm kiếm chính xác theo ID hoặc Name
        for asset in self.assets_by_id.values():
            if asset.id.lower() == label_lower or asset.name.lower() == label_lower:
                matched_asset = asset
                break

        # 2. Tìm kiếm qua Tags (từ khóa đồng nghĩa Việt/Anh)
        if not matched_asset:
            for asset in self.assets_by_id.values():
                tags_lower = [t.lower() for t in asset.tags]
                if label_lower in tags_lower or any(label_lower in t or t in label_lower for t in tags_lower):
                    matched_asset = asset
                    break

        if not matched_asset:
            logger.info(f"[LocalAssetProvider] Không tìm thấy asset cho query '{query.label}'")
            return AssetLookupResult(
                found=False,
                error_code="ASSET_NOT_FOUND",
                message=f"Không tìm thấy visual asset phù hợp với nhãn '{query.label}'.",
            )

        # 3. Lựa chọn Pose hoặc Action tương ứng
        selected_pose_name = "default"
        pose_obj: Optional[AssetPose] = None

        requested_pose = query.pose or query.action
        if requested_pose:
            req_lower = requested_pose.lower()
            # Kiểm tra xem có pose trùng tên không
            for p_name, p_val in matched_asset.poses.items():
                if p_name.lower() == req_lower:
                    selected_pose_name = p_name
                    pose_obj = p_val
                    break

        # Nếu không có pose trùng, lấy pose mặc định
        if not pose_obj:
            pose_obj = matched_asset.get_pose(None)
            selected_pose_name = pose_obj.name if pose_obj else "default"

        rel_path = pose_obj.file_path if pose_obj else matched_asset.path
        target_path = self._resolve_file_path(rel_path)

        # 4. Kiểm định tính toàn vẹn của SVG
        is_valid, svg_content, err_msg = self._validate_svg_content(target_path)
        if not is_valid:
            logger.warning(f"[LocalAssetProvider] Asset '{matched_asset.id}' không hợp lệ: {err_msg}")
            return AssetLookupResult(
                found=False,
                asset=matched_asset,
                selected_pose=selected_pose_name,
                resolved_path=str(target_path),
                error_code="INVALID_ASSET",
                message=err_msg,
            )

        return AssetLookupResult(
            found=True,
            asset=matched_asset,
            selected_pose=selected_pose_name,
            resolved_path=str(target_path),
            svg_content=svg_content,
            message="Tìm thấy asset thành công.",
        )


class GeneratedAssetProvider(AssetProvider):
    """
    Nhà cung ứng Asset dự phòng / động (Procedural / Generative).
    Tạo SVG vector whiteboard hợp lệ khi asset chưa có sẵn trong thư viện tĩnh.
    """

    def __init__(self, style_preset: str = "whiteboard_lineart"):
        self.style_preset = style_preset
        self.generated_cache: Dict[str, VisualAsset] = {}

    def _generate_procedural_svg(self, label: str, category: str) -> str:
        """Sinh mã SVG vector tối giản có khung vẽ và biểu tượng nét mực đen chuẩn."""
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 500" width="100%" height="100%">
  <g id="gen_{label}" stroke="#1A1A1A" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" fill="none">
    <rect x="40" y="40" width="420" height="420" rx="20" stroke-dasharray="12 8" />
    <circle cx="250" cy="220" r="90" />
    <path d="M 190 200 Q 250 250 310 200" />
    <text x="250" y="380" font-family="sans-serif" font-size="28" font-weight="bold" stroke="none" fill="#1A1A1A" text-anchor="middle">{label.upper()}</text>
  </g>
</svg>"""

    async def lookup(self, query: AssetLookupQuery) -> AssetLookupResult:
        """Sinh asset vector tự động cho các đối tượng mới."""
        label = query.label.strip()
        asset_id = f"gen_asset_{label.lower().replace(' ', '_')}"

        if asset_id not in self.generated_cache:
            svg_text = self._generate_procedural_svg(label, query.category or "object")
            pose = AssetPose(
                name="default",
                file_path=f"generated://{asset_id}.svg",
                description=f"Generated procedural vector for {label}",
                view_box="0 0 500 500",
            )
            asset = VisualAsset(
                id=asset_id,
                name=label,
                category=query.category or "object",
                tags=[label.lower()],
                format="svg",
                path=pose.file_path,
                poses={"default": pose},
                actions=[query.action] if query.action else [],
                metadata={"is_generated": True, "generator": "procedural_svg_v1"},
            )
            self.generated_cache[asset_id] = (asset, svg_text)
        else:
            asset, svg_text = self.generated_cache[asset_id]

        return AssetLookupResult(
            found=True,
            asset=asset,
            selected_pose="default",
            resolved_path=asset.path,
            svg_content=svg_text,
            message="Sinh asset vector tự động thành công.",
        )

    async def get_asset(self, asset_id: str) -> Optional[VisualAsset]:
        if asset_id in self.generated_cache:
            return self.generated_cache[asset_id][0]
        return None

    async def load_svg(self, asset_id: str, pose: Optional[str] = None) -> Optional[str]:
        if asset_id in self.generated_cache:
            return self.generated_cache[asset_id][1]
        return None


class CompositeAssetProvider(AssetProvider):
    """
    Nhà cung cấp chuỗi (Chained Provider):
    Ưu tiên tìm trong LocalAssetProvider trước; nếu ASSET_NOT_FOUND mới chuyển sang GeneratedAssetProvider.
    """

    def __init__(self, local_provider: LocalAssetProvider, fallback_provider: Optional[AssetProvider] = None):
        self.local_provider = local_provider
        self.fallback_provider = fallback_provider

    async def lookup(self, query: AssetLookupQuery) -> AssetLookupResult:
        res = await self.local_provider.lookup(query)
        if res.found:
            return res
        if self.fallback_provider:
            logger.info(f"[CompositeAssetProvider] Fallback sang dynamic generator cho '{query.label}'")
            return await self.fallback_provider.lookup(query)
        return res

    async def get_asset(self, asset_id: str) -> Optional[VisualAsset]:
        res = await self.local_provider.get_asset(asset_id)
        if res:
            return res
        if self.fallback_provider:
            return await self.fallback_provider.get_asset(asset_id)
        return None

    async def load_svg(self, asset_id: str, pose: Optional[str] = None) -> Optional[str]:
        content = await self.local_provider.load_svg(asset_id, pose)
        if content:
            return content
        if self.fallback_provider:
            return await self.fallback_provider.load_svg(asset_id, pose)
        return None
