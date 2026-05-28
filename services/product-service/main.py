"""
商品管理服务 - CRUD API
独立微服务，端口 8006
提供商品和分类的完整增删改查功能
"""
import os
import sys
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Path, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
import uvicorn

# 确保导入路径正确
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Product, Category, init_database, get_db, engine, SessionLocal

# ============================================================
# Pydantic 请求/响应模型
# ============================================================

class ProductCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="商品名称")
    sku: str = Field(..., min_length=1, max_length=50, description="SKU编码")
    platform: str = Field(..., description="所属平台: douyin/pdd/xianyu/kuaishou")
    category: str = Field(..., description="商品分类")
    price: float = Field(..., gt=0, description="售价")
    cost: float = Field(0, ge=0, description="成本价")
    stock: int = Field(0, ge=0, description="库存数量")
    image: Optional[str] = Field("", description="商品图片URL")
    description: Optional[str] = Field("", description="商品描述")
    status: Optional[str] = Field("active", description="商品状态")


class ProductUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    sku: Optional[str] = Field(None, min_length=1, max_length=50)
    platform: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    cost: Optional[float] = Field(None, ge=0)
    stock: Optional[int] = Field(None, ge=0)
    image: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    sales: Optional[int] = Field(None, ge=0)


class CategoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="分类名称")
    parent_id: Optional[int] = Field(None, description="父分类ID")
    sort_order: int = Field(0, description="排序序号")


class BatchPriceAdjustRequest(BaseModel):
    product_ids: List[int] = Field(..., min_items=1, description="商品ID列表")
    adjust_type: str = Field(..., description="调整方式: increase_pct/decrease_pct/increase_amt/decrease_amt")
    adjust_value: float = Field(..., gt=0, description="调整数值")


class BatchActionRequest(BaseModel):
    product_ids: List[int] = Field(..., min_items=1, description="商品ID列表")
    action: str = Field(..., description="操作: delete/disable")


# 平台映射
PLATFORM_MAP = {
    "douyin": "抖音",
    "pdd": "拼多多",
    "xianyu": "闲鱼",
    "kuaishou": "快手",
}

VALID_STATUSES = {"active", "draft", "out_of_stock", "disabled"}
STATUS_LABELS = {
    "active": "在售",
    "draft": "草稿",
    "out_of_stock": "缺货",
    "disabled": "已下架",
}


# ============================================================
# 种子数据
# ============================================================

def seed_default_categories(db: Session):
    """初始化默认分类"""
    if db.query(Category).count() > 0:
        return
    defaults = ["数码配件", "家居日用", "服饰鞋包", "美妆个护", "食品生鲜", "办公用品"]
    for i, name in enumerate(defaults):
        db.add(Category(name=name, sort_order=i))
    db.commit()


def seed_sample_products(db: Session):
    """初始化示例商品数据（仅当表为空时）"""
    if db.query(Product).count() > 0:
        return

    import random
    random.seed(42)

    platforms = ["douyin", "pdd", "xianyu", "kuaishou"]
    categories = ["数码配件", "家居日用", "服饰鞋包", "美妆个护", "食品生鲜", "办公用品"]
    product_names = {
        "数码配件": ["Type-C数据线", "无线充电器", "蓝牙耳机", "手机壳", "充电宝", "USB集线器"],
        "家居日用": ["创意台灯", "收纳盒", "保温杯", "桌面摆件", "置物架", "香薰蜡烛"],
        "服饰鞋包": ["纯棉T恤", "休闲帆布包", "运动袜", "棒球帽", "围巾", "皮带"],
        "美妆个护": ["面膜套装", "洗面奶", "护手霜", "口红", "眼影盘", "防晒霜"],
        "食品生鲜": ["坚果礼盒", "牛肉干", "水果干", "蜂蜜", "茶叶", "咖啡豆"],
        "办公用品": ["笔记本", "签字笔", "文件夹", "便签纸", "计算器", "订书机"],
    }

    for i in range(1, 51):
        cat = random.choice(categories)
        plat = random.choice(platforms)
        price = round(random.uniform(15, 500), 2)
        cost = round(price * random.uniform(0.3, 0.7), 2)
        stock = random.randint(0, 200)
        sales = random.randint(0, 1000)
        names = product_names.get(cat, [f"{cat}商品"])
        name = f"{random.choice(names)}{i:03d}"

        status = "active"
        status_label = "在售"
        if stock == 0:
            status = "out_of_stock"
            status_label = "缺货"
        elif stock < 20:
            status = "active"
            status_label = "在售"

        db.add(Product(
            name=name,
            sku=f"SKU{i:04d}",
            platform=plat,
            platform_name=PLATFORM_MAP[plat],
            category=cat,
            price=price,
            cost=cost,
            stock=stock,
            sales=sales,
            status=status,
            status_label=status_label,
            image=f"https://picsum.photos/seed/{i}/80/80",
            description=f"{name}的详细描述",
        ))
    db.commit()


