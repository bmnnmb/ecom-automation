"""
售后服务路由

使用统一错误处理和标准化响应格式。
"""
from fastapi import APIRouter, Query, Path
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

from utils.errors import NotFoundError, ValidationError, ApiError, ErrorCode
from utils.responses import success_response, paginated_response

router = APIRouter()


# ============================================================
# 请求/响应模型
# ============================================================

class AftersaleCreate(BaseModel):
    order_id: str = Field(..., description="关联订单ID")
    platform: str = Field(..., description="来源平台")
    type: str = Field(..., description="售后类型: refund | return | exchange")
    reason: str = Field(..., min_length=1, max_length=500, description="售后原因")
    amount: Optional[float] = Field(None, ge=0, description="退款金额（退款类型时必填）")
    customer_id: Optional[str] = Field(None, description="客户ID")
    description: Optional[str] = Field(None, max_length=2000, description="详细描述")


class AftersaleUpdate(BaseModel):
    status: Optional[str] = Field(None, description="售后状态")
    admin_remark: Optional[str] = Field(None, max_length=1000, description="管理员备注")
    refund_amount: Optional[float] = Field(None, ge=0, description="实际退款金额")


VALID_AFTERSALE_TYPES = {"refund", "return", "exchange"}
VALID_AFTERSALE_STATUSES = {"pending", "approved", "rejected", "processing", "completed", "cancelled"}


# ============================================================
# 模拟数据存储
# ============================================================
_aftersales_db: dict = {}
_aftersale_counter = 0


def _next_aftersale_id() -> str:
    global _aftersale_counter
    _aftersale_counter += 1
    return f"AS-{_aftersale_counter:06d}"


# ============================================================
# 路由
# ============================================================

@router.get("/")
async def list_aftersales(
    platform: Optional[str] = Query(None, description="按平台筛选"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    aftersale_type: Optional[str] = Query(None, alias="type", description="按售后类型筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """获取售后服务列表"""
    if status and status not in VALID_AFTERSALE_STATUSES:
        raise ValidationError(
            message=f"无效的售后状态: {status}",
            detail=f"支持的状态: {', '.join(VALID_AFTERSALE_STATUSES)}",
        )
    if aftersale_type and aftersale_type not in VALID_AFTERSALE_TYPES:
        raise ValidationError(
            message=f"无效的售后类型: {aftersale_type}",
            detail=f"支持的类型: {', '.join(VALID_AFTERSALE_TYPES)}",
        )

    items = list(_aftersales_db.values())
    if platform:
        items = [a for a in items if a["platform"] == platform]
    if status:
        items = [a for a in items if a["status"] == status]
    if aftersale_type:
        items = [a for a in items if a["type"] == aftersale_type]

    total = len(items)
    start = (page - 1) * page_size
    paged = items[start : start + page_size]

    return paginated_response(items=paged, total=total, page=page, page_size=page_size)


@router.post("/")
async def create_aftersale(aftersale: AftersaleCreate):
    """创建售后工单"""
    if aftersale.type not in VALID_AFTERSALE_TYPES:
        raise ValidationError(
            message=f"无效的售后类型: {aftersale.type}",
            detail=f"支持的类型: {', '.join(VALID_AFTERSALE_TYPES)}",
        )

    if aftersale.type == "refund" and (aftersale.amount is None or aftersale.amount <= 0):
        raise ValidationError(
            message="退款类型必须提供退款金额",
            detail="amount 字段为必填且须大于0",
        )

    as_id = _next_aftersale_id()
    now = datetime.now().isoformat()

    record = {
        "id": as_id,
        "order_id": aftersale.order_id,
        "platform": aftersale.platform,
        "type": aftersale.type,
        "reason": aftersale.reason,
        "amount": aftersale.amount,
        "customer_id": aftersale.customer_id,
        "description": aftersale.description,
        "status": "pending",
        "admin_remark": None,
        "refund_amount": None,
        "created_at": now,
        "updated_at": now,
    }
    _aftersales_db[as_id] = record

    return success_response(data=record, message="售后工单创建成功")


@router.get("/{aftersale_id}")
async def get_aftersale(aftersale_id: str = Path(..., description="售后工单ID")):
    """获取售后工单详情"""
    aftersale = _aftersales_db.get(aftersale_id)
    if not aftersale:
        raise NotFoundError(resource="售后工单", resource_id=aftersale_id)
    return success_response(data=aftersale)


@router.patch("/{aftersale_id}")
async def update_aftersale(
    aftersale_id: str = Path(..., description="售后工单ID"),
    body: AftersaleUpdate = ...,
):
    """更新售后工单"""
    aftersale = _aftersales_db.get(aftersale_id)
    if not aftersale:
        raise NotFoundError(resource="售后工单", resource_id=aftersale_id)

    if body.status and body.status not in VALID_AFTERSALE_STATUSES:
        raise ValidationError(
            message=f"无效的售后状态: {body.status}",
            detail=f"支持的状态: {', '.join(VALID_AFTERSALE_STATUSES)}",
        )

    update_data = body.model_dump(exclude_unset=True)
    aftersale.update(update_data)
    aftersale["updated_at"] = datetime.now().isoformat()

    return success_response(data=aftersale, message="售后工单更新成功")
