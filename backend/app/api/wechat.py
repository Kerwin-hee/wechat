"""微信公众号对接 API"""

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.common import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wechat", tags=["公众号"])


@router.post("/auth", response_model=APIResponse[dict])
async def wechat_auth(
    user_id: Annotated[str, Depends(get_current_user)],
):
    """获取公众号授权二维码"""
    # TODO: 调用微信第三方平台接口获取授权二维码
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="公众号授权待微信第三方平台资质就绪后实现",
    )


@router.get("/auth/callback", response_model=APIResponse[dict])
async def wechat_auth_callback(
    auth_code: str,
    user_id: Annotated[str, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """公众号授权回调"""
    # TODO: 用 auth_code 换取 authorizer_access_token
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="公众号授权待微信第三方平台资质就绪后实现",
    )


@router.get("/materials", response_model=APIResponse[dict])
async def get_materials(
    user_id: Annotated[str, Depends(get_current_user)],
    page: int = 1,
    page_size: int = 20,
):
    """获取公众号素材列表"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="素材管理待公众号授权就绪后实现",
    )


@router.post("/draft", response_model=APIResponse[dict])
async def publish_draft(
    user_id: Annotated[str, Depends(get_current_user)],
):
    """发布草稿到公众号"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="草稿发布待公众号授权就绪后实现",
    )


@router.post("/publish", response_model=APIResponse[dict])
async def publish_article(
    user_id: Annotated[str, Depends(get_current_user)],
):
    """群发文章"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="群发待公众号授权就绪后实现",
    )
