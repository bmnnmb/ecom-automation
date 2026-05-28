"""
Legacy DB models — SQLite-compatible (UUID→String).
MultiPlatformSKUModel is still used by sku_repository.
"""
from sqlalchemy import Column, String, Numeric, Integer, JSON, DateTime, Float, Text, UniqueConstraint
from datetime import datetime
from database import Base


class MultiPlatformSKUModel(Base):
    """多平台 SKU 数据库模型"""
    __tablename__ = "multi_platform_skus"

    id = Column(String(36), primary_key=True)
    shop_id = Column(String(36), nullable=False)
    platform = Column(String(20), nullable=False)
    platform_sku_id = Column(String(128), nullable=False)
    platform_product_id = Column(String(128), nullable=False)
    outer_id = Column(String(128))
    sku_name = Column(String, nullable=False)
    price = Column(Numeric(12, 2))
    stock = Column(Integer, default=0)
    attributes = Column(JSON, default=dict)
    status = Column(String(20), default="online")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        UniqueConstraint("platform", "platform_sku_id", name="uq_sku_platform"),
    )


class LegacyOrderModel(Base):
    """旧订单模型 (保留兼容, 表名避免与 order_db_models.OrderRecord 冲突)"""
    __tablename__ = "legacy_orders"

    id = Column(String(36), primary_key=True)
    order_id = Column(String(64), unique=True, nullable=False, index=True)
    platform = Column(String(20), nullable=False, index=True)
    platform_order_id = Column(String(128), nullable=False)
    status = Column(String(20), nullable=False, default="pending", index=True)
    payment_status = Column(String(20), default="unpaid")
    items = Column(JSON, nullable=False, default=list)
    total_amount = Column(Float, nullable=False, default=0)
    discount_amount = Column(Float, default=0)
    actual_amount = Column(Float, nullable=False, default=0)
    customer = Column(JSON, nullable=True)
    shipping = Column(JSON, nullable=True)
    payment = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    paid_at = Column(DateTime, nullable=True)
    shipped_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    remarks = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    risk_level = Column(String(20), default="low")
    metadata_json = Column(JSON, nullable=True)

    __table_args__ = (
        UniqueConstraint("platform", "platform_order_id", name="uq_legacy_order_platform"),
    )
