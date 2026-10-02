from __future__ import annotations

import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Cấu hình ứng dụng tải từ biến môi trường hoặc .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Whiteboard Video Production Studio API"
    app_version: str = "0.1.0"
    app_env: str = Field(default="development", description="development | staging | production")
    debug: bool = Field(default=True)
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000)

    # CORS
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    # Provider Keys (Tất cả đều để trống làm mặc định, không hardcode)
    gemini_api_key: str = Field(default="", description="Google Gemini API Key")
    openai_api_key: str = Field(default="", description="OpenAI API Key")
    elevenlabs_api_key: str = Field(default="", description="ElevenLabs API Key")

    # Storage
    storage_type: str = Field(default="local", description="local | memory | s3")
    storage_base_dir: str = Field(default="./out/storage")


settings = AppSettings()
