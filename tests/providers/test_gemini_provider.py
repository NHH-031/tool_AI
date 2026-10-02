import pytest
import httpx
from core.providers.base import LLMMessage
from core.providers.gemini import GeminiProvider, LLMProviderError, LLMStructuredOutputError
from core.schemas.script import ScriptOutput


def test_gemini_provider_prepare_contents():
    """Kiểm tra GeminiProvider chuyển đổi đúng các role sang payload của Gemini."""
    provider = GeminiProvider(api_key="mock-key", model_name="gemini-1.5-flash")
    messages = [
        LLMMessage(role="system", content="System instruction content"),
        LLMMessage(role="user", content="User prompt question"),
        LLMMessage(role="assistant", content="Assistant previous answer"),
    ]
    payload = provider._prepare_contents(messages)

    assert "system_instruction" in payload
    assert payload["system_instruction"]["parts"][0]["text"] == "System instruction content"
    assert len(payload["contents"]) == 2
    assert payload["contents"][0]["role"] == "user"
    assert payload["contents"][0]["parts"][0]["text"] == "User prompt question"
    assert payload["contents"][1]["role"] == "model"
    assert payload["contents"][1]["parts"][0]["text"] == "Assistant previous answer"


@pytest.mark.asyncio
async def test_gemini_provider_requires_api_key():
    """Kiểm tra báo lỗi rõ ràng khi không có API key."""
    provider = GeminiProvider(api_key="")
    with pytest.raises(LLMProviderError, match="GEMINI_API_KEY chưa được cấu hình"):
        await provider.generate_text([LLMMessage(role="user", content="Hello")])

    with pytest.raises(LLMProviderError, match="GEMINI_API_KEY chưa được cấu hình"):
        await provider.generate_structured([LLMMessage(role="user", content="Hello")], ScriptOutput)
