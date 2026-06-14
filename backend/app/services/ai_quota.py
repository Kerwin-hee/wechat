"""AI 额度管理服务"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_quota import AIQuota

logger = logging.getLogger(__name__)

# 免费用户每日额度
FREE_QUOTA_LIMITS = {
    "full_article": 3,
    "continue": 10,
    "rewrite": 5,
    "outline": 5,
    "title_optimize": 5,
}


class QuotaExceededError(Exception):
    """额度已用完"""

    def __init__(self, ai_type: str, used: int, limit: int):
        self.ai_type = ai_type
        self.used = used
        self.limit = limit
        super().__init__(f"{ai_type} 额度已用完 ({used}/{limit})")


async def get_or_create_quota(db: AsyncSession, user_id: UUID) -> AIQuota:
    result = await db.execute(select(AIQuota).where(AIQuota.user_id == user_id))
    quota = result.scalar_one_or_none()
    if quota is None:
        quota = AIQuota(
            user_id=user_id,
            **{f"{k}_limit": v for k, v in FREE_QUOTA_LIMITS.items()},
        )
        db.add(quota)
        await db.flush()
    return quota


async def check_and_consume_quota(
    db: AsyncSession,
    user_id: UUID,
    ai_type: str,
    is_pro: bool = False,
) -> AIQuota:
    """检查并消耗额度，PRO 用户不限"""
    quota = await get_or_create_quota(db, user_id)

    if is_pro:
        return quota

    used_field = f"{ai_type}_used"
    limit_field = f"{ai_type}_limit"

    current_used: int = getattr(quota, used_field, 0)
    current_limit: int = getattr(quota, limit_field, 0)

    if current_used >= current_limit:
        raise QuotaExceededError(ai_type, current_used, current_limit)

    setattr(quota, used_field, current_used + 1)
    await db.flush()
    return quota


async def get_quota_info(db: AsyncSession, user_id: UUID, is_pro: bool) -> dict:
    quota = await get_or_create_quota(db, user_id)
    return {
        "full_article_used": quota.full_article_used,
        "full_article_limit": quota.full_article_limit,
        "continue_used": quota.continue_used,
        "continue_limit": quota.continue_limit,
        "rewrite_used": quota.rewrite_used,
        "rewrite_limit": quota.rewrite_limit,
        "outline_used": quota.outline_used,
        "outline_limit": quota.outline_limit,
        "title_used": quota.title_used,
        "title_limit": quota.title_limit,
        "is_pro": is_pro,
        "reset_at": quota.reset_at.isoformat() if quota.reset_at else "",
    }
