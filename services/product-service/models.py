"""
商品管理数据模型
使用 SQLAlchemy + SQLite 实现持久化存储
支持：商品、分类、客户、订单、库存变动日志
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Float, Text, Boolean,
    DateTime, ForeignKey, create_engine, Index, CheckConstraint,
    UniqueConstraint, event
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, validates

Base = declarative_base()


class TimestampMixin:
    """时间戳混入类 - 统一时间字段"""
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间")


class SoftDeleteMixin:
    """软删除混入类"""
    is_deleted = Column(Boolean, default=False, nullable=False, comment="是否已删除")
    deleted_at = Column(DateTime, nullable=True, comment="删除时间")


class Category(TimestampMixin, Base):
    """商品分类模型"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, comment="分类名称")
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True, comment="父分类ID")
    sort_order = Column(Integer, default=0, comment="排序序号")
    is_active = Column(Boolean, default=True, comment="是否启用")
    level = Column(Integer, default=0, comment="分类层级")
    path = Column(String(500), default="", comment="分类路径，如: /1/5/12")

    # 关系
    parent = relationship("Category", remote_side=[id], backref="children")
    products = relationship("Product", back_populates="category_ref")

    # 索引
    __table_args__ = (
        Index("idx_categories_parent", "parent_id"),
        Index("idx_categories_active_sort", "is_active", "sort_order"),
        CheckConstraint("sort_order >= 0", name="ck_categories_sort_order"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "parent_id": self.parent_id,
            "sort_order": self.sort_order,
            "is_active": self.is_active,
            "level": self.level,
            "path": self.path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Product(TimestampMixin, SoftDeleteMixin, Base):
    """商品模型"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment="商品名称")
    sku = Column(String(50), nullable=False, unique=True, comment="SKU编码")
    platform = Column(String(20), nullable=False, comment="所属平台: douyin/pdd/xianyu/kuaishou")
    platform_name = Column(String(20), nullable=False, comment="平台中文名")
    category = Column(String(100), nullable=False, comment="商品分类")
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, comment="分类ID")
    price = Column(Float, nullable=False, comment="售价")
    cost = Column(Float, default=0, comment="成本价")
    profit = Column(Float, default=0, comment="利润")
    margin = Column(Float, default=0, comment="利润率(%)")
    stock = Column(Integer, default=0, comment="库存数量")
    locked_stock = Column(Integer, default=0, comment="锁定库存")
    sales = Column(Integer, default=0, comment="累计销量")
    status = Column(String(20), default="active", comment="状态: active/draft/out_of_stock/disabled")
    status_label = Column(String(20), default="在售", comment="状态标签")
    image = Column(String(500), default="", comment="商品图片URL")
    description = Column(Text, default="", comment="商品描述")
    weight = Column(Float, nullable=True, comment="重量(kg)")
    min_stock_alert = Column(Integer, default=10, comment="最低库存预警值")

    # 关系
    category_ref = relationship("Category", back_populates="products")
    inventory_logs = relationship("InventoryLog", back_populates="product_ref", order_by="desc(InventoryLog.created_at)")

    # 索引和约束
    __table_args__ = (
        Index("idx_products_platform_status", "platform", "status"),
        Index("idx_products_category_status", "category_id", "status"),
        Index("idx_products_platform_category", "platform", "category"),
        Index("idx_products_status_stock", "status", "stock"),
        Index("idx_products_created_at", "created_at"),
        Index("idx_products_sku", "sku"),
        CheckConstraint("price >= 0", name="ck_products_price_positive"),
        CheckConstraint("cost >= 0", name="ck_products_cost_positive"),
        CheckConstraint("stock >= 0", name="ck_products_stock_positive"),
        CheckConstraint("locked_stock >= 0", name="ck_products_locked_stock_positive"),
        CheckConstraint("sales >= 0", name="ck_products_sales_positive"),
    )

    @validates('price')
    def validate_price(self, key, price):
        if price < 0:
            raise ValueError("价格不能为负数")
        return price

    @validates('stock')
    def validate_stock(self, key, stock):
        if stock < 0:
            raise ValueError("库存不能为负数")
        return stock

    @validates('platform')
    def validate_platform(self, key, platform):
        valid_platforms = ['douyin', 'pdd', 'xianyu', 'kuaishou']
        if platform not in valid_platforms:
            raise ValueError(f"无效平台: {platform}，有效值: {valid_platforms}")
        return platform

    def to_dict(self):
        # 状态映射
        status_map = {
            "active": {"label": "在售", "color": "green"},
            "draft": {"label": "草稿", "color": "default"},
            "out_of_stock": {"label": "缺货", "color": "red"},
            "disabled": {"label": "已下架", "color": "default"},
        }
        platform_map = {
            "douyin": {"name": "抖音", "color": "#165DFF"},
            "pdd": {"name": "拼多多", "color": "#F53F3F"},
            "xianyu": {"name": "闲鱼", "color": "#FF7D00"},
            "kuaishou": {"name": "快手", "color": "#722ED1"},
        }
        s = status_map.get(self.status, status_map["draft"])
        p = platform_map.get(self.platform, {"name": self.platform, "color": "#86909C"})

        return {
            "id": f"SP{str(self.id).zfill(6)}",
            "db_id": self.id,
            "name": self.name,
            "sku": self.sku,
            "platform": self.platform,
            "platformName": p["name"],
            "platformColor": p["color"],
            "category": self.category,
            "categoryId": self.category_id,
            "price": self.price,
            "cost": self.cost,
            "profit": round(self.price - self.cost, 2),
            "margin": f"{((self.price - self.cost) / self.price * 100):.1f}" if self.price > 0 else "0.0",
            "stock": self.stock,
            "lockedStock": self.locked_stock,
            "availableStock": self.stock - self.locked_stock,
            "sales": self.sales,
            "status": self.status,
            "statusLabel": s["label"],
            "statusColor": s["color"],
            "image": self.image,
            "description": self.description,
            "weight": self.weight,
            "minStockAlert": self.min_stock_alert,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


class Customer(TimestampMixin, SoftDeleteMixin, Base):
    """客户模型"""
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="客户姓名")
    phone = Column(String(20), nullable=True, comment="手机号")
    email = Column(String(200), nullable=True, comment="邮箱")
    gender = Column(String(10), nullable=True, comment="性别: 男/女")
    level = Column(String(20), default="普通", comment="客户等级: 普通/银卡/金卡/钻石")
    tags = Column(Text, default="[]", comment="标签JSON数组")
    avatar = Column(String(500), default="", comment="头像URL")
    address = Column(String(500), default="", comment="地址")
    province = Column(String(50), nullable=True, comment="省份")
    city = Column(String(50), nullable=True, comment="城市")
    total_spent = Column(Float, default=0, comment="累计消费")
    order_count = Column(Integer, default=0, comment="订单数")
    last_order_time = Column(String(30), default="", comment="最近下单时间")
    points = Column(Integer, default=0, comment="积分")
    balance = Column(Float, default=0, comment="账户余额")
    remark = Column(Text, default="", comment="备注")

    __table_args__ = (
        Index("idx_customers_phone", "phone"),
        Index("idx_customers_level", "level"),
        Index("idx_customers_name", "name"),
        Index("idx_customers_province_city", "province", "city"),
        Index("idx_customers_created_at", "created_at"),
        CheckConstraint("total_spent >= 0", name="ck_customers_total_spent"),
        CheckConstraint("order_count >= 0", name="ck_customers_order_count"),
        CheckConstraint("points >= 0", name="ck_customers_points"),
    )

    @validates('level')
    def validate_level(self, key, level):
        valid_levels = ['普通', '银卡', '金卡', '钻石']
        if level not in valid_levels:
            raise ValueError(f"无效客户等级: {level}，有效值: {valid_levels}")
        return level

    def to_dict(self):
        import json
        level_map = {
            "普通": {"color": "#8c8c8c"},
            "银卡": {"color": "#bfbfbf"},
            "金卡": {"color": "#faad14"},
            "钻石": {"color": "#722ed1"},
        }
        lv = level_map.get(self.level, level_map["普通"])

        tags_list = []
        try:
            tags_list = json.loads(self.tags) if self.tags else []
        except Exception:
            tags_list = []

        return {
            "id": f"C{str(self.id).zfill(6)}",
            "db_id": self.id,
            "name": self.name,
            "phone": self.phone or "",
            "email": self.email or "",
            "gender": self.gender or "",
            "level": self.level,
            "levelColor": lv["color"],
            "tags": tags_list,
            "avatar": self.avatar or f"https://api.dicebear.com/7.x/avataaars/svg?seed={self.id}",
            "address": self.address or "",
            "province": self.province or "",
            "city": self.city or "",
            "totalSpent": self.total_spent or 0,
            "orderCount": self.order_count or 0,
            "lastOrderTime": self.last_order_time or "-",
            "points": self.points or 0,
            "balance": self.balance or 0,
            "remark": self.remark or "",
            "registerTime": self.created_at.strftime("%Y-%m-%d") if self.created_at else "",
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


class InventoryLog(TimestampMixin, Base):
    """库存变动日志"""
    __tablename__ = "inventory_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, comment="商品ID")
    change_type = Column(String(20), nullable=False, comment="变动类型: sale/restock/adjust/lock/unlock")
    quantity = Column(Integer, nullable=False, comment="变动数量(正数增加，负数减少)")
    before_stock = Column(Integer, nullable=False, comment="变动前库存")
    after_stock = Column(Integer, nullable=False, comment="变动后库存")
    order_id = Column(String(50), nullable=True, comment="关联订单ID")
    operator = Column(String(50), default="system", comment="操作人")
    remark = Column(String(500), default="", comment="备注")

    # 关系
    product_ref = relationship("Product", back_populates="inventory_logs")

    __table_args__ = (
        Index("idx_inventory_logs_product", "product_id"),
        Index("idx_inventory_logs_created_at", "created_at"),
        Index("idx_inventory_logs_change_type", "change_type"),
        CheckConstraint("after_stock >= 0", name="ck_inventory_logs_after_stock"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "productId": self.product_id,
            "changeType": self.change_type,
            "quantity": self.quantity,
            "beforeStock": self.before_stock,
            "afterStock": self.after_stock,
            "orderId": self.order_id,
            "operator": self.operator,
            "remark": self.remark,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }


# 数据库初始化
DATABASE_URL = "sqlite:///./data/product_service.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# SQLite 外键支持
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def init_database():
    """创建所有表"""
    import os
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
