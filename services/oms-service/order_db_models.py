"""
订单数据库模型 (SQLite 兼容)
使用 String 代替 Enum，保证 SQLite 兼容性。
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON
from database import Base


class OrderRecord(Base):
    """订单持久化表"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(50), nullable=False, unique=True, index=True)
    platform = Column(String(20), nullable=False, index=True)
    platform_order_id = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="pending", index=True)
    payment_status = Column(String(20), default="unpaid")

    # 金额
    total_amount = Column(Float, nullable=False, default=0)
    discount_amount = Column(Float, default=0)
    actual_amount = Column(Float, nullable=False, default=0)

    # 客户信息 (JSON)
    customer = Column(JSON, nullable=True)
    # 物流信息 (JSON)
    shipping = Column(JSON, nullable=True)
    # 支付信息 (JSON)
    payment = Column(JSON, nullable=True)
    # 商品列表 (JSON)
    items = Column(JSON, nullable=False, default=list)

    # 时间
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    paid_at = Column(DateTime, nullable=True)
    shipped_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # 扩展
    remarks = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    risk_level = Column(String(20), default="low")