# ============================================================
# FastAPI 应用
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    init_database()
    db = SessionLocal()
    try:
        seed_default_categories(db)
        seed_sample_products(db)
    finally:
        db.close()
    print("✅ 商品服务启动完成，数据库已初始化")
    yield
    print("🛑 商品服务关闭")


app = FastAPI(
    title="商品管理服务",
    description="商品CRUD API - 独立微服务",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# 商品 CRUD 路由
# ============================================================

@app.get("/api/products")
async def list_products(
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    platform: Optional[str] = Query(None, description="平台筛选"),
    category: Optional[str] = Query(None, description="分类筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    """获取商品列表（支持筛选、搜索、分页）"""
    query = db.query(Product)

    if keyword:
        kw = f"%{keyword}%"
        query = query.filter(or_(Product.name.ilike(kw), Product.sku.ilike(kw)))
    if platform and platform != "all":
        query = query.filter(Product.platform == platform)
    if category and category != "all":
        query = query.filter(Product.category == category)
    if status and status != "all":
        query = query.filter(Product.status == status)

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "success": True,
        "data": [p.to_dict() for p in items],
        "meta": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        },
    }


@app.get("/api/products/stats")
async def get_product_stats(db: Session = Depends(get_db)):
    """获取商品统计数据"""
    total = db.query(Product).count()
    active = db.query(Product).filter(Product.status == "active").count()
    low_stock = db.query(Product).filter(Product.stock < 20, Product.stock > 0).count()
    out_of_stock = db.query(Product).filter(Product.stock == 0).count()
    total_value = db.query(func.sum(Product.price * Product.stock)).scalar() or 0

    return {
        "success": True,
        "data": {
            "total": total,
            "active": active,
            "lowStock": low_stock,
            "outOfStock": out_of_stock,
            "totalValue": round(total_value, 2),
        },
    }


@app.get("/api/products/{product_id}")
async def get_product(
    product_id: int = Path(..., description="商品ID"),
    db: Session = Depends(get_db),
):
    """获取商品详情"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"商品 {product_id} 不存在")
    return {"success": True, "data": product.to_dict()}


@app.post("/api/products")
async def create_product(
    body: ProductCreateRequest,
    db: Session = Depends(get_db),
):
    """创建商品"""
    # 检查SKU唯一性
    existing = db.query(Product).filter(Product.sku == body.sku).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"SKU '{body.sku}' 已存在")

    platform_name = PLATFORM_MAP.get(body.platform, body.platform)
    status = body.status or "active"
    status_label = STATUS_LABELS.get(status, "在售")

    product = Product(
        name=body.name,
        sku=body.sku,
        platform=body.platform,
        platform_name=platform_name,
        category=body.category,
        price=body.price,
        cost=body.cost,
        stock=body.stock,
        status=status,
        status_label=status_label,
        image=body.image or "",
        description=body.description or "",
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    return {"success": True, "data": product.to_dict(), "message": "商品创建成功"}


@app.patch("/api/products/{product_id}")
async def update_product(
    product_id: int = Path(..., description="商品ID"),
    body: ProductUpdateRequest = ...,
    db: Session = Depends(get_db),
):
    """更新商品"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"商品 {product_id} 不存在")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "platform" and value:
            setattr(product, "platform_name", PLATFORM_MAP.get(value, value))
        if key == "status" and value:
            setattr(product, "status_label", STATUS_LABELS.get(value, value))
        setattr(product, key, value)

    product.updated_at = datetime.now()
    db.commit()
    db.refresh(product)

    return {"success": True, "data": product.to_dict(), "message": "商品更新成功"}


@app.delete("/api/products/{product_id}")
async def delete_product(
    product_id: int = Path(..., description="商品ID"),
    db: Session = Depends(get_db),
):
    """删除商品"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"商品 {product_id} 不存在")

    db.delete(product)
    db.commit()
    return {"success": True, "message": f"商品 {product_id} 已删除"}


# ============================================================
# 批量操作
# ============================================================

@app.post("/api/products/batch/delete")
async def batch_delete_products(
    body: BatchActionRequest,
    db: Session = Depends(get_db),
):
    """批量删除商品"""
    count = db.query(Product).filter(Product.id.in_(body.product_ids)).delete(synchronize_session=False)
    db.commit()
    return {"success": True, "message": f"已删除 {count} 个商品"}


@app.post("/api/products/batch/disable")
async def batch_disable_products(
    body: BatchActionRequest,
    db: Session = Depends(get_db),
):
    """批量下架商品"""
    count = db.query(Product).filter(Product.id.in_(body.product_ids)).update(
        {"status": "disabled", "status_label": "已下架", "updated_at": datetime.now()},
        synchronize_session=False,
    )
    db.commit()
    return {"success": True, "message": f"已下架 {count} 个商品"}


@app.post("/api/products/batch/price")
async def batch_adjust_price(
    body: BatchPriceAdjustRequest,
    db: Session = Depends(get_db),
):
    """批量调价"""
    products = db.query(Product).filter(Product.id.in_(body.product_ids)).all()
    updated = 0

    for p in products:
        if body.adjust_type == "increase_pct":
            p.price = round(p.price * (1 + body.adjust_value / 100), 2)
        elif body.adjust_type == "decrease_pct":
            p.price = round(p.price * (1 - body.adjust_value / 100), 2)
        elif body.adjust_type == "increase_amt":
            p.price = round(p.price + body.adjust_value, 2)
        elif body.adjust_type == "decrease_amt":
            p.price = round(max(p.price - body.adjust_value, 0), 2)

        if p.price > 0 and p.cost > 0:
            p.margin = round((p.price - p.cost) / p.price * 100, 2)
        p.updated_at = datetime.now()
        updated += 1

    db.commit()
    return {"success": True, "message": f"已调整 {updated} 个商品的价格"}


# ============================================================
# 分类 CRUD 路由
# ============================================================

@app.get("/api/categories")
async def list_categories(db: Session = Depends(get_db)):
    """获取所有分类"""
    cats = db.query(Category).filter(Category.is_active == True).order_by(Category.sort_order).all()
    return {"success": True, "data": [c.to_dict() for c in cats]}


@app.post("/api/categories")
async def create_category(
    body: CategoryCreateRequest,
    db: Session = Depends(get_db),
):
    """创建分类"""
    existing = db.query(Category).filter(Category.name == body.name).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"分类 '{body.name}' 已存在")

    cat = Category(name=body.name, parent_id=body.parent_id, sort_order=body.sort_order)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return {"success": True, "data": cat.to_dict(), "message": "分类创建成功"}


@app.delete("/api/categories/{category_id}")
async def delete_category(
    category_id: int = Path(..., description="分类ID"),
    db: Session = Depends(get_db),
):
    """删除分类"""
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail=f"分类 {category_id} 不存在")

    cat.is_active = False
    db.commit()
    return {"success": True, "message": f"分类 '{cat.name}' 已禁用"}


# ============================================================
# 健康检查
# ============================================================

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "product-service", "version": "1.0.0"}


@app.get("/")
async def root():
    return {"service": "product-service", "version": "1.0.0", "status": "running"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8006)
