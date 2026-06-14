"""文章管理 API — 与联调对接文档对齐

ID 格式：art_<uuid_hex>
"""

import logging
import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.article import Article, ArticleVersion
from app.schemas.article import (
    ArticleCreateRequest,
    ArticleDetailResponse,
    ArticleListItem,
    ArticleUpdateRequest,
    ArticleVersionItem,
)
from app.schemas.common import APIResponse, PaginatedData, Pagination, PaginatedResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/articles", tags=["文章"])

MAX_FREE_VERSIONS = 20

# ── ID 前缀工具 ──

ART_PREFIX = "art_"
VER_PREFIX = "ver_"


def _art_id(uid: uuid.UUID) -> str:
    return f"{ART_PREFIX}{uid.hex[:16]}"


def _ver_id(uid: uuid.UUID) -> str:
    return f"{VER_PREFIX}{uid.hex[:16]}"


def _parse_art_id(raw: str) -> uuid.UUID:
    """从 art_xxx 中解析 UUID"""
    if raw.startswith(ART_PREFIX):
        raw = raw[len(ART_PREFIX):]
    return uuid.UUID(raw)


def _parse_ver_id(raw: str) -> uuid.UUID:
    if raw.startswith(VER_PREFIX):
        raw = raw[len(VER_PREFIX):]
    return uuid.UUID(raw)


# ── 格式化工具 ──

