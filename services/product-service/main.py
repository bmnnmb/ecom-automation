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

from models import Product, Category, Customer, init_database, get_db, engine, SessionLocal

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


class CustomerCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="客户姓名")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    email: Optional[str] = Field(None, max_length=200, description="邮箱")
    gender: Optional[str] = Field(None, description="性别: 男/女")
    level: Optional[str] = Field("普通", description="客户等级: 普通/银卡/金卡/钻石")
    tags: Optional[List[str]] = Field([], description="标签列表")
    avatar: Optional[str] = Field("", description="头像URL")
    address: Optional[str] = Field("", description="地址")
    total_spent: Optional[float] = Field(0, ge=0, description="累计消费")
    order_count: Optional[int] = Field(0, ge=0, description="订单数")
    last_order_time: Optional[str] = Field("-", description="最近下单时间")
    points: Optional[int] = Field(0, ge=0, description="积分")
    balance: Optional[float] = Field(0, ge=0, description="账户余额")


class CustomerUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=200)
    gender: Optional[str] = None
    level: Optional[str] = None
    tags: Optional[List[str]] = None
    avatar: Optional[str] = None
    address: Optional[str] = None
    total_spent: Optional[float] = Field(None, ge=0)
    order_count: Optional[int] = Field(None, ge=0)
    last_order_time: Optional[str] = None
    points: Optional[int] = Field(None, ge=0)
    balance: Optional[float] = Field(None, ge=0)


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


