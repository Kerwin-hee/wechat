"""应用配置，基于 pydantic-settings 管理环境变量"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── 应用 ──
    APP_NAME: str = "公众号文章编辑器"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # ── 服务 ──
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── CORS ──
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # ── 数据库 (PostgreSQL) ──
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/wechat_editor"

    # ── Redis ──
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT ──
    JWT_SECRET_KEY: str = "change-me-in-production-use-a-strong-random-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── AI 服务 ──
    AI_PRIMARY_PROVIDER: Literal["openai", "deepseek"] = "openai"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    AI_REQUEST_TIMEOUT: int = 60  # 秒
    AI_MAX_TOKENS_DEFAULT: int = 2048

    # ── 微信 ──
    WECHAT_APP_ID: str = ""
    WECHAT_APP_SECRET: str = ""
    WECHAT_TOKEN: str = ""
    WECHAT_ENCODING_AES_KEY: str = ""
    # 第三方平台
    WECHAT_COMPONENT_APP_ID: str = ""
    WECHAT_COMPONENT_APP_SECRET: str = ""
    WECHAT_COMPONENT_TOKEN: str = ""
    WECHAT_COMPONENT_AES_KEY: str = ""

    # ── 短信 (阿里云) ──
    SMS_ACCESS_KEY_ID: str = ""
    SMS_ACCESS_KEY_SECRET: str = ""
    SMS_SIGN_NAME: str = ""
    SMS_TEMPLATE_CODE: str = ""

    # ── 支付 ──
    WECHAT_PAY_MCH_ID: str = ""
    WECHAT_PAY_API_V3_KEY: str = ""
    WECHAT_PAY_SERIAL_NO: str = ""
    WECHAT_PAY_PRIVATE_KEY_PATH: str = ""
    ALIPAY_APP_ID: str = ""
    ALIPAY_PRIVATE_KEY_PATH: str = ""
    ALIPAY_PUBLIC_KEY_PATH: str = ""


@lru_cache()
def get_settings() -> Settings:
    return Settings()
