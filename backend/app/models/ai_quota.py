"""AI 额度模型"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AIQuota(Base):
    __tablename__ = "ai_quotas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    # 各类型额度
    full_article_used: Mapped[int] = mapped_column(Integer, default=0)
    full_article_limit: Mapped[int] = mapped_column(Integer, default=3)
    continue_used: Mapped[int] = mapped_column(Integer, default=0)
    continue_limit: Mapped[int] = mapped_column(Integer, default=10)
    rewrite_used: Mapped[int] = mapped_column(Integer, default=0)
    rewrite_limit: Mapped[int] = mapped_column(Integer, default=5)
    outline_used: Mapped[int] = mapped_column(Integer, default=0)
    outline_limit: Mapped[int] = mapped_column(Integer, default=5)
    title_used: Mapped[int] = mapped_column(Integer, default=0)
    title_limit: Mapped[int] = mapped_column(Integer, default=5)
    # 会员
    is_pro: Mapped[bool] = mapped_column(Boolean, default=False)
    # 每日重置时间
    reset_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # 关联
    user: Mapped["User"] = relationship(back_populates="ai_quota")
