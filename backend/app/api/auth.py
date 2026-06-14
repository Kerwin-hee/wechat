"""用户认证 API — 与联调对接文档对齐"""

import logging
import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.redis import get_redis
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.user import (
    EmailLoginRequest,
    EmailRegisterRequest,
    PhoneLoginRequest,
    SendCodeRequest,
    TokenRefreshRequest,
    TokenResponse,
    WechatLoginSuccessResponse,
    WechatQRCodeResponse,
    WechatStatusResponse,
    WechatUserInfo,
)

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/auth", tags=["认证"])

USR_PREFIX = "usr_"


def _usr_id(uid: uuid.UUID) -> str:
    return f"{USR_PREFIX}{uid.hex[:12]}"


# ── 微信扫码登录 ──


@router.get("/wechat/qrcode", response_model=APIResponse[WechatQRCodeResponse])
async def wechat_qrcode(redis: Annotated["Redis", Depends(get_redis)]):
    """获取微信扫码登录二维码"""
    scene_id = uuid.uuid4().hex[:16]
    # 存储 scene 到 Redis，5 分钟过期
    await redis.setex(f"wechat:scene:{scene_id}", 300, "pending")

    # TODO: 调用微信 OAuth 获取真实二维码
    qrcode_url = f"https://open.weixin.qq.com/connect/qrconnect?appid={settings.WECHAT_APP_ID}&state={scene_id}"

    return APIResponse(
        data=WechatQRCodeResponse(
            qrcode_url=qrcode_url,
            scene_id=scene_id,
            expires_in=300,
        )
    )


@router.get("/wechat/status", response_model=APIResponse[WechatStatusResponse])
async def wechat_status(
    redis: Annotated["Redis", Depends(get_redis)],
    db: Annotated[AsyncSession, Depends(get_db)],
    scene_id: str = Query(...),
):
    """轮询微信登录状态"""
    scene_data = await redis.get(f"wechat:scene:{scene_id}")
    if scene_data is None:
        return APIResponse(data=WechatStatusResponse(status="expired"))

    if scene_data == "success":
        # 获取已登录用户信息
        user_id_str = await redis.get(f"wechat:scene:{scene_id}:user")
        if user_id_str:
            user_uid = uuid.UUID(user_id_str)
            result = await db.execute(select(User).where(User.id == user_uid))
            user = result.scalar_one_or_none()
            if user:
                access_token = create_access_token(str(user.id))
                refresh_token = create_refresh_token(str(user.id))
                # 清理 scene
                await redis.delete(f"wechat:scene:{scene_id}")
                await redis.delete(f"wechat:scene:{scene_id}:user")

                return APIResponse(
                    data=WechatLoginSuccessResponse(
                        access_token=access_token,
                        refresh_token=refresh_token,
                        user=WechatUserInfo(
                            id=_usr_id(user.id),
                            nickname=user.nickname,
                            avatar=user.avatar_url or "",
                            membership="pro" if user.is_pro else "free",
                            is_new_user=False,
                        ),
                    ).model_dump()
                )

    if scene_data == "scanned":
        return APIResponse(data=WechatStatusResponse(status="scanned"))

    return APIResponse(data=WechatStatusResponse(status="pending"))


# ── 手机验证码登录 ──


@router.post("/phone/code", response_model=APIResponse[None])
async def send_phone_code(
    req: SendCodeRequest,
    redis: Annotated["Redis", Depends(get_redis)],
):
    """发送手机验证码"""
    existing = await redis.get(f"sms:code:{req.phone}")
    if existing:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="验证码已发送，请 60 秒后重试",
        )

    import random
    code = f"{random.randint(100000, 999999)}"
    logger.info("手机 %s 验证码: %s (模拟)", req.phone, code)
    await redis.setex(f"sms:code:{req.phone}", 300, code)

    return APIResponse(message="验证码已发送")


@router.post("/phone/login", response_model=APIResponse[TokenResponse])
async def phone_login(
    req: PhoneLoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated["Redis", Depends(get_redis)],
):
    """手机验证码登录"""
    stored_code = await redis.get(f"sms:code:{req.phone}")
    if stored_code is None or stored_code != req.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误或已过期",
        )
    await redis.delete(f"sms:code:{req.phone}")

    result = await db.execute(select(User).where(User.phone == req.phone))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            phone=req.phone,
            nickname=f"用户{req.phone[-4:]}",
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)

    return APIResponse(data=_issue_tokens(str(user.id)))


# ── 邮箱注册/登录 ──


@router.post("/email/register", response_model=APIResponse[TokenResponse], status_code=status.HTTP_201_CREATED)
async def email_register(
    req: EmailRegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    existing = await db.execute(select(User).where(User.email == req.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该邮箱已注册")

    user = User(
        email=req.email,
        password_hash=hash_password(req.password),
        nickname=req.nickname,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    return APIResponse(data=_issue_tokens(str(user.id)))


@router.post("/email/login", response_model=APIResponse[TokenResponse])
async def email_login(
    req: EmailLoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()

    if user is None or user.password_hash is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误")

    if user.locked_until and user.locked_until > datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="账户已锁定，请 15 分钟后重试")

    if not verify_password(req.password, user.password_hash):
        user.login_failed_count += 1
        if user.login_failed_count >= 5:
            user.locked_until = datetime.now(UTC).replace(minute=+15)
        await db.flush()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误")

    user.login_failed_count = 0
    user.locked_until = None
    await db.flush()

    return APIResponse(data=_issue_tokens(str(user.id)))


# ── Token 刷新 ──


@router.post("/refresh", response_model=APIResponse[TokenResponse])
async def refresh_token(req: TokenRefreshRequest):
    payload = decode_token(req.refresh_token)
    if payload is None or payload.type != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新令牌无效或已过期")

    return APIResponse(data=_issue_tokens(payload.sub))


# ── 辅助 ──


def _issue_tokens(user_id: str) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
        expires_in=7200,
    )
