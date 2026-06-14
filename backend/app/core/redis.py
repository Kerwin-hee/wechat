"""Redis 客户端"""

import redis.asyncio as aioredis

from app.core.config import get_settings

settings = get_settings()

redis_client: aioredis.Redis = aioredis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)


async def get_redis() -> aioredis.Redis:
    """FastAPI 依赖注入：获取 Redis 客户端"""
    return redis_client
