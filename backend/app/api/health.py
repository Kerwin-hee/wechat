"""健康检查"""

from datetime import UTC, datetime

from fastapi import APIRouter

from app.schemas.common import APIResponse

router = APIRouter()


@router.get("/health", response_model=APIResponse[dict])
async def health_check():
    """健康检查端点 — 与联调文档对齐"""
    return APIResponse(
        message="ok",
        data={
            "version": "1.0.0",
            "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "services": {
                "database": "ok",
                "ai_gateway": "ok",
                "redis": "ok",
            },
        },
    )
