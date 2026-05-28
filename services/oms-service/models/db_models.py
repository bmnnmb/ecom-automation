from sqlalchemy import Column, String, Numeric, Integer, JSON, DateTime, Float, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from database import Base

class MultiPlatformSKUModel(Base):
    """
    多平台 SKU 数据库模型
    """
    __tablename__ = "multi_platform_skus"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id = Column(UUID(as_uuid=True), nullable=False)
    platform = Column(String(20), nullable=False)
    platform_sku_id = Column(String(128), nullable=False)
    platform_product_id = Column(String(128), nullable=False)
    outer_id = Column(String(128))
    sku_name = Column(String, nullable=False)
    price = Column(Numeric(12, 2))
    stock = Column(Integer, default=0)
    attributes = Column(JSON, default={})
    status = Column(String(20), default="online")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("platform", "platform_sku_id", name="multi_platform_skus_platform_platform_sku_id_key"),
    )


class OrderModel(Base):
    """
    订单数据库模型
    对应 Pydantic Order 模型，持久化到 PostgreSQL
    """
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(String(64), unique=True, nullable=False, index=True)
    platform = Column(String(20), nullable=False, index=True)
    platform_order_id = Column(String(128), nullable=False)
    status = Column(String(20), nullable=False, default="pending", index=True)
    payment_status = Column(String(20), default="unpaid")

    # 订单详情 (JSON 存储商品列表)
    items = Column(JSON, nullable=False, default=list)
    total_amount = Column(Float, nullable=False, default=0)
    discount_amount = Column(Float, default=0)
    actual_amount = Column(Float, nullable=False, default=0)

    # 客户/物流/支付信息 (JSON 存储)
    customer = Column(JSON, nullable=False)
    shipping = Column(JSON, nullable=True)
    payment = Column(JSON, nullable=True)

    # 时间字段
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    paid_at = Column(DateTime(timezone=True), nullable=True)
    shipped_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # 扩展字段
    remarks = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    risk_level = Column(String(20), default="low")
    metadata = Column(JSON, nullable=True)

    __table_args__ = (
        UniqueConstraint("platform", "platform_order_id", name="orders_platform_platform_order_id_key"),
    )
