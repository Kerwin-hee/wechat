"""FastAPI 应用入口"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ai, articles, auth, health, payment, user, wechat
from app.core.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    from app.services.ai_gateway import _ai_gateway

    global _ai_gateway
    _ai_gateway = None  # 重置，下次请求时懒加载
    yield
    # 关闭时
    from app.services.ai_gateway import get_ai_gateway

    gw = get_ai_gateway()
    await gw.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(articles.router, prefix="/api")
app.include_router(user.router, prefix="/api")
app.include_router(payment.router, prefix="/api")
app.include_router(wechat.router, prefix="/api")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
