"""支付 API — 与联调对接文档对齐"""

import logging
import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.common import APIResponse
from app.schemas.payment import CreateOrderRequest, OrderResponse, OrderStatusResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payment", tags=["支付"])

ORD_PREFIX = "ord_"

PLANS = {
    "pro_monthly": {
        "name": "Pro 月度",
        "price": 1990,  # 分
        "duration_days": 30,
    },
    "pro_yearly": {
        "name": "Pro 年度",
        "price": 19900,  # 分
        "duration_days": 365,
    },
}


@router.post("/order", response_model=APIResponse[OrderResponse])
async def create_order(
    req: CreateOrderRequest,
    user_id: Annotated[str, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """创建支付订单"""
    if req.plan not in PLANS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的付费方案")

    plan = PLANS[req.plan]
    order_id = f"{ORD_PREFIX}{uuid.uuid4().hex[:16]}"

    # TODO: 调用微信/支付宝统一下单
    return APIResponse(
        data=OrderResponse(
            order_id=order_id,
            amount=plan["price"],
        )
    )


@router.get("/order/{order_id}", response_model=APIResponse[OrderStatusResponse])
async def get_order_status(
    order_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
):
    """查询订单状态"""
    # TODO: 查询真实订单状态
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="订单查询待支付商户号就绪后实现",
    )


@router.post("/wechat/notify", response_model=APIResponse[None])
async def wechat_pay_notify():
    """微信支付回调"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="支付回调待支付商户号就绪后实现",
    )


@router.post("/alipay/notify", response_model=APIResponse[None])
async def alipay_notify():
    """支付宝回调"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="支付回调待支付商户号就绪后实现",
    )
