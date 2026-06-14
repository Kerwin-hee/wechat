"""通用响应模型 — 与前后端联调对接文档对齐"""

import uuid
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


def _gen_request_id() -> str:
    return uuid.uuid4().hex


class APIResponse(BaseModel, Generic[T]):
    """统一 API 响应格式

    ```json
    { "code": 0, "message": "success", "data": {...}, "request_id": "uuid" }
    ```
    """

    code: int = 0
    message: str = "success"
    data: T | None = None
    request_id: str = Field(default_factory=_gen_request_id)


class Pagination(BaseModel):
    """分页信息"""

    page: int
    page_size: int
    total: int
    total_pages: int


class PaginatedData(BaseModel, Generic[T]):
    """分页数据包裹"""

    list_: list[T] = Field(alias="list")
    pagination: Pagination

    model_config = {"populate_by_name": True}


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""

    code: int = 0
    message: str = "success"
    data: PaginatedData[T]
    request_id: str = Field(default_factory=_gen_request_id)
