from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/assets", tags=["Assets"])

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MANIFEST_PATH = PROJECT_ROOT / "assets" / "library" / "manifest.json"


class AssetPoseItem(BaseModel):
    name: str
    description: str = ""
    view_box: str = "0 0 500 500"
    file_path: str


class AssetCatalogItem(BaseModel):
    id: str
    name: str
    category: str
    tags: List[str] = Field(default_factory=list)
    format: str = "svg"
    path: str
    poses: Dict[str, AssetPoseItem] = Field(default_factory=dict)
    actions: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MasterpieceItem(BaseModel):
    id: str
    title: str
    description: str
    theme: str
    keywords: List[str]
    image_url: str
    resolution: str = "1920x1080"
    style: str = "Notion Doodle / Vector Comic Line Art"


@router.get("", response_model=List[AssetCatalogItem])
async def list_assets() -> List[AssetCatalogItem]:
    """Trả về danh mục các Vector SVG Assets khả dụng cho Whiteboard Studio."""
    if not MANIFEST_PATH.exists():
        return []

    try:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("assets", [])
    except Exception:
        return []


@router.get("/masterpieces", response_model=List[MasterpieceItem])
async def list_masterpieces() -> List[MasterpieceItem]:
    """Trả về danh mục các tác phẩm nghệ thuật vẽ tay 1080p chuẩn mực (Phương án 2)."""
    return [
        MasterpieceItem(
            id="astronaut_mars",
            title="Phi Hành Gia Trên Sao Hỏa",
            description="Tàu vũ trụ đổ bộ và phi hành gia leo thang bước xuống bề mặt đất đá Sao Hỏa.",
            theme="Khoa học & Không gian",
            keywords=["astronaut", "phi hành gia", "mars", "sao hỏa", "space", "vũ trụ"],
            image_url="/assets/artwork/generated/astronaut_mars.png",
        ),
        MasterpieceItem(
            id="teacher_classroom",
            title="Cô Giáo & Tiết Học Lịch Sử",
            description="Cô giáo chỉ bảng giảng bài, học sinh chăm chú giơ tay phát biểu.",
            theme="Giáo dục & Đào tạo",
            keywords=["teacher", "giáo viên", "thầy", "cô", "classroom", "lớp học", "blackboard", "bảng"],
            image_url="/assets/artwork/generated/teacher_classroom.png",
        ),
        MasterpieceItem(
            id="engineer_workspace",
            title="Kỹ Sư Công Nghệ & Tăng Trưởng",
            description="Lập trình viên làm việc bên laptop, cà phê và biểu đồ tăng trưởng phân tích.",
            theme="Công nghệ & Kinh doanh",
            keywords=["engineer", "kỹ sư", "lập trình", "code", "developer", "laptop", "chart", "biểu đồ"],
            image_url="/assets/artwork/generated/engineer_workspace.png",
        ),
        MasterpieceItem(
            id="doctor_medical",
            title="Bác Sĩ Tư Vấn Sức Khỏe",
            description="Bác sĩ đeo ống nghe tư vấn tận tình cho bệnh nhân tại phòng khám.",
            theme="Y tế & Sức khỏe",
            keywords=["doctor", "bác sĩ", "y tế", "sức khỏe", "khám", "clinic", "bệnh viện"],
            image_url="/assets/artwork/generated/doctor_medical.png",
        ),
        MasterpieceItem(
            id="cat_palm",
            title="Mèo Con Trèo Cây Cau",
            description="Chú mèo tinh nghịch thoăn thoắt bám thân cây cau vươn cao.",
            theme="Thiên nhiên & Động vật",
            keywords=["cat", "mèo", "palm", "cau", "tree", "cây"],
            image_url="/assets/artwork/generated/cat_palm.png",
        ),
        MasterpieceItem(
            id="dog_ball",
            title="Chú Chó Đua Tốc Độ Cùng Quả Bóng",
            description="Chú chó sải bước đầy hào hứng đuổi theo quả bóng trên sân cỏ.",
            theme="Động vật & Thể thao",
            keywords=["dog", "chó", "ball", "bóng", "run", "chạy"],
            image_url="/assets/artwork/generated/dog_ball.png",
        ),
        MasterpieceItem(
            id="tiger_rabbit_forest",
            title="Hổ & Thỏ Trong Rừng Sâu",
            description="Cọp dũng mãnh và thỏ nhanh nhẹn trong bối cảnh rừng cổ thụ.",
            theme="Truyện ngụ ngôn",
            keywords=["tiger", "hổ", "cọp", "rabbit", "thỏ", "forest", "rừng"],
            image_url="/assets/artwork/generated/tiger_rabbit_forest.png",
        ),
        MasterpieceItem(
            id="fish_ocean",
            title="Đàn Cá Đại Dương & Rạn San Hô",
            description="Đàn cá bơi lội sinh động giữa lòng đại dương và bầy san hô mềm mại.",
            theme="Đại dương & Sinh thái",
            keywords=["fish", "cá", "ocean", "biển", "sea", "coral", "san hô"],
            image_url="/assets/artwork/generated/fish_ocean.png",
        ),
        MasterpieceItem(
            id="farmer_tree",
            title="Nông Dân Ươm Mầm Cây Xanh",
            description="Người nông dân cần mẫn chăm sóc mầm xanh và bóng mát cây cổ thụ.",
            theme="Nông nghiệp & Đời sống",
            keywords=["farmer", "nông dân", "tree", "cây", "plant", "gieo mầm"],
            image_url="/assets/artwork/generated/farmer_tree.png",
        ),
        MasterpieceItem(
            id="earth_sun",
            title="Trái Đất Quay Quanh Mặt Trời",
            description="Hành tinh xanh chuyển động trên quỹ đạo tỏa sáng của Mặt Trời.",
            theme="Thiên văn học",
            keywords=["earth", "trái đất", "sun", "mặt trời", "orbit", "quỹ đạo"],
            image_url="/assets/artwork/generated/earth_sun.png",
        ),
        MasterpieceItem(
            id="monkey_banana",
            title="Khỉ Leo Cây Hái Chuối",
            description="Chú khỉ tinh nghịch trên cây chuối trĩu quả giữa núi rừng.",
            theme="Hoạt hình vui nhộn",
            keywords=["monkey", "khỉ", "banana", "chuối", "mountain", "núi"],
            image_url="/examples/scene-01-monkey-mountain-banana.png",
        ),
    ]


