from __future__ import annotations

from typing import List, Literal
from pydantic import BaseModel, ConfigDict, Field


class DetailBudget(BaseModel):
    """Phân bổ ngân sách chi tiết cho từng thành phần trong phân cảnh."""
    model_config = ConfigDict(populate_by_name=True)

    main_subject: Literal["high", "medium", "low"] = Field(
        default="high",
        description="Chủ thể chính: Ưu tiên đường nét nhận diện, chi tiết giải phẫu/tư thế, biểu cảm"
    )
    secondary_subject: Literal["high", "medium", "low"] = Field(
        default="medium",
        description="Đối tượng tương tác: Đặc điểm hình thái nhận diện rõ ràng"
    )
    background: Literal["low", "minimal", "none"] = Field(
        default="low",
        description="Khung cảnh / mặt đất: Tối giản, chỉ giữ đường chân trời hoặc mô đất cơ bản"
    )
    decorative_elements: Literal["minimal", "none"] = Field(
        default="minimal",
        description="Họa tiết phụ trợ: Rất ít, chỉ thêm khi phục vụ trực tiếp câu chuyện"
    )


class WhiteboardVisualStyleProfile(BaseModel):
    """
    Hồ sơ phong cách thị giác Whiteboard Art chuẩn mực.
    Đảm bảo mọi phân cảnh đều dùng chung một ngôn ngữ tạo hình nhất quán,
    tuân thủ nghiêm ngặt chuẩn mực Notion-style restrained doodle và geeklee/srt-whiteboard-animation.
    """
    model_config = ConfigDict(populate_by_name=True)

    style_name: str = Field(
        default="professional-hand-drawn-whiteboard",
        description="Tên định danh phong cách thị giác"
    )
    background_color: str = Field(
        default="#F5EBD7",
        description="Mã màu nền giấy kem ấm cũ (Warm cream paper: #F5EBD7 / BGR 215, 235, 245)"
    )
    primary_line_color: str = Field(
        default="#1A1A1A",
        description="Mã màu nét phác thảo chủ đạo (Dark charcoal sketch: #1A1A1A)"
    )
    accent_colors: List[str] = Field(
        default_factory=lambda: ["#E05A47", "#E67E22", "#3498DB"],
        description="Danh sách màu nhấn khái niệm được phép (Đỏ: cảnh báo/quả; Cam: năng lượng; Lam: nước/quỹ đạo)"
    )
    line_style: str = Field(
        default="clean sketch",
        description="Đặc tính đường nét: nét phác thảo sạch, có chủ ý, độ dày đồng nhất"
    )
    line_weight: float = Field(
        default=6.0,
        description="Độ dày nét chuẩn trên canvas 1080p (pixels)"
    )
    complexity: Literal["minimal", "medium", "detailed"] = Field(
        default="medium",
        description="Mức độ phức tạp: trung bình (đủ nhận diện, không rối nét)"
    )
    character_style: str = Field(
        default="expressive simplified cartoon",
        description="Phong cách nhân vật: hoạt họa tối giản giàu biểu cảm, silhouette rõ ràng"
    )
    background_complexity: Literal["none", "low", "medium"] = Field(
        default="low",
        description="Độ phức tạp hậu cảnh: thấp, tối đa hóa khoảng trống âm"
    )
    negative_space: Literal["high", "very_high"] = Field(
        default="high",
        description="Mức độ khoảng trống âm (negative space): cao, tạo bố cục thoáng đãng"
    )

    # Ràng buộc cấm kỵ bắt buộc
    text_in_artwork: Literal["forbidden"] = Field(
        default="forbidden",
        description="Tuyệt đối không vẽ chữ, nhãn, ký tự hay typography vào hình vẽ cảnh"
    )
    photorealism: Literal["forbidden"] = Field(
        default="forbidden",
        description="Tuyệt đối không dùng phong cách tả thực hoặc ảnh chụp"
    )
    three_d: Literal["forbidden"] = Field(
        default="forbidden",
        description="Tuyệt đối không dùng tạo hình khối 3D hoặc đổ bóng phức tạp"
    )
    watermark: Literal["forbidden"] = Field(
        default="forbidden",
        description="Tuyệt đối không có watermark hay logo rác trong hình vẽ"
    )

    detail_budget: DetailBudget = Field(
        default_factory=DetailBudget,
        description="Ngân sách chi tiết phân bổ cho các thành phần thị giác"
    )
