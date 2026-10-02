from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
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
