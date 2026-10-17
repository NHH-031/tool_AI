"""Structured Logging System for Whiteboard Video Studio.

Hỗ trợ:
- Correlation ID / Request ID tracking qua contextvars.
- Định dạng JSON có cấu trúc (Structured Logging) cho production/monitoring.
- Masking tự động cho các API keys nhạy cảm (Google, OpenAI, HuggingFace).
"""
from __future__ import annotations

import contextvars
import datetime
import json
import logging
import os
import re
from typing import Any, Dict

# Context variable lưu Request ID của request hiện tại
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")


def get_current_request_id() -> str:
    """Lấy Request ID của ngữ cảnh hiện tại."""
    return request_id_var.get()


def mask_sensitive_value(value: str) -> str:
    """Ẩn bớt ký tự của API key hoặc token nhạy cảm."""
    if not value or len(value) < 8:
        return "***"
    return f"{value[:4]}***{value[-4:]}"


def mask_sensitive_text(text: str) -> str:
    """Tự động mask các pattern API key trong chuỗi văn bản."""
    # Mask OpenAI keys (sk-...)
    text = re.sub(r"sk-[A-Za-z0-9]{20,}", lambda m: f"sk-{m.group(0)[3:7]}***{m.group(0)[-4:]}", text)
    # Mask HuggingFace tokens (hf_...)
    text = re.sub(r"hf_[A-Za-z0-9]{20,}", lambda m: f"hf_{m.group(0)[3:7]}***{m.group(0)[-4:]}", text)
    # Mask Gemini keys (AIza...)
    text = re.sub(r"AIza[A-Za-z0-9_\-]{20,}", lambda m: f"AIza***{m.group(0)[-4:]}", text)
    return text


class StructuredJsonFormatter(logging.Formatter):
    """Formatter xuất log định dạng JSON chuẩn cho CloudWatch / Datadog / Docker logs."""

    def format(self, record: logging.LogRecord) -> str:
        req_id = get_current_request_id()
        msg = record.getMessage()
        msg_masked = mask_sensitive_text(msg)

        payload: Dict[str, Any] = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": msg_masked,
            "request_id": req_id or getattr(record, "request_id", None),
        }

        # Bổ sung các extra fields nếu có
        for key in ["scene_id", "job_id", "duration_ms", "provider", "status_code"]:
            val = getattr(record, key, None)
            if val is not None:
                payload[key] = val

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


class ColoredConsoleFormatter(logging.Formatter):
    """Formatter đẹp mắt cho console khi chạy local development."""

    COLORS = {
        "DEBUG": "\033[36m",    # Cyan
        "INFO": "\033[32m",     # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",    # Red
        "CRITICAL": "\033[35m", # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        req_id = get_current_request_id()
        req_part = f"[{req_id[:8]}] " if req_id else ""
        msg = mask_sensitive_text(record.getMessage())
        return f"{color}[{record.levelname[:4]}]{self.RESET} {req_part}{record.name}: {msg}"


def setup_logging(use_json: bool = False, level: int = logging.INFO) -> None:
    """Thiết lập logging toàn cục cho hệ thống."""
    root = logging.getLogger()
    root.setLevel(level)

    # Xóa các handler cũ nếu có
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler()
    if use_json or os.getenv("LOG_FORMAT", "").lower() == "json":
        handler.setFormatter(StructuredJsonFormatter())
    else:
        handler.setFormatter(ColoredConsoleFormatter())

    root.addHandler(handler)
