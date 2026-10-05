from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional, Type, TypeVar
import httpx
from pydantic import BaseModel

from .base import LLMMessage, LLMProvider, LLMResponse

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMProviderError(Exception):
    """Lỗi nền tảng từ phía dịch vụ LLM Provider."""
    pass


class LLMStructuredOutputError(LLMProviderError):
    """Lỗi khi LLM trả về nội dung không thỏa mãn schema có cấu trúc."""
    def __init__(self, message: str, raw_content: str = ""):
        super().__init__(message)
        self.raw_content = raw_content


class GeminiProvider(LLMProvider):
    """
    Adapter kết nối Google Gemini thông qua REST API chuẩn của Google Cloud,
    hỗ trợ Structured Output với JSON schema và độc lập với phiên bản SDK.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.5-flash",
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        timeout_seconds: float = 60.0,
    ):
        self.api_key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY", "")
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def _prepare_contents(self, messages: List[LLMMessage]) -> Dict[str, Any]:
        """Chuyển đổi danh sách LLMMessage sang định dạng payload của Gemini."""
        contents: List[Dict[str, Any]] = []
        system_instructions: List[str] = []

        for msg in messages:
            role = msg.role.lower()
            if role == "system":
                system_instructions.append(msg.content)
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": msg.content}]})
            else:
                contents.append({"role": "user", "parts": [{"text": msg.content}]})

        # Nếu không có tin nhắn user nào, bổ sung 1 tin nhắn trống
        if not contents:
            contents.append({"role": "user", "parts": [{"text": ""}]})

        payload: Dict[str, Any] = {"contents": contents}
        if system_instructions:
            payload["system_instruction"] = {
                "parts": [{"text": "\n\n".join(system_instructions)}]
            }
        return payload

    async def generate_text(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Sinh văn bản tự do từ danh sách tin nhắn thông qua Gemini."""
        if not self.api_key:
            raise LLMProviderError("GEMINI_API_KEY chưa được cấu hình. Vui lòng thiết lập biến môi trường hoặc truyền api_key.")

        url = f"{self.base_url}/models/{self.model_name}:generateContent?key={self.api_key}"
        payload = self._prepare_contents(messages)
        gen_config: Dict[str, Any] = {"temperature": temperature}
        if max_tokens:
            gen_config["maxOutputTokens"] = max_tokens
        payload["generationConfig"] = gen_config

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            try:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
            except httpx.HTTPStatusError as e:
                err_text = e.response.text if e.response else str(e)
                raise LLMProviderError(f"Gemini API returned error {e.response.status_code}: {err_text}") from e
            except Exception as e:
                raise LLMProviderError(f"Gemini connection failure: {str(e)}") from e

        try:
            candidates = data.get("candidates", [])
            if not candidates:
                raise LLMProviderError(f"Gemini returned empty candidates: {data}")
            first_candidate = candidates[0]
            parts = first_candidate.get("content", {}).get("parts", [])
            content = parts[0].get("text", "") if parts else ""
            usage = data.get("usageMetadata", {})
            return LLMResponse(
                content=content,
                token_usage={
                    "prompt_tokens": usage.get("promptTokenCount", 0),
                    "completion_tokens": usage.get("candidatesTokenCount", 0),
                    "total_tokens": usage.get("totalTokenCount", 0),
                },
                model_name=self.model_name,
            )
        except Exception as e:
            raise LLMProviderError(f"Failed to parse Gemini response: {e}") from e

    async def generate_structured(
        self,
        messages: List[LLMMessage],
        response_schema: Type[T],
        temperature: float = 0.2,
    ) -> T:
        """Sinh dữ liệu có cấu trúc tuân thủ chính xác Pydantic Schema."""
        if not self.api_key:
            raise LLMProviderError("GEMINI_API_KEY chưa được cấu hình. Vui lòng thiết lập biến môi trường hoặc truyền api_key.")

        url = f"{self.base_url}/models/{self.model_name}:generateContent?key={self.api_key}"
        payload = self._prepare_contents(messages)

        # Cấu hình structured JSON output của Gemini
        payload["generationConfig"] = {
            "temperature": temperature,
            "responseMimeType": "application/json",
            "responseSchema": response_schema.model_json_schema(),
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            try:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
            except httpx.HTTPStatusError as e:
                err_text = e.response.text if e.response else str(e)
                raise LLMProviderError(f"Gemini API error {e.response.status_code}: {err_text}") from e
            except Exception as e:
                raise LLMProviderError(f"Gemini request failed: {str(e)}") from e

        raw_text = ""
        try:
            candidates = data.get("candidates", [])
            if not candidates:
                raise LLMStructuredOutputError("Gemini returned empty candidates", raw_content=str(data))
            parts = candidates[0].get("content", {}).get("parts", [])
            raw_text = parts[0].get("text", "") if parts else ""
            
            # Phân giải thành Pydantic model
            return response_schema.model_validate_json(raw_text)
        except Exception as e:
            raise LLMStructuredOutputError(
                f"Failed to parse structured model {response_schema.__name__}: {str(e)}",
                raw_content=raw_text,
            ) from e
