"""支付相关 Schema — 与联调对接文档对齐"""

from pydantic import BaseModel, Field


class CreateOrderRequest(BaseModel):
    plan: str = Field(..., pattern="^(pro_monthly|pro_yearly)$")
    payment_method: str = Field(..., pattern="^(wechat|alipay)$")


class OrderResponse(BaseModel):
    order_id: str  # ord_ 前缀
    payment_url: str | None = None
    qr_code: str | None = None
    amount: int  # 分


class OrderStatusResponse(BaseModel):
    order_id: str
    status: str  # pending / paid / failed / refunded
    plan: str
    amount: int
    paid_at: str | None = None
    membership_expires_at: str | None = None
