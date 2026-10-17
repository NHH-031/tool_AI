import json
import logging
import time
from core.logger import mask_sensitive_text, StructuredJsonFormatter, request_id_var
from core.rate_limiter import SlidingWindowRateLimiter


def test_mask_sensitive_text():
    openai_key = "sk-1234567890abcdef1234567890abcdef"
    masked_openai = mask_sensitive_text(f"Key is {openai_key}")
    assert "sk-1234***cdef" in masked_openai
    assert openai_key not in masked_openai

    hf_token = "hf_abcdefghijklmnopqrstuvwxyz012345"
    masked_hf = mask_sensitive_text(f"Token is {hf_token}")
    assert "hf_abcd***2345" in masked_hf
    assert hf_token not in masked_hf

    gemini_key = "AIzaSyD-1234567890abcdef123456789"
    masked_gemini = mask_sensitive_text(f"Gemini: {gemini_key}")
    assert "AIza***6789" in masked_gemini
    assert gemini_key not in masked_gemini


def test_structured_json_formatter():
    formatter = StructuredJsonFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test message with sk-1234567890abcdef1234567890abcdef",
        args=(),
        exc_info=None,
    )
    request_id_var.set("req-test-123")
    formatted = formatter.format(record)
    data = json.loads(formatted)

    assert data["level"] == "INFO"
    assert data["logger"] == "test_logger"
    assert data["request_id"] == "req-test-123"
    assert "sk-1234***cdef" in data["message"]


def test_sliding_window_rate_limiter():
    limiter = SlidingWindowRateLimiter(requests_per_minute=3)
    ip = "192.168.1.100"

    assert limiter.is_allowed(ip) is True
    assert limiter.is_allowed(ip) is True
    assert limiter.is_allowed(ip) is True
    # 4th hit should be rejected
    assert limiter.is_allowed(ip) is False
    assert limiter.get_retry_after(ip) > 0

    # Another IP should still be allowed
    assert limiter.is_allowed("192.168.1.101") is True
