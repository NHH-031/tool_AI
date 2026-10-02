from apps.api.config import AppSettings


def test_default_config():
    cfg = AppSettings()
    assert cfg.app_name == "AI Whiteboard Video Production Studio API"
    assert cfg.port == 8000
    assert cfg.gemini_api_key == ""
    assert cfg.openai_api_key == ""
    assert cfg.storage_type == "local"
