"""用户相关 Schema — 与联调对接文档对齐"""

from pydantic import BaseModel, EmailStr, Field


# ── 微信登录 ──


class WechatQRCodeResponse(BaseModel):
    qrcode_url: str
    scene_id: str
    expires_in: int = 300


class WechatStatusResponse(BaseModel):
    status: str  # pending / scanned / success / expired


class WechatUserInfo(BaseModel):
    id: str  # usr_ 前缀
    nickname: str
    avatar: str
    membership: str = "free"  # free / pro
    is_new_user: bool = False


class WechatLoginSuccessResponse(BaseModel):
    status: str = "success"
    access_token: str
    refresh_token: str
    expires_in: int = 7200
    user: WechatUserInfo


# ── Token ──


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int = 7200


# ── 手机/邮箱 ──


class PhoneLoginRequest(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")
    code: str = Field(..., min_length=4, max_length=6)


class SendCodeRequest(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")


class EmailRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    nickname: str = Field(default="用户", max_length=64)


class EmailLoginRequest(BaseModel):
    email: EmailStr
    password: str


# ── 用户信息 ──


class UserProfileResponse(BaseModel):
    id: str
    nickname: str
    avatar: str | None = None
    membership: str = "free"
    is_new_user: bool = False
