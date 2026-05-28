"""
商品管理数据模型
使用 SQLAlchemy + SQLite 实现持久化存储
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Float, Text, Boolean,
    DateTime, ForeignKey, create_engine, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


class Category(Base):
    """商品分类模型"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, comment="分类名称")
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True, comment="父分类ID")
    sort_order = Column(Integer, default=0, comment="排序序号")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    parent = relationship("Category", remote_side=[id], backref="children")
    products = relationship("Product", back_populates="category_ref")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "parent_id": self.parent_id,
            "sort_order": self.sort_order,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Product(Base):
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
    sales = Column(Integer, default=0, comment="累计销量")
    status = Column(String(20), default="active", comment="状态: active/draft/out_of_stock/disabled")
    status_label = Column(String(20), default="在售", comment="状态标签")
    image = Column(String(500), default="", comment="商品图片URL")
    description = Column(Text, default="", comment="商品描述")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    category_ref = relationship("Category", back_populates="products")

    # 索引
    __table_args__ = (
        Index("idx_products_platform", "platform"),
        Index("idx_products_category", "category"),
        Index("idx_products_status", "status"),
        Index("idx_products_sku", "sku"),
    )

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
            "price": self.price,
            "cost": self.cost,
            "profit": round(self.price - self.cost, 2),
            "margin": f"{((self.price - self.cost) / self.price * 100):.1f}" if self.price > 0 else "0.0",
            "stock": self.stock,
            "sales": self.sales,
            "status": self.status,
            "statusLabel": s["label"],
            "statusColor": s["color"],
            "image": self.image,
            "description": self.description,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


class Customer(Base):
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
    total_spent = Column(Float, default=0, comment="累计消费")
    order_count = Column(Integer, default=0, comment="订单数")
    last_order_time = Column(String(30), default="", comment="最近下单时间")
    points = Column(Integer, default=0, comment="积分")
    balance = Column(Float, default=0, comment="账户余额")
    created_at = Column(DateTime, default=datetime.now, comment="注册时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_customers_phone", "phone"),
        Index("idx_customers_level", "level"),
        Index("idx_customers_name", "name"),
    )

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
            "totalSpent": self.total_spent or 0,
            "orderCount": self.order_count or 0,
            "lastOrderTime": self.last_order_time or "-",
            "points": self.points or 0,
            "balance": self.balance or 0,
            "registerTime": self.created_at.strftime("%Y-%m-%d") if self.created_at else "",
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


# 数据库初始化
DATABASE_URL = "sqlite:///./data/product_service.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
