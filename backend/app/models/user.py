"""用户模型"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # 微信
    wechat_openid: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    wechat_unionid: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # 手机 / 邮箱
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 个人信息
    nickname: Mapped[str] = mapped_column(String(64), default="用户")
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # 会员
    is_pro: Mapped[bool] = mapped_column(Boolean, default=False)
    pro_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # 登录安全
    login_failed_count: Mapped[int] = mapped_column(default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 关联
    ai_quota: Mapped["AIQuota"] = relationship(back_populates="user", uselist=False)