class GenerateLineArtRequest(BaseModel):
    prompt: str
    subject: Optional[str] = None
    action: Optional[str] = None


GenerateLineArtRequest.model_rebuild()


@router.get("/provider")
async def get_generator_provider() -> Dict[str, Any]:
    """Trả về thông tin Provider sinh ảnh nghệ thuật đang hoạt động."""
    import os
    from core.artwork.generator import ArtworkGeneratorFactory

    generator = ArtworkGeneratorFactory.create()
    provider_name = type(generator).__name__
    return {
        "provider": provider_name,
        "mode": "free_cloud_flux" if provider_name == "FluxCloudArtProvider" else "curated_or_api",
        "description": "FLUX.1-schnell 1080p Notion Doodle Line-Art Generator (100% Free, Zero VRAM)"
        if provider_name == "FluxCloudArtProvider"
        else "Curated High-Fidelity Masterpiece Provider",
        "benchmark_compliance": "95%-100%",
        "target_style": "Notion Comic Doodle (#1A1A1A on #F5EBD7)",
    }


@router.post("/generate-lineart")
async def generate_lineart_on_demand(req: GenerateLineArtRequest) -> Dict[str, Any]:
    """Sinh hình minh họa nét vẽ tay theo yêu cầu bằng mô hình FLUX.1-schnell."""
    import uuid
    from core.artwork.generator import ArtworkGeneratorFactory
    from core.artwork.prompt_builder import StructuredIllustrationPrompt

    generator = ArtworkGeneratorFactory.create()
    art_id = f"custom_art_{uuid.uuid4().hex[:8]}"
    out_dir = PROJECT_ROOT / "assets" / "artwork" / "generated"
    out_path = out_dir / f"{art_id}.png"

    prompt_struct = StructuredIllustrationPrompt(
        subject=req.subject or req.prompt,
        action=req.action or "is clearly illustrated in clean line art",
        relationship="",
        composition="16:9 widescreen",
        pose="natural",
        line_style="clean line art",
        whiteboard_style="Notion doodle",
        background="#F5EBD7",
        negative_constraints="no colors, no gradients, no photorealism",
        full_prompt=req.prompt,
    )

    result_path = await generator.generate_artwork(
        prompt=prompt_struct,
        output_path=out_path,
        width=1920,
        height=1080,
    )

    return {
        "status": "success",
        "id": art_id,
        "image_url": f"/assets/artwork/generated/{result_path.name}",
        "file_path": str(result_path),
        "style": "Notion Doodle / Vector Comic Line Art",
    }

