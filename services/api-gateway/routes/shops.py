"""
店铺管理路由

使用统一错误处理和标准化响应格式。
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

class ShopCreate(BaseModel):
    platform: str = Field(..., description="平台: douyin | kuaishou | pinduoduo | xianyu")
    shop_name: str = Field(..., min_length=1, max_length=100, description="店铺名称")
    shop_url: Optional[str] = Field(None, description="店铺链接")


class ShopUpdate(BaseModel):
    shop_name: Optional[str] = Field(None, min_length=1, max_length=100, description="店铺名称")
    shop_url: Optional[str] = Field(None, description="店铺链接")
    auth_status: Optional[str] = Field(None, description="授权状态")


VALID_PLATFORMS = {"douyin", "kuaishou", "pinduoduo", "xianyu"}
VALID_AUTH_STATUSES = {"pending", "authorized", "expired", "revoked"}


# ============================================================
# 模拟数据存储
# ============================================================
_shops_db: dict = {}
_shop_counter = 0


def _next_shop_id() -> str:
    global _shop_counter
    _shop_counter += 1
    return f"SHOP-{_shop_counter:06d}"


# ============================================================
# 路由
# ============================================================

@router.get("/")
async def list_shops(
    platform: Optional[str] = Query(None, description="按平台筛选"),
    auth_status: Optional[str] = Query(None, description="按授权状态筛选"),
):
    """获取店铺列表"""
    items = list(_shops_db.values())
    if platform:
        if platform not in VALID_PLATFORMS:
            raise ValidationError(
                message=f"无效的平台: {platform}",
                detail=f"支持的平台: {', '.join(VALID_PLATFORMS)}",
            )
        items = [s for s in items if s["platform"] == platform]
    if auth_status:
        items = [s for s in items if s["auth_status"] == auth_status]
    return success_response(data=items)


@router.post("/")
async def create_shop(shop: ShopCreate):
    """创建店铺"""
    if shop.platform not in VALID_PLATFORMS:
        raise ValidationError(
            message=f"无效的平台: {shop.platform}",
            detail=f"支持的平台: {', '.join(VALID_PLATFORMS)}",
        )

    # 检查同平台下是否重名
    for existing in _shops_db.values():
        if existing["platform"] == shop.platform and existing["shop_name"] == shop.shop_name:
            raise ApiError(
                code=ErrorCode.RESOURCE_ALREADY_EXISTS,
                message=f"同平台下已存在同名店铺 '{shop.shop_name}'",
            )

    shop_id = _next_shop_id()
    now = datetime.now().isoformat()

    record = {
        "id": shop_id,
        "platform": shop.platform,
        "shop_name": shop.shop_name,
        "shop_url": shop.shop_url,
        "auth_status": "pending",
        "created_at": now,
        "updated_at": now,
    }
    _shops_db[shop_id] = record
    return success_response(data=record, message="店铺创建成功")


@router.get("/{shop_id}")
async def get_shop(shop_id: str = Path(..., description="店铺ID")):
    """获取店铺详情"""
    shop = _shops_db.get(shop_id)
    if not shop:
        raise NotFoundError(resource="店铺", resource_id=shop_id)
    return success_response(data=shop)


@router.patch("/{shop_id}")
async def update_shop(
    shop_id: str = Path(..., description="店铺ID"),
    body: ShopUpdate = ...,
):
    """更新店铺信息"""
    shop = _shops_db.get(shop_id)
    if not shop:
        raise NotFoundError(resource="店铺", resource_id=shop_id)

    if body.auth_status and body.auth_status not in VALID_AUTH_STATUSES:
        raise ValidationError(
            message=f"无效的授权状态: {body.auth_status}",
            detail=f"支持的状态: {', '.join(VALID_AUTH_STATUSES)}",
        )

    update_data = body.model_dump(exclude_unset=True)
    shop.update(update_data)
    shop["updated_at"] = datetime.now().isoformat()

    return success_response(data=shop, message="店铺更新成功")


@router.delete("/{shop_id}")
async def delete_shop(shop_id: str = Path(..., description="店铺ID")):
    """删除店铺"""
    shop = _shops_db.get(shop_id)
    if not shop:
        raise NotFoundError(resource="店铺", resource_id=shop_id)

    del _shops_db[shop_id]
    return success_response(message=f"店铺 {shop_id} 已删除")
