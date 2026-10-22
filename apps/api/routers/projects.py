from __future__ import annotations

import datetime
import uuid
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, status, UploadFile, File
from pydantic import BaseModel, Field

router = APIRouter(prefix="/projects", tags=["Projects"])


class ProjectSummary(BaseModel):
    id: str
    title: str
    description: str = ""
    aspect_ratio: str = "16:9"
    template_id: str = "notion_minimal"
    status: str = "completed"
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_sec: float = 5.3
    scene_count: int = 1
    created_at: str
    updated_at: str


# In-memory store initialized with Phase 9 demo project
_PROJECTS_DB: Dict[str, ProjectSummary] = {
    "proj-monkey-banana-01": ProjectSummary(
        id="proj-monkey-banana-01",
        title="Con khỉ trèo cây lấy chuối",
        description="Demo sản xuất nội dung Whiteboard hoạt hình tự động từ ý tưởng đến video MP4 Full HD.",
        aspect_ratio="16:9",
        template_id="notion_minimal",
        status="completed",
        video_url="/media/monkey_banana_e2e/scene_default_final.mp4",
        thumbnail_url="/media/monkey_banana_e2e/scene_default.png",
        duration_sec=5.3,
        scene_count=1,
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )
}


class CreateProjectRequest(BaseModel):
    title: str = Field(min_length=1)
    description: str = ""
    template_id: str = "notion_minimal"
    aspect_ratio: str = "16:9"


@router.get("", response_model=List[ProjectSummary])
async def list_projects() -> List[ProjectSummary]:
    """Trả về danh sách các dự án video Whiteboard."""
    return list(_PROJECTS_DB.values())


