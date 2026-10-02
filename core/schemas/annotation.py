from __future__ import annotations

from typing import List, Literal, Tuple
from pydantic import BaseModel, Field


class CanvasSchema(BaseModel):
    width: int = Field(gt=0, description="Chiều rộng canvas theo pixel nguyên bản")
    height: int = Field(gt=0, description="Chiều cao canvas theo pixel nguyên bản")


class RegionSchema(BaseModel):
    x: int = Field(ge=0, description="Tọa độ x góc trên bên trái")
    y: int = Field(ge=0, description="Tọa độ y góc trên bên trái")
    width: int = Field(gt=0, description="Chiều rộng vùng vẽ")
    height: int = Field(gt=0, description="Chiều cao vùng vẽ")


class RevealSchema(BaseModel):
    direction: Literal[
        "top_to_bottom", "bottom_to_top", "left_to_right", "right_to_left"
    ] = Field(default="top_to_bottom", description="Hướng quét cho proxy xem trước")
    startMs: int = Field(ge=0, description="Thời điểm bắt đầu vẽ (milliseconds)")
    durationMs: int = Field(gt=0, description="Thời lượng vẽ phần tử (milliseconds)")
    maskPaddingPx: int = Field(default=22, ge=0, description="Độ đệm padding viền mask")
    protectedRegions: List[RegionSchema] = Field(
        default_factory=list,
        description="Các vùng bảo vệ không được để lộ nét khi vẽ layer này",
    )


class HandPathSchema(BaseModel):
    start: Tuple[int, int] = Field(description="Tọa độ xuất phát của tay [x, y]")
    end: Tuple[int, int] = Field(description="Tọa độ kết thúc của tay [x, y]")
    easing: str = Field(default="easeInOut", description="Đường cong gia tốc")


class ElementSchema(BaseModel):
    id: str = Field(description="Mã định danh duy nhất của phần tử")
    label: str = Field(description="Tên mô tả đối tượng")
    sequence: int = Field(ge=1, description="Thứ tự xuất hiện theo mạch kịch bản")
    narrativeRole: str = Field(default="", description="Vai trò ngữ diện trong câu chuyện")
    subtitle: str = Field(default="", description="Câu phụ đề tương ứng")
    type: str = Field(default="object", description="Phân loại phần tử (structure, character, text, etc.)")
    region: RegionSchema = Field(description="Vùng giới hạn trên ảnh")
    reveal: RevealSchema = Field(description="Thông số thời gian và che chắn")
    handPath: HandPathSchema = Field(description="Quỹ đạo tay cho preview")


class AnnotationSchema(BaseModel):
    sceneId: str = Field(description="Mã định danh phân cảnh")
    canvas: CanvasSchema = Field(description="Kích thước khung hình chuẩn")
    storyBasis: str = Field(default="", description="Tóm tắt nội dung câu chuyện của cảnh")
    sceneDurationMs: int = Field(gt=0, description="Tổng thời lượng phân cảnh (milliseconds)")
    elements: List[ElementSchema] = Field(
        default_factory=list, description="Danh sách các phần tử theo thứ tự vẽ"
    )