def _fmt_time(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _article_to_list_item(a: Article) -> ArticleListItem:
    import json as _json
    tags = []
    if a.tags:
        try:
            tags = _json.loads(a.tags)
        except _json.JSONDecodeError:
            pass
    return ArticleListItem(
        id=_art_id(a.id),
        title=a.title,
        plain_text=a.plain_text,
        word_count=a.word_count,
        image_count=a.image_count,
        total_image_size=a.total_image_size,
        status=a.status,
        cover_url=a.cover_url,
        summary=a.summary,
        tags=tags,
        created_at=_fmt_time(a.created_at) or "",
        updated_at=_fmt_time(a.updated_at) or "",
        published_at=_fmt_time(a.published_at),
        sync_status="synced" if a.status != "local" else "local_only",
    )


def _article_to_detail(a: Article) -> ArticleDetailResponse:
    import json as _json
    tags = []
    if a.tags:
        try:
            tags = _json.loads(a.tags)
        except _json.JSONDecodeError:
            pass
    return ArticleDetailResponse(
        id=_art_id(a.id),
        title=a.title,
        content=a.content,
        plain_text=a.plain_text,
        word_count=a.word_count,
        image_count=a.image_count,
        total_image_size=a.total_image_size,
        status=a.status,
        cover_url=a.cover_url,
        summary=a.summary,
        wechat_media_id=a.wechat_media_id,
        wechat_publish_url=a.wechat_publish_url,
        tags=tags,
        created_at=_fmt_time(a.created_at) or "",
        updated_at=_fmt_time(a.updated_at) or "",
        published_at=_fmt_time(a.published_at),
    )


# ── 创建文章 ──

@router.post("", response_model=APIResponse[ArticleDetailResponse], status_code=status.HTTP_201_CREATED)
async def create_article(
    req: ArticleCreateRequest,
    user_id: Annotated[str, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # 计算 plain_text 和 word_count
    plain_text = _html_to_plain(req.content)
    word_count = len(plain_text)

    article = Article(
        user_id=_parse_art_id(user_id) if user_id.startswith(ART_PREFIX) else uuid.UUID(user_id),
        title=req.title,
        content=req.content,
        plain_text=plain_text,
        word_count=word_count,
        status=req.status,
    )
    db.add(article)
    await db.flush()
    await db.refresh(article)

    # 创建首个版本
    version = ArticleVersion(
        article_id=article.id,
        version_number=1,
        title=req.title,
        content=req.content,
        word_count=word_count,
    )
    db.add(version)
    await db.flush()

    return APIResponse(data=_article_to_detail(article))


# ── 文章列表 ──

@router.get("", response_model=PaginatedResponse[ArticleListItem])
async def list_articles(
    user_id: Annotated[str, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    keyword: str | None = None,
    sort_by: str | None = Query(default=None, pattern="^(created_at|updated_at|word_count)$"),
    order: str | None = Query(default=None, pattern="^(asc|desc)$"),
):
    uid = _parse_art_id(user_id) if user_id.startswith(ART_PREFIX) else uuid.UUID(user_id)

    conditions = [
        Article.user_id == uid,
        Article.deleted_at.is_(None),
    ]
    if status:
        conditions.append(Article.status == status)
    if keyword:
        conditions.append(
            or_(
                Article.title.ilike(f"%{keyword}%"),
                Article.plain_text.ilike(f"%{keyword}%"),
            )
        )

    # 总数
    count_q = select(func.count(Article.id)).where(and_(*conditions))
    total = (await db.execute(count_q)).scalar() or 0

    # 排序
    sort_col = getattr(Article, sort_by, Article.updated_at) if sort_by else Article.updated_at
    if order == "asc":
        sort_col = sort_col.asc()
    else:
        sort_col = sort_col.desc()

    offset = (page - 1) * page_size
    q = (
        select(Article)
        .where(and_(*conditions))
        .order_by(sort_col)
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(q)
    articles = result.scalars().all()

    total_pages = max(1, (total + page_size - 1) // page_size)

    return PaginatedResponse(
        data=PaginatedData(
            list_=[_article_to_list_item(a) for a in articles],
            pagination=Pagination(
                page=page,
                page_size=page_size,
                total=total,
                total_pages=total_pages,
            ),
        )
    )


# ── 文章详情 ──

@router.get("/{article_id}", response_model=APIResponse[ArticleDetailResponse])
async def get_article(
    article_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    uid = _parse_art_id(user_id) if user_id.startswith(ART_PREFIX) else uuid.UUID(user_id)
    aid = _parse_art_id(article_id)
    article = await _get_user_article(db, aid, uid)
    return APIResponse(data=_article_to_detail(article))


# ── 更新文章 ──

@router.put("/{article_id}", response_model=APIResponse[ArticleDetailResponse])
async def update_article(
    article_id: str,
    req: ArticleUpdateRequest,
    user_id: Annotated[str, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    uid = _parse_art_id(user_id) if user_id.startswith(ART_PREFIX) else uuid.UUID(user_id)
    aid = _parse_art_id(article_id)
    article = await _get_user_article(db, aid, uid)

    update_data = req.model_dump(exclude_unset=True)

    # 处理 tags
    if "tags" in update_data and update_data["tags"] is not None:
        update_data["tags"] = json.dumps(update_data["tags"])

    # 如果 content 更新了，重新计算 plain_text 和 word_count
    if "content" in update_data and update_data["content"] is not None:
        update_data["plain_text"] = _html_to_plain(update_data["content"])
        update_data["word_count"] = len(update_data["plain_text"])

    for key, value in update_data.items():
        setattr(article, key, value)

    await db.flush()
    await db.refresh(article)

    # 内容变更时创建版本快照
    if "content" in update_data or "title" in update_data:
        v_q = (
            select(func.max(ArticleVersion.version_number))
            .where(ArticleVersion.article_id == aid)
        )
        latest_v = (await db.execute(v_q)).scalar() or 0
        new_version = ArticleVersion(
            article_id=article.id,
            version_number=latest_v + 1,
            title=article.title,
            content=article.content,
            word_count=article.word_count,
        )
        db.add(new_version)

        # 免费用户版本上限
        version_count_q = select(func.count(ArticleVersion.id)).where(
            ArticleVersion.article_id == aid
        )
        version_count = (await db.execute(version_count_q)).scalar() or 0
        if version_count > MAX_FREE_VERSIONS:
            oldest_q = (
                select(ArticleVersion)
                .where(ArticleVersion.article_id == aid)
                .order_by(ArticleVersion.version_number.asc())
                .limit(1)
            )
            oldest = (await db.execute(oldest_q)).scalar_one_or_none()
            if oldest:
                await db.delete(oldest)

    return APIResponse(data=_article_to_detail(article))


# ── 删除文章（软删除）──

@router.delete("/{article_id}", response_model=APIResponse[None])
async def delete_article(
    article_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    uid = _parse_art_id(user_id) if user_id.startswith(ART_PREFIX) else uuid.UUID(user_id)
    aid = _parse_art_id(article_id)
    article = await _get_user_article(db, aid, uid)
    article.deleted_at = datetime.now(UTC)
    article.status = "trash"
    await db.flush()
    return APIResponse(message="已移至回收站")


# ── 版本历史 ──

@router.get("/{article_id}/versions", response_model=PaginatedResponse[ArticleVersionItem])
async def get_versions(
    article_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    uid = _parse_art_id(user_id) if user_id.startswith(ART_PREFIX) else uuid.UUID(user_id)
    aid = _parse_art_id(article_id)
    await _get_user_article(db, aid, uid)

    count_q = select(func.count(ArticleVersion.id)).where(ArticleVersion.article_id == aid)
    total = (await db.execute(count_q)).scalar() or 0

    offset = (page - 1) * page_size
    q = (
        select(ArticleVersion)
        .where(ArticleVersion.article_id == aid)
        .order_by(ArticleVersion.version_number.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(q)
    versions = result.scalars().all()

    total_pages = max(1, (total + page_size - 1) // page_size)

    return PaginatedResponse(
        data=PaginatedData(
            list_=[
                ArticleVersionItem(
                    id=_ver_id(v.id),
                    article_id=_art_id(v.article_id),
                    version_number=v.version_number,
                    title=v.title,
                    content=v.content,
                    word_count=v.word_count,
                    diff_from_previous=v.diff_from_previous,
                    created_at=_fmt_time(v.created_at) or "",
                )
                for v in versions
            ],
            pagination=Pagination(
                page=page,
                page_size=page_size,
                total=total,
                total_pages=total_pages,
            ),
        )
    )


# ── 恢复版本 ──

@router.post("/{article_id}/restore/{version_id}", response_model=APIResponse[ArticleDetailResponse])
async def restore_version(
    article_id: str,
    version_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    uid = _parse_art_id(user_id) if user_id.startswith(ART_PREFIX) else uuid.UUID(user_id)
    aid = _parse_art_id(article_id)
    vid = _parse_ver_id(version_id)

    article = await _get_user_article(db, aid, uid)

    v_q = select(ArticleVersion).where(
        and_(ArticleVersion.id == vid, ArticleVersion.article_id == aid)
    )
    result = await db.execute(v_q)
    version = result.scalar_one_or_none()
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="版本不存在")

    article.title = version.title
    article.content = version.content
    article.word_count = version.word_count
    await db.flush()
    await db.refresh(article)

    return APIResponse(data=_article_to_detail(article))


# ── 辅助 ──

import json as _json
import re


async def _get_user_article(db: AsyncSession, article_id: uuid.UUID, user_id: uuid.UUID) -> Article:
    q = select(Article).where(
        and_(
            Article.id == article_id,
            Article.user_id == user_id,
            Article.deleted_at.is_(None),
        )
    )
    result = await db.execute(q)
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")
    return article


def _html_to_plain(html: str) -> str:
    """从 HTML 提取纯文本"""
    # 简单实现：去掉 HTML 标签
    clean = re.sub(r"<[^>]+>", "", html)
    clean = re.sub(r"&[a-z]+;", " ", clean)
    return clean.strip()
