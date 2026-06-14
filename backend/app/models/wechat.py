"""微信公众号绑定模型"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WechatAccount(Base):
    __tablename__ = "wechat_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    authorizer_appid: Mapped[str] = mapped_column(String(64), unique=True)
    authorizer_access_token: Mapped[str] = mapped_column(Text)
    authorizer_refresh_token: Mapped[str] = mapped_column(Text)
    token_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # 公众号信息
    nickname: Mapped[str | None] = mapped_column(String(128), nullable=True)
    head_img: Mapped[str | None] = mapped_column(String(512), nullable=True)
    service_type: Mapped[int | None] = mapped_column(nullable=True)
    verify_type: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