def seed_sample_customers(db: Session):
    """初始化示例客户数据（仅当表为空时）"""
    import json
    import random as rnd
    if db.query(Customer).count() > 0:
        return

    rnd.seed(123)
    surnames = ["张", "李", "王", "赵", "陈", "刘", "杨", "黄", "周", "吴", "孙", "马", "朱", "胡", "郭", "何", "林", "罗", "高", "郑"]
    given_names = ["伟", "芳", "娜", "敏", "静", "丽", "强", "磊", "军", "洋", "勇", "艳", "杰", "涛", "明", "超", "秀英", "华", "慧", "建华"]
    levels = ["普通", "银卡", "金卡", "钻石"]
    level_weights = [0.5, 0.25, 0.15, 0.1]
    tag_options = ["新客户", "活跃", "沉睡", "流失", "VIP", "高价值"]
    cities = ["北京市朝阳区", "上海市浦东新区", "广州市天河区", "深圳市南山区", "杭州市西湖区", "成都市锦江区", "南京市鼓楼区", "武汉市洪山区", "重庆市渝中区", "苏州市工业园区"]

    for i in range(1, 51):
        surname = rnd.choice(surnames)
        given = rnd.choice(given_names)
        name = surname + given
        gender = rnd.choice(["男", "女"])
        level = rnd.choices(levels, weights=level_weights, k=1)[0]
        phone = f"1{rnd.choice('3456789')}{rnd.randint(10000000, 99999999)}"
        email = f"customer{i}@example.com"
        total_spent = round(rnd.uniform(500, 50000), 2)
        order_count = rnd.randint(1, 60)
        points = rnd.randint(0, 10000)
        balance = round(rnd.uniform(0, 5000), 2)
        city = rnd.choice(cities)
        address = f"{city}某某街道{i}号"

        tags = []
        if rnd.random() > 0.5:
            tags.append(rnd.choice(["新客户", "活跃", "沉睡", "流失"]))
        if rnd.random() > 0.7:
            tags.append(rnd.choice(tag_options))
        if level in ("金卡", "钻石"):
            tags.append("VIP")
        if total_spent > 30000:
            tags.append("高价值")
        tags = list(set(tags))

        days_ago = rnd.randint(1, 365)
        from datetime import timedelta
        created = datetime.now() - timedelta(days=days_ago)
        last_order_days = rnd.randint(0, 30)
        last_order_time = (datetime.now() - timedelta(days=last_order_days)).strftime("%Y-%m-%d %H:%M")

        db.add(Customer(
            name=name,
            phone=phone,
            email=email,
            gender=gender,
            level=level,
            tags=json.dumps(tags, ensure_ascii=False),
            avatar=f"https://api.dicebear.com/7.x/avataaars/svg?seed={i}",
            address=address,
            total_spent=total_spent,
            order_count=order_count,
            last_order_time=last_order_time,
            points=points,
            balance=balance,
            created_at=created,
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
        seed_sample_customers(db)
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
# 客户 CRUD 路由
# ============================================================

@app.get("/api/customers/stats")
async def get_customer_stats(db: Session = Depends(get_db)):
    """获取客户统计数据"""
    import json
    total = db.query(Customer).count()
    # 新增：30天内注册
    from datetime import timedelta
    thirty_days_ago = datetime.now() - timedelta(days=30)
    new_customers = db.query(Customer).filter(Customer.created_at >= thirty_days_ago).count()
    # 活跃：30天内有订单
    active_customers = db.query(Customer).filter(
        Customer.last_order_time != "",
        Customer.last_order_time != "-",
    ).count()
    # VIP: 金卡/钻石
    vip_customers = db.query(Customer).filter(
        Customer.level.in_(["金卡", "钻石"])
    ).count()

    return {
        "success": True,
        "data": {
            "total": total,
            "newCustomers": new_customers,
            "activeCustomers": active_customers,
            "vipCustomers": vip_customers,
        },
    }


@app.get("/api/customers")
async def list_customers(
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    level: Optional[str] = Query(None, description="客户等级筛选"),
    tag: Optional[str] = Query(None, description="标签筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    """获取客户列表（支持搜索、筛选、分页）"""
    query = db.query(Customer)

    if keyword:
        kw = f"%{keyword}%"
        query = query.filter(
            or_(
                Customer.name.ilike(kw),
                Customer.phone.ilike(kw),
                Customer.email.ilike(kw),
            )
        )
    if level and level != "all":
        query = query.filter(Customer.level == level)
    if tag and tag != "all":
        query = query.filter(Customer.tags.ilike(f"%{tag}%"))

    total = query.count()
    items = query.order_by(Customer.id.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "success": True,
        "data": [c.to_dict() for c in items],
        "meta": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        },
    }


@app.get("/api/customers/{customer_id}")
async def get_customer(
    customer_id: int = Path(..., description="客户ID"),
    db: Session = Depends(get_db),
):
    """获取客户详情"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"客户 {customer_id} 不存在")
    return {"success": True, "data": customer.to_dict()}


@app.post("/api/customers")
async def create_customer(
    body: CustomerCreateRequest,
    db: Session = Depends(get_db),
):
    """创建客户"""
    import json
    customer = Customer(
        name=body.name,
        phone=body.phone,
        email=body.email,
        gender=body.gender,
        level=body.level or "普通",
        tags=json.dumps(body.tags or [], ensure_ascii=False),
        avatar=body.avatar or "",
        address=body.address or "",
        total_spent=body.total_spent or 0,
        order_count=body.order_count or 0,
        last_order_time=body.last_order_time or "-",
        points=body.points or 0,
        balance=body.balance or 0,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return {"success": True, "data": customer.to_dict(), "message": "客户创建成功"}


@app.patch("/api/customers/{customer_id}")
async def update_customer(
    customer_id: int = Path(..., description="客户ID"),
    body: CustomerUpdateRequest = ...,
    db: Session = Depends(get_db),
):
    """更新客户"""
    import json
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"客户 {customer_id} 不存在")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "tags" and isinstance(value, list):
            setattr(customer, key, json.dumps(value, ensure_ascii=False))
        else:
            setattr(customer, key, value)

    customer.updated_at = datetime.now()
    db.commit()
    db.refresh(customer)
    return {"success": True, "data": customer.to_dict(), "message": "客户信息更新成功"}


@app.delete("/api/customers/{customer_id}")
async def delete_customer(
    customer_id: int = Path(..., description="客户ID"),
    db: Session = Depends(get_db),
):
    """删除客户"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"客户 {customer_id} 不存在")

    db.delete(customer)
    db.commit()
    return {"success": True, "message": f"客户 {customer_id} 已删除"}


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
