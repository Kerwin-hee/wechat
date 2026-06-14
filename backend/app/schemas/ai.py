"""AI 相关 Schema — 与联调对接文档对齐"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── 枚举 ──


class AIType(str, Enum):
    full_article = "full_article"
    continue_writing = "continue_writing"
    rewrite = "rewrite"
    outline = "outline"
    title_optimize = "title_optimize"


class AIStyle(str, Enum):
    formal = "formal"
    casual = "casual"
    concise = "concise"
    passionate = "passionate"
    professional = "professional"


class AITargetAudience(str, Enum):
    general = "general"
    professional = "professional"
    tech = "tech"
    student = "student"


class AIWordCount(str, Enum):
    w500_1000 = "500-1000"
    w1000_2000 = "1000-2000"
    w2000_3000 = "2000-3000"


# ── 请求 ──


class AIOptions(BaseModel):
    style: str | None = None
    target_audience: str | None = None
    word_count: str | None = None  # "500-1000" / "1000-2000" / "2000-3000"
    reference_materials: str | None = None


class AIGenerateRequest(BaseModel):
    """统一的 AI 生成请求 — 通过 type 区分功能"""

    type: AIType
    context: str = Field(..., min_length=1, max_length=5000)
    options: AIOptions | None = None


# ── 响应 ──


class AIQuotaItem(BaseModel):
    used: int
    limit: int | None  # 付费用户为 null


class AIQuotaResponse(BaseModel):
    full_article: AIQuotaItem
    continue_writing: AIQuotaItem
    rewrite: AIQuotaItem
    outline: AIQuotaItem
    title_optimize: AIQuotaItem
    reset_at: str  # ISO 8601
    is_unlimited: bool
