"""文章相关 Schema — 与联调对接文档对齐"""

from datetime import datetime

from pydantic import BaseModel, Field


# ── 请求 ──


class ArticleCreateRequest(BaseModel):
    title: str = Field(default="未命名文章", max_length=255)
    content: str = Field(default="<p></p>")  # HTML
    status: str = Field(default="draft")


class ArticleUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    content: str | None = None  # HTML
    summary: str | None = Field(default=None, max_length=500)
    tags: list[str] | None = None


# ── 响应 ──


class ArticleListItem(BaseModel):
    """文章列表项（不含 content 详情）"""

    id: str  # art_ 前缀
    title: str
    plain_text: str
    word_count: int
    image_count: int
    total_image_size: int
    status: str  # draft / published / trash
    cover_url: str | None = None
    summary: str | None = None
    tags: list[str] = []
    created_at: str
    updated_at: str
    published_at: str | None = None
    sync_status: str = "local_only"  # synced / syncing / failed / local_only


class ArticleDetailResponse(BaseModel):
    """文章详情（含 content）"""

    id: str
    title: str
    content: str  # HTML
    plain_text: str
    word_count: int
    image_count: int
    total_image_size: int
    status: str
    cover_url: str | None = None
    summary: str | None = None
    wechat_media_id: str | None = None
    wechat_publish_url: str | None = None
    tags: list[str] = []
    created_at: str
    updated_at: str
    published_at: str | None = None


class ArticleVersionItem(BaseModel):
    """版本历史项"""

    id: str  # ver_ 前缀
    article_id: str
    version_number: int
    title: str
    content: str  # HTML
    word_count: int
    diff_from_previous: str | None = None
    created_at: str


class VersionRestoreResponse(BaseModel):
    """恢复版本后返回当前文章"""
    # 直接复用文章详情
    article: ArticleDetailResponse
    version_number: int
