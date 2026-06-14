"""用户相关 API（额度查询等）— 与联调对接文档对齐"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.ai import AIQuotaItem, AIQuotaResponse
from app.schemas.common import APIResponse
from app.services.ai_quota import get_quota_info

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["用户"])


@router.get("/quota", response_model=APIResponse[AIQuotaResponse])
async def get_quota(
    user_id: Annotated[str, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """查询当前用户 AI 额度 — GET /api/user/quota"""
    # TODO: 从数据库获取 is_pro
    is_pro = False
    info = await get_quota_info(db, user_id, is_pro)

    return APIResponse(
        data=AIQuotaResponse(
            full_article=AIQuotaItem(
                used=info["full_article_used"],
                limit=info["full_article_limit"] if not is_pro else None,
            ),
            continue_writing=AIQuotaItem(
                used=info["continue_used"],
                limit=info["continue_limit"] if not is_pro else None,
            ),
            rewrite=AIQuotaItem(
                used=info["rewrite_used"],
                limit=info["rewrite_limit"] if not is_pro else None,
            ),
            outline=AIQuotaItem(
                used=info["outline_used"],
                limit=info["outline_limit"] if not is_pro else None,
            ),
            title_optimize=AIQuotaItem(
                used=info["title_used"],
                limit=info["title_limit"] if not is_pro else None,
            ),
            reset_at=info["reset_at"],
            is_unlimited=is_pro,
        )
    )
