"""
订单管理路由

所有返回格式使用统一的 success_response / paginated_response。
异常使用统一的 ApiError 体系，由 error handler 转换为标准错误响应。
"""
from fastapi import APIRouter, Query, Path
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from utils.errors import NotFoundError, ValidationError, ApiError, ErrorCode
from utils.responses import success_response, paginated_response

router = APIRouter()


# ============================================================
# 请求/响应模型
# ============================================================

class OrderItemCreate(BaseModel):
    sku_id: str = Field(..., description="SKU ID")
    product_name: str = Field(..., description="商品名称")
    quantity: int = Field(..., gt=0, description="数量")
    unit_price: float = Field(..., ge=0, description="单价")


class OrderCreate(BaseModel):
    platform: str = Field(..., description="来源平台: douyin | kuaishou | pinduoduo | xianyu")
    platform_order_id: str = Field(..., description="平台订单号")
    items: List[OrderItemCreate] = Field(..., min_length=1, description="商品列表")
    customer_name: str = Field(..., description="客户姓名")
    customer_phone: str = Field(..., description="客户电话")
    customer_address: str = Field(..., description="收货地址")
    remarks: Optional[str] = Field(None, description="备注")


class OrderUpdateStatus(BaseModel):
    status: str = Field(
        ...,
        description="目标状态: pending | processing | shipped | delivered | completed | cancelled | refunding | refunded",
    )
    tracking_number: Optional[str] = Field(None, description="发货时填写运单号")
    carrier: Optional[str] = Field(None, description="发货时填写承运商")


VALID_ORDER_STATUSES = {
    "pending", "processing", "shipped", "delivered",
    "completed", "cancelled", "refunding", "refunded",
}

VALID_PLATFORMS = {"douyin", "kuaishou", "pinduoduo", "xianyu"}

# 状态流转规则: from -> allowed_to
STATUS_TRANSITIONS = {
    "pending": {"processing", "cancelled"},
    "processing": {"shipped", "cancelled"},
    "shipped": {"delivered", "refunding"},
    "delivered": {"completed", "refunding"},
    "completed": {"refunding"},
    "refunding": {"refunded"},
    "refunded": set(),
    "cancelled": set(),
}


# ============================================================
# 模拟数据存储（后续替换为数据库）
# ============================================================
_orders_db: dict = {}
_order_counter = 0


def _next_order_id() -> str:
    global _order_counter
    _order_counter += 1
    return f"ORD-{_order_counter:06d}"


# ============================================================
# 路由
# ============================================================

@router.get("/")
async def list_orders(
    platform: Optional[str] = Query(None, description="按平台筛选"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """获取订单列表（支持平台、状态筛选和分页）"""
    if platform and platform not in VALID_PLATFORMS:
        raise ValidationError(
            message=f"无效的平台: {platform}",
            detail=f"支持的平台: {', '.join(VALID_PLATFORMS)}",
        )
    if status and status not in VALID_ORDER_STATUSES:
        raise ValidationError(
            message=f"无效的订单状态: {status}",
            detail=f"支持的状态: {', '.join(VALID_ORDER_STATUSES)}",
        )

    items = list(_orders_db.values())
    if platform:
        items = [o for o in items if o["platform"] == platform]
    if status:
        items = [o for o in items if o["status"] == status]

    total = len(items)
    start = (page - 1) * page_size
    paged = items[start : start + page_size]

    return paginated_response(items=paged, total=total, page=page, page_size=page_size)


@router.post("/")
async def create_order(order: OrderCreate):
    """创建订单"""
    if order.platform not in VALID_PLATFORMS:
        raise ValidationError(
            message=f"无效的平台: {order.platform}",
            detail=f"支持的平台: {', '.join(VALID_PLATFORMS)}",
        )

    # 检查平台订单号是否重复
    for existing in _orders_db.values():
        if existing["platform_order_id"] == order.platform_order_id:
            raise ApiError(
                code=ErrorCode.RESOURCE_ALREADY_EXISTS,
                message=f"平台订单号 '{order.platform_order_id}' 已存在",
            )

    order_id = _next_order_id()
    now = datetime.now().isoformat()
    total_amount = sum(item.unit_price * item.quantity for item in order.items)

    record = {
        "order_id": order_id,
        "platform": order.platform,
        "platform_order_id": order.platform_order_id,
        "status": "pending",
        "payment_status": "unpaid",
        "items": [item.model_dump() for item in order.items],
        "total_amount": total_amount,
        "discount_amount": 0,
        "actual_amount": total_amount,
        "customer": {
            "name": order.customer_name,
            "phone": order.customer_phone,
            "address": order.customer_address,
        },
        "shipping": None,
        "payment": None,
        "remarks": order.remarks,
        "tags": [],
        "created_at": now,
        "updated_at": now,
    }
    _orders_db[order_id] = record

    return success_response(data=record, message="订单创建成功")


@router.get("/{order_id}")
async def get_order(order_id: str = Path(..., description="订单ID")):
    """获取订单详情"""
    order = _orders_db.get(order_id)
    if not order:
        raise NotFoundError(resource="订单", resource_id=order_id)
    return success_response(data=order)


@router.patch("/{order_id}/status")
async def update_order_status(
    order_id: str = Path(..., description="订单ID"),
    body: OrderUpdateStatus = ...,
):
    """更新订单状态（遵循状态机规则）"""
    order = _orders_db.get(order_id)
    if not order:
        raise NotFoundError(resource="订单", resource_id=order_id)

    if body.status not in VALID_ORDER_STATUSES:
        raise ValidationError(
            message=f"无效的目标状态: {body.status}",
            detail=f"支持的状态: {', '.join(VALID_ORDER_STATUSES)}",
        )

    current = order["status"]
    allowed = STATUS_TRANSITIONS.get(current, set())
    if body.status not in allowed:
        raise ApiError(
            code=ErrorCode.OPERATION_CONFLICT,
            message=f"不允许从 '{current}' 转换到 '{body.status}'",
            detail=f"允许的目标状态: {', '.join(sorted(allowed)) if allowed else '无（终态）'}",
        )

    # 发货时必须提供物流信息
    if body.status == "shipped":
        if not body.tracking_number or not body.carrier:
            raise ValidationError(
                message="发货时必须提供运单号和承运商",
                detail="tracking_number 和 carrier 字段为必填",
            )
        order["shipping"] = {
            "carrier": body.carrier,
            "tracking_number": body.tracking_number,
            "shipping_method": "express",
        }
        order["shipped_at"] = datetime.now().isoformat()

    if body.status == "completed":
        order["completed_at"] = datetime.now().isoformat()

    order["status"] = body.status
    order["updated_at"] = datetime.now().isoformat()

    return success_response(data=order, message=f"订单状态已更新为 '{body.status}'")


@router.delete("/{order_id}")
async def delete_order(order_id: str = Path(..., description="订单ID")):
    """删除订单（仅 pending 状态可删除）"""
    order = _orders_db.get(order_id)
    if not order:
        raise NotFoundError(resource="订单", resource_id=order_id)

    if order["status"] != "pending":
        raise ApiError(
            code=ErrorCode.OPERATION_CONFLICT,
            message=f"只有 pending 状态的订单可以删除，当前状态: {order['status']}",
        )

    del _orders_db[order_id]
    return success_response(message=f"订单 {order_id} 已删除")
