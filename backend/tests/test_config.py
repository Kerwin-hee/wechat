"""测试配置模块"""

import pytest
from app.core.config import Settings, get_settings


class TestConfig:
    """配置测试"""

    def test_default_settings(self):
        settings = Settings()
        assert settings.APP_NAME == "公众号文章编辑器"
        assert settings.PORT == 8000
        assert settings.ENVIRONMENT == "development"

    def test_get_settings_is_singleton(self):
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_ai_settings(self):
        settings = Settings()
        assert settings.AI_PRIMARY_PROVIDER in ("openai", "deepseek")
        assert settings.AI_REQUEST_TIMEOUT == 60
        assert settings.AI_MAX_TOKENS_DEFAULT == 2048
