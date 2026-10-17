from __future__ import annotations

import json
import logging
import os
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel

from .base import LLMMessage, LLMProvider, LLMResponse

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class OllamaProvider(LLMProvider):
    """
    Nhà cung cấp LLM Local qua Ollama.
    Mặc định kết nối tới http://localhost:11434 để chạy model Qwen 3.6:35B-A3B (hoặc model tùy biến).
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.model_name = model_name or os.getenv("OLLAMA_MODEL", "qwen3.6:35b-a3b")

    def is_available(self) -> bool:
        """Kiểm tra xem Ollama service có đang chạy không."""
        try:
            url = f"{self.base_url}/api/tags"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                return resp.status == 200
        except Exception:
            return False

    async def generate_text(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        url = f"{self.base_url}/api/chat"
        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120.0) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                content = res_json.get("message", {}).get("content", "")
                prompt_tokens = res_json.get("prompt_eval_count", 0)
                eval_tokens = res_json.get("eval_count", 0)
                return LLMResponse(
                    content=content,
                    token_usage={"prompt_tokens": prompt_tokens, "completion_tokens": eval_tokens},
                    model_name=self.model_name,
                )
        except Exception as e:
            logger.error(f"[OllamaProvider] Error calling {url}: {e}")
            raise RuntimeError(f"Ollama call failed: {e}")

    async def generate_structured(
        self,
        messages: List[LLMMessage],
        response_schema: Type[T],
        temperature: float = 0.2,
    ) -> T:
        schema_json = json.dumps(response_schema.model_json_schema(), ensure_ascii=False)
        system_instruction = (
            f"You are a structured JSON generator. You MUST respond with ONLY a valid JSON object matching this schema:\n"
            f"{schema_json}\nDo not include any other markdown formatting or conversational text."
        )

        augmented_messages = [LLMMessage(role="system", content=system_instruction)] + messages

        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model_name,
            "messages": [{"role": m.role, "content": m.content} for m in augmented_messages],
            "format": "json",
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=120.0) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            content = res_json.get("message", {}).get("content", "")

        return response_schema.model_validate_json(content)
