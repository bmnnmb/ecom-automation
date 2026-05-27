"""
标准化成功响应工具

统一所有API的成功响应格式:
{
    "success": true,
    "data": { ... },
    "meta": { "page": 1, "total": 100, ... }  # 分页时可选
}
"""
from typing import Any, Optional, Dict, List
from fastapi.encoders import jsonable_encoder


def success_response(data: Any = None, message: Optional[str] = None) -> dict:
    """构造标准化成功响应"""
    body: dict = {"success": True}
    if data is not None:
        body["data"] = jsonable_encoder(data)
    if message:
        body["message"] = message
    return body


def paginated_response(
    items: List[Any],
    total: int,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """构造分页响应"""
    return {
        "success": True,
        "data": jsonable_encoder(items),
        "meta": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
        },
    }
