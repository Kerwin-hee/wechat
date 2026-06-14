"""AI 服务 API — 与联调对接文档对齐

统一端点：POST /api/ai/generate，通过 type 区分功能
SSE 事件：event: started/token/done/error
"""

import asyncio
import json
import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.ai import AIGenerateRequest, AIQuotaItem, AIQuotaResponse, AIType
from app.schemas.common import APIResponse
from app.services.ai_gateway import get_ai_gateway
from app.services.ai_prompts import (
    build_continue_messages,
    build_full_article_messages,
    build_outline_messages,
    build_rewrite_messages,
    build_title_optimize_messages,
)
from app.services.ai_quota import check_and_consume_quota, get_quota_info

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI"])


def _sse_event(event: str, data: dict) -> str:
    """构造 SSE 事件帧"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _build_quota_remaining(info: dict) -> dict:
    """构建 quota_remaining 结构"""
    return {
        "full_article": info["full_article_used"],
        "continue_writing": info["continue_used"],
    }


@router.post("/generate")
async def ai_generate(
    req: AIGenerateRequest,
    request: Request,
    user_id: Annotated[str, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """统一的 AI 生成端点 — SSE 流式返回

    通过 type 字段区分：
    - full_article: 全文生成
    - continue_writing: 续写
    - rewrite: 改写
    - outline: 大纲生成
    - title_optimize: 标题优化
    """
    request_id = uuid.uuid4().hex
    ai_type = req.type.value

    # 将文档 type 映射到内部额度 key
    quota_type_map = {
        "full_article": "full_article",
        "continue_writing": "continue",
        "rewrite": "rewrite",
        "outline": "outline",
        "title_optimize": "title_optimize",
    }
    quota_key = quota_type_map[ai_type]

    # 检查额度
    try:
        await check_and_consume_quota(db, user_id, quota_key)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))

    # 获取剩余额度
    quota_info = await get_quota_info(db, user_id, is_pro=False)

    # 根据 type 构建消息
    gateway = get_ai_gateway()
    options = req.options or None

    # 对于 rewrite 和 title_optimize 等非流式场景，直接返回
    if ai_type == "rewrite":
        return await _handle_rewrite(req, user_id, db, request_id, quota_info)
    if ai_type == "outline":
        return await _handle_outline(req, user_id, db, request_id, quota_info)
    if ai_type == "title_optimize":
        return await _handle_title_optimize(req, user_id, db, request_id, quota_info)

    # 流式场景：full_article 和 continue_writing
    if ai_type == "full_article":
        word_count = 1500
        if options and options.word_count:
            wc = options.word_count
            if "-" in wc:
                parts = wc.split("-")
                word_count = (int(parts[0]) + int(parts[1])) // 2
        messages = build_full_article_messages(
            topic=req.context,
            target_audience=options.target_audience if options else None,
            style=options.style if options else None,
            word_count=word_count,
            reference_materials=options.reference_materials if options else None,
        )
    else:
        messages = build_continue_messages(context=req.context[-500:])

    async def event_stream():
        # started 事件
        yield _sse_event("started", {
            "request_id": request_id,
            "quota_remaining": _build_quota_remaining(quota_info),
        })

        full_text = ""
        token_index = 0
        try:
            async for token in gateway.chat_completion_stream(messages):
                full_text += token
                yield _sse_event("token", {"token": token, "index": token_index})
                token_index += 1

            # done 事件
            yield _sse_event("done", {
                "total_tokens": len(full_text),
                "finish_reason": "stop",
                "quota_remaining": {"full_article": quota_info.get("full_article_used", 0)},
            })
        except asyncio.TimeoutError:
            yield _sse_event("error", {
                "code": 2001,
                "message": "AI 服务超时",
                "quota_consumed": False,
            })
        except Exception as e:
            logger.error("AI generate error: %s", e)
            yield _sse_event("error", {
                "code": 2002,
                "message": str(e)[:200],
                "quota_consumed": False,
            })

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _handle_rewrite(req, user_id, db, request_id, quota_info) -> APIResponse:
    """改写 — 非流式"""
    import difflib

    options = req.options
    style = options.style if options and options.style else "concise"
    messages = build_rewrite_messages(text=req.context, style=style)
    gateway = get_ai_gateway()

    try:
        result = await gateway.chat_completion(messages, max_tokens=2048)
        rewritten = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    return APIResponse(
        data={
            "original": req.context,
            "rewritten": rewritten,
            "request_id": request_id,
        }
    )


async def _handle_outline(req, user_id, db, request_id, quota_info) -> APIResponse:
    """大纲生成 — 非流式"""
    messages = build_outline_messages(topic=req.context)
    gateway = get_ai_gateway()

    try:
        result = await gateway.chat_completion(messages, max_tokens=2048, temperature=0.5)
        raw = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        outline_data = _extract_json(raw)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    return APIResponse(data={"outline": outline_data, "request_id": request_id})


async def _handle_title_optimize(req, user_id, db, request_id, quota_info) -> APIResponse:
    """标题优化 — 非流式"""
    messages = build_title_optimize_messages(content=req.context)
    gateway = get_ai_gateway()

    try:
        result = await gateway.chat_completion(messages, max_tokens=2048, temperature=0.8)
        raw = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        title_data = _extract_json(raw)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    return APIResponse(data={"candidates": title_data.get("candidates", []), "request_id": request_id})


def _extract_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        raw = "\n".join(lines)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw}
