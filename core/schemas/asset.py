from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class AssetPose(BaseModel):
    """Đặc tả tư thế (pose) hoặc biến thể thị giác cụ thể của một thực thể."""
    name: str = Field(description="Tên tư thế (ví dụ: 'standing', 'climbing', 'eating')")
    file_path: str = Field(description="Đường dẫn tương đối hoặc tuyệt đối tới file SVG")
    description: str = Field(default="", description="Mô tả trực quan của tư thế")
    view_box: str = Field(default="0 0 500 500", description="SVG viewBox chuẩn")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Thông số kỹ thuật bổ trợ")


class VisualAsset(BaseModel):
    """Mô hình tài nguyên trực quan hoàn chỉnh cho Whiteboard Asset Library."""
    id: str = Field(description="Mã định danh duy nhất của Asset")
    name: str = Field(description="Tên định danh chuẩn của tài nguyên (ví dụ: 'monkey', 'tree')")
    category: str = Field(
        default="object",
        description="Phân loại ngữ nghĩa (character, structure, object, diagram, metaphor, background)",
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Danh sách từ khóa tra cứu song ngữ (ví dụ: ['monkey', 'khỉ', 'chú khỉ'])",
    )
    format: Literal["svg", "png"] = Field(default="svg", description="Định dạng vector/raster")
    path: str = Field(description="Đường dẫn file SVG mặc định (default pose)")
    poses: Dict[str, AssetPose] = Field(
        default_factory=dict,
        description="Bản đồ các tư thế/hành động hỗ trợ (standing, climbing, eating...)",
    )
    actions: List[str] = Field(
        default_factory=list,
        description="Danh sách các hành vi/động tác tương thích với asset này",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Thông số mỹ thuật, kích thước gốc, tác giả, license",
    )

    def get_pose(self, pose_name: Optional[str]) -> Optional[AssetPose]:
        """Lấy pose theo tên, nếu không chỉ định trả về pose mặc định nếu có."""
        if not pose_name:
            if "default" in self.poses:
                return self.poses["default"]
            if "standing" in self.poses:
                return self.poses["standing"]
            return next(iter(self.poses.values()), None) if self.poses else None
        return self.poses.get(pose_name)

    def has_action(self, action_name: str) -> bool:
        """Kiểm tra asset có hỗ trợ action chỉ định không."""
        return (
            action_name.lower() in [a.lower() for a in self.actions]
            or action_name.lower() in [p.lower() for p in self.poses.keys()]
        )


class AssetLookupQuery(BaseModel):
    """Tham số truy vấn tìm kiếm Asset từ Visual Scene Graph."""
    label: str = Field(description="Nhãn thực thể cần tra cứu (ví dụ: 'monkey', 'cây', 'tree')")
    category: Optional[str] = Field(default=None, description="Lọc theo category nếu có")
    action: Optional[str] = Field(default=None, description="Hành động mong muốn (ví dụ: 'climbing')")
    pose: Optional[str] = Field(default=None, description="Tư thế mong muốn (ví dụ: 'climbing')")
    tags: List[str] = Field(default_factory=list, description="Các thẻ phụ trợ")
    format: str = Field(default="svg", description="Định dạng ưu tiên")


class AssetLookupResult(BaseModel):
    """Kết quả tra cứu Asset từ hệ thống Asset Provider."""
    found: bool = Field(description="Tìm thấy asset phù hợp hay không")
    asset: Optional[VisualAsset] = Field(default=None, description="Thông tin metadata của asset")
    selected_pose: Optional[str] = Field(default=None, description="Tên pose được chọn")
    resolved_path: Optional[str] = Field(default=None, description="Đường dẫn file SVG thực tế đã xác thực")
    svg_content: Optional[str] = Field(default=None, description="Nội dung chuỗi XML SVG nếu được yêu cầu tải")
    error_code: Optional[str] = Field(
        default=None,
        description="Mã lỗi nếu thất bại (ví dụ: 'ASSET_NOT_FOUND', 'INVALID_ASSET')",
    )
    message: str = Field(default="", description="Thông báo chi tiết trạng thái")