@router.post("", response_model=ProjectSummary, status_code=status.HTTP_201_CREATED)
async def create_project(req: CreateProjectRequest) -> ProjectSummary:
    """Tạo mới một dự án video Whiteboard."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    proj_id = f"proj-{int(datetime.datetime.now().timestamp())}-{uuid.uuid4().hex[:6]}"
    proj = ProjectSummary(
        id=proj_id,
        title=req.title,
        description=req.description,
        template_id=req.template_id,
        aspect_ratio=req.aspect_ratio,
        status="draft",
        video_url=None,
        thumbnail_url=None,
        duration_sec=0.0,
        scene_count=1,
        created_at=now,
        updated_at=now,
    )
    _PROJECTS_DB[proj_id] = proj
    return proj


@router.get("/{project_id}", response_model=ProjectSummary)
async def get_project(project_id: str) -> ProjectSummary:
    """Lấy chi tiết dự án theo ID."""
    if project_id not in _PROJECTS_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found",
        )
    return _PROJECTS_DB[project_id]


@router.post("/{project_id}/duplicate", response_model=ProjectSummary, status_code=status.HTTP_201_CREATED)
async def duplicate_project(project_id: str) -> ProjectSummary:
    """
    Nhân bản dự án (Duplicate): Tạo bản sao nguyên vẹn của kịch bản, ảnh và âm thanh (Task 10.4).
    """
    import shutil
    from pathlib import Path
    project_root = Path(__file__).resolve().parent.parent.parent.parent

    if project_id not in _PROJECTS_DB:
        # Fallback tạo project summary nếu là ID mới
        orig = ProjectSummary(
            id=project_id,
            title="Dự án Whiteboard",
            description="",
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )
    else:
        orig = _PROJECTS_DB[project_id]

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    new_id = f"proj-{int(datetime.datetime.now().timestamp())}-{uuid.uuid4().hex[:6]}"


    # Sao chép thư mục tài nguyên storyboard trên ổ đĩa
    orig_storyboard = project_root / "output" / "storyboard" / project_id
    new_storyboard = project_root / "output" / "storyboard" / new_id
    if orig_storyboard.exists():
        new_storyboard.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(orig_storyboard, new_storyboard, dirs_exist_ok=True)

    # Sao chép thư mục export nếu có
    orig_export = project_root / "output" / "export" / project_id
    new_export = project_root / "output" / "export" / new_id
    if orig_export.exists():
        new_export.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(orig_export, new_export, dirs_exist_ok=True)

    # Cập nhật đường dẫn thumbnail và video nếu trỏ vào project cũ
    new_thumb = orig.thumbnail_url
    if new_thumb and project_id in new_thumb:
        new_thumb = new_thumb.replace(project_id, new_id)

    new_video = orig.video_url
    if new_video and project_id in new_video:
        new_video = new_video.replace(project_id, new_id)

    duplicated = ProjectSummary(
        id=new_id,
        title=f"{orig.title} (Bản sao)",
        description=orig.description,
        template_id=orig.template_id,
        aspect_ratio=orig.aspect_ratio,
        status=orig.status,
        video_url=new_video,
        thumbnail_url=new_thumb,
        duration_sec=orig.duration_sec,
        scene_count=orig.scene_count,
        created_at=now,
        updated_at=now,
    )
    _PROJECTS_DB[new_id] = duplicated
    return duplicated


@router.get("/{project_id}/export-package")
async def export_project_package(project_id: str):
    """
    Xuất file dự án (.whiteboard): Đóng gói toàn bộ script, hình ảnh và audio vào một file zip (Task 10.4).
    """
    import zipfile
    import json
    import re
    from pathlib import Path
    from fastapi.responses import FileResponse
    project_root = Path(__file__).resolve().parent.parent.parent.parent

    if project_id not in _PROJECTS_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found",
        )
    proj = _PROJECTS_DB[project_id]

    packages_dir = project_root / "output" / "packages"
    packages_dir.mkdir(parents=True, exist_ok=True)
    package_file = packages_dir / f"{project_id}.whiteboard"

    # Tạo zip package
    with zipfile.ZipFile(package_file, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. Ghi project.json
        zf.writestr("project.json", json.dumps(proj.model_dump(), ensure_ascii=False, indent=2))

        # 2. Đóng gói storyboard assets
        sb_dir = project_root / "output" / "storyboard" / project_id
        if sb_dir.exists():
            for f in sb_dir.rglob("*"):
                if f.is_file():
                    arcname = f"storyboard/{f.relative_to(sb_dir)}"
                    zf.write(f, arcname)

        # 3. Đóng gói export assets (video, subtitles)
        exp_dir = project_root / "output" / "export" / project_id
        if exp_dir.exists():
            for f in exp_dir.rglob("*"):
                if f.is_file():
                    arcname = f"export/{f.relative_to(exp_dir)}"
                    zf.write(f, arcname)

    safe_title = re.sub(r'[\\/*?:"<>| ]', "_", proj.title) or "project"
    return FileResponse(
        path=str(package_file),
        media_type="application/zip",
        filename=f"{safe_title}.whiteboard",
    )


@router.post("/import-package", response_model=ProjectSummary, status_code=status.HTTP_201_CREATED)
async def import_project_package(file: UploadFile = File(...)) -> ProjectSummary:
    """
    Nhập file dự án (.whiteboard): Khôi phục nguyên trạng dự án từ file nén package (Task 10.4).
    """
    import zipfile
    import json
    import shutil
    from pathlib import Path
    project_root = Path(__file__).resolve().parent.parent.parent.parent

    temp_zip = project_root / "output" / f"temp_import_{int(datetime.datetime.now().timestamp())}.zip"
    temp_zip.parent.mkdir(parents=True, exist_ok=True)

    with temp_zip.open("wb") as buf:
        shutil.copyfileobj(file.file, buf)

    try:
        with zipfile.ZipFile(temp_zip, "r") as zf:
            namelist = zf.namelist()
            if "project.json" not in namelist:
                raise HTTPException(status_code=400, detail="File .whiteboard không hợp lệ: Thiếu project.json")

            raw_proj = zf.read("project.json").decode("utf-8")
            proj_data = json.loads(raw_proj)

            new_id = f"proj-{int(datetime.datetime.now().timestamp())}-{uuid.uuid4().hex[:6]}"
            now = datetime.datetime.now(datetime.timezone.utc).isoformat()

            # Trích xuất storyboard
            target_sb = project_root / "output" / "storyboard" / new_id
            target_exp = project_root / "output" / "export" / new_id

            for member in namelist:
                if member.startswith("storyboard/"):
                    rel = member[len("storyboard/"):]
                    if rel and not rel.endswith("/"):
                        dest = target_sb / rel
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_bytes(zf.read(member))
                elif member.startswith("export/"):
                    rel = member[len("export/"):]
                    if rel and not rel.endswith("/"):
                        dest = target_exp / rel
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_bytes(zf.read(member))

            orig_id = proj_data.get("id", "default")
            new_thumb = proj_data.get("thumbnail_url")
            if new_thumb and orig_id in new_thumb:
                new_thumb = new_thumb.replace(orig_id, new_id)

            new_video = proj_data.get("video_url")
            if new_video and orig_id in new_video:
                new_video = new_video.replace(orig_id, new_id)

            imported = ProjectSummary(
                id=new_id,
                title=f"{proj_data.get('title', 'Dự án đã nhập')} (Đã nhập)",
                description=proj_data.get("description", ""),
                template_id=proj_data.get("template_id", "notion_minimal"),
                aspect_ratio=proj_data.get("aspect_ratio", "16:9"),
                status=proj_data.get("status", "draft"),
                video_url=new_video,
                thumbnail_url=new_thumb,
                duration_sec=float(proj_data.get("duration_sec", 0.0)),
                scene_count=int(proj_data.get("scene_count", 1)),
                created_at=now,
                updated_at=now,
            )
            _PROJECTS_DB[new_id] = imported
            return imported
    finally:
        temp_zip.unlink(missing_ok=True)

