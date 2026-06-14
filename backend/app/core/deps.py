"""FastAPI 依赖注入：JWT 鉴权"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import TokenPayload, decode_token

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
) -> str:
    """从请求头 Bearer Token 中提取当前用户 ID"""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
        )

    payload: TokenPayload | None = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌无效或已过期",
        )

    return payload.sub


async def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
) -> str | None:
    """可选的用户认证：未登录返回 None"""
    if credentials is None:
        return None
    payload: TokenPayload | None = decode_token(credentials.credentials)
    if payload is None:
        return None
    return payload.sub
