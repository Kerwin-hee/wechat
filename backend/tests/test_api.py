"""测试 API 端点 — 与联调文档对齐"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    """测试 /api/health 端点 — 含 services 和 request_id"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["version"] == "1.0.0"
        assert "services" in data["data"]
        assert data["data"]["services"]["database"] == "ok"
        assert "request_id" in data


@pytest.mark.asyncio
async def test_health_has_request_id():
    """测试响应中包含 request_id"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/health")
        data = resp.json()
        assert "request_id" in data
        assert len(data["request_id"]) == 32  # uuid hex


@pytest.mark.asyncio
async def test_auth_required():
    """测试未认证时受保护端点返回 401"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/user/quota")
        assert resp.status_code == 401
