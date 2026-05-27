"""
商品管理路由

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

class ProductCreate(BaseModel):
    shop_id: str = Field(..., description="店铺ID")
    title: str = Field(..., min_length=1, max_length=200, description="商品标题")
    price: float = Field(..., gt=0, description="售价")
    cost_price: Optional[float] = Field(None, ge=0, description="成本价")
    sku_id: Optional[str] = Field(None, description="SKU ID")
    category: Optional[str] = Field(None, description="商品分类")
    description: Optional[str] = Field(None, description="商品描述")
    stock: int = Field(0, ge=0, description="库存数量")


class ProductUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="商品标题")
    price: Optional[float] = Field(None, gt=0, description="售价")
    cost_price: Optional[float] = Field(None, ge=0, description="成本价")
    stock: Optional[int] = Field(None, ge=0, description="库存数量")
    status: Optional[str] = Field(None, description="商品状态")


VALID_PRODUCT_STATUSES = {"draft", "active", "inactive", "sold_out"}


# ============================================================
# 模拟数据存储
# ============================================================
_products_db: dict = {}
_product_counter = 0


def _next_product_id() -> str:
    global _product_counter
    _product_counter += 1
    return f"PROD-{_product_counter:06d}"


# ============================================================
# 路由
# ============================================================

@router.get("/")
async def list_products(
    shop_id: Optional[str] = Query(None, description="按店铺筛选"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """获取商品列表"""
    items = list(_products_db.values())

    if shop_id:
        items = [p for p in items if p["shop_id"] == shop_id]
    if status:
        items = [p for p in items if p["status"] == status]
    if keyword:
        kw = keyword.lower()
        items = [p for p in items if kw in p["title"].lower()]

    total = len(items)
    start = (page - 1) * page_size
    paged = items[start : start + page_size]

    return paginated_response(items=paged, total=total, page=page, page_size=page_size)


@router.post("/")
async def create_product(product: ProductCreate):
    """创建商品"""
    product_id = _next_product_id()
    now = datetime.now().isoformat()

    # 计算利润率
    margin = None
    if product.cost_price and product.cost_price > 0:
        margin = round((product.price - product.cost_price) / product.price * 100, 2)

    record = {
        "id": product_id,
        "shop_id": product.shop_id,
        "title": product.title,
        "price": product.price,
        "cost_price": product.cost_price,
        "sku_id": product.sku_id,
        "category": product.category,
        "description": product.description,
        "stock": product.stock,
        "status": "draft",
        "margin_rate": margin,
        "listing_risk_score": 0.0,
        "created_at": now,
        "updated_at": now,
    }
    _products_db[product_id] = record

    return success_response(data=record, message="商品创建成功")


@router.get("/{product_id}")
async def get_product(product_id: str = Path(..., description="商品ID")):
    """获取商品详情"""
    product = _products_db.get(product_id)
    if not product:
        raise NotFoundError(resource="商品", resource_id=product_id)
    return success_response(data=product)


@router.patch("/{product_id}")
async def update_product(
    product_id: str = Path(..., description="商品ID"),
    body: ProductUpdate = ...,
):
    """更新商品信息"""
    product = _products_db.get(product_id)
    if not product:
        raise NotFoundError(resource="商品", resource_id=product_id)

    if body.status and body.status not in VALID_PRODUCT_STATUSES:
        raise ValidationError(
            message=f"无效的商品状态: {body.status}",
            detail=f"支持的状态: {', '.join(VALID_PRODUCT_STATUSES)}",
        )

    update_data = body.model_dump(exclude_unset=True)
    product.update(update_data)
    product["updated_at"] = datetime.now().isoformat()

    # 重新计算利润率
    if product.get("cost_price") and product["cost_price"] > 0:
        product["margin_rate"] = round(
            (product["price"] - product["cost_price"]) / product["price"] * 100, 2
        )

    return success_response(data=product, message="商品更新成功")


@router.delete("/{product_id}")
async def delete_product(product_id: str = Path(..., description="商品ID")):
    """删除商品"""
    product = _products_db.get(product_id)
    if not product:
        raise NotFoundError(resource="商品", resource_id=product_id)

    del _products_db[product_id]
    return success_response(message=f"商品 {product_id} 已删除")
