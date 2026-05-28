"""
OMS服务 SQLAlchemy ORM模型
订单管理系统数据库模型定义
"""
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, Integer, String, Float, Text, Boolean,
    DateTime, ForeignKey, Index, CheckConstraint,
    Enum, JSON, event
)
from sqlalchemy.orm import relationship, validates
from database import Base


class PlatformEnum(str, PyEnum):
    """电商平台枚举"""
    DOUYIN = "douyin"
    KUAISHOU = "kuaishou"
    PINDUODUO = "pinduoduo"
    XIANYU = "xianyu"


class OrderStatusEnum(str, PyEnum):
    """订单状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDING = "refunding"
    REFUNDED = "refunded"


class PaymentStatusEnum(str, PyEnum):
    """支付状态枚举"""
    UNPAID = "unpaid"
    PAID = "paid"
    PARTIAL_REFUND = "partial_refund"
    FULL_REFUND = "full_refund"


class TicketStatusEnum(str, PyEnum):
    """工单状态枚举"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketTypeEnum(str, PyEnum):
    """工单类型枚举"""
    REFUND = "refund"
    EXCHANGE = "exchange"
    RETURN = "return"
    COMPLAINT = "complaint"
    INQUIRY = "inquiry"


class RiskLevelEnum(str, PyEnum):
    """风险等级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TimestampMixin:
    """时间戳混入"""
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间")


class Order(TimestampMixin, Base):
    """订单模型"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(50), nullable=False, unique=True, comment="订单ID")
    platform = Column(Enum(PlatformEnum), nullable=False, comment="来源平台")
    platform_order_id = Column(String(100), nullable=False, comment="平台订单号")
    status = Column(Enum(OrderStatusEnum), default=OrderStatusEnum.PENDING, comment="订单状态")
    payment_status = Column(Enum(PaymentStatusEnum), default=PaymentStatusEnum.UNPAID, comment="支付状态")

    # 订单金额
    total_amount = Column(Float, nullable=False, comment="订单总金额")
    discount_amount = Column(Float, default=0, comment="优惠金额")
    actual_amount = Column(Float, nullable=False, comment="实付金额")
    shipping_fee = Column(Float, default=0, comment="运费")

    # 客户信息
    customer_id = Column(String(50), nullable=True, comment="客户ID")
    customer_name = Column(String(100), nullable=True, comment="客户姓名")
    customer_phone = Column(String(20), nullable=True, comment="客户电话")
    customer_address = Column(Text, nullable=True, comment="收货地址")
    platform_uid = Column(String(100), nullable=True, comment="平台用户ID")

    # 物流信息
    carrier = Column(String(50), nullable=True, comment="承运商")
    tracking_number = Column(String(100), nullable=True, comment="运单号")
    shipping_method = Column(String(50), default="standard", comment="配送方式")

    # 时间信息
    paid_at = Column(DateTime, nullable=True, comment="支付时间")
    shipped_at = Column(DateTime, nullable=True, comment="发货时间")
    delivered_at = Column(DateTime, nullable=True, comment="送达时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    cancelled_at = Column(DateTime, nullable=True, comment="取消时间")

    # 扩展字段
    remarks = Column(Text, nullable=True, comment="备注")
    buyer_message = Column(Text, nullable=True, comment="买家留言")
    tags = Column(JSON, default=list, comment="标签")
    risk_level = Column(Enum(RiskLevelEnum), default=RiskLevelEnum.LOW, comment="风险等级")
    metadata_json = Column(JSON, nullable=True, comment="元数据")

    # 关系
    items = relationship("OrderItem", back_populates="order_ref", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="order_ref")

    __table_args__ = (
        Index("idx_orders_platform", "platform"),
        Index("idx_orders_status", "status"),
        Index("idx_orders_payment_status", "payment_status"),
        Index("idx_orders_platform_order_id", "platform_order_id"),
        Index("idx_orders_customer_id", "customer_id"),
        Index("idx_orders_created_at", "created_at"),
        Index("idx_orders_platform_status", "platform", "status"),
        Index("idx_orders_tracking_number", "tracking_number"),
        CheckConstraint("total_amount >= 0", name="ck_orders_total_amount"),
        CheckConstraint("actual_amount >= 0", name="ck_orders_actual_amount"),
    )

    @validates('actual_amount')
    def validate_amount(self, key, amount):
        if amount < 0:
            raise ValueError("实付金额不能为负数")
        return amount

    def to_dict(self):
        return {
            "id": self.id,
            "orderId": self.order_id,
            "platform": self.platform.value if self.platform else None,
            "platformOrderId": self.platform_order_id,
            "status": self.status.value if self.status else None,
            "paymentStatus": self.payment_status.value if self.payment_status else None,
            "totalAmount": self.total_amount,
            "discountAmount": self.discount_amount,
            "actualAmount": self.actual_amount,
            "shippingFee": self.shipping_fee,
            "customerId": self.customer_id,
            "customerName": self.customer_name,
            "customerPhone": self.customer_phone,
            "customerAddress": self.customer_address,
            "carrier": self.carrier,
            "trackingNumber": self.tracking_number,
            "shippingMethod": self.shipping_method,
            "paidAt": self.paid_at.isoformat() if self.paid_at else None,
            "shippedAt": self.shipped_at.isoformat() if self.shipped_at else None,
            "deliveredAt": self.delivered_at.isoformat() if self.delivered_at else None,
            "completedAt": self.completed_at.isoformat() if self.completed_at else None,
            "cancelledAt": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "remarks": self.remarks,
            "buyerMessage": self.buyer_message,
            "tags": self.tags or [],
            "riskLevel": self.risk_level.value if self.risk_level else None,
            "items": [item.to_dict() for item in self.items] if self.items else [],
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


class OrderItem(TimestampMixin, Base):
    """订单商品项"""
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, comment="订单ID")
    sku_id = Column(String(50), nullable=False, comment="SKU ID")
    product_name = Column(String(200), nullable=False, comment="商品名称")
    quantity = Column(Integer, nullable=False, comment="数量")
    unit_price = Column(Float, nullable=False, comment="单价")
    total_price = Column(Float, nullable=False, comment="总价")
    specifications = Column(JSON, nullable=True, comment="规格参数")

    # 关系
    order_ref = relationship("Order", back_populates="items")

    __table_args__ = (
        Index("idx_order_items_order_id", "order_id"),
        Index("idx_order_items_sku_id", "sku_id"),
        CheckConstraint("quantity > 0", name="ck_order_items_quantity"),
        CheckConstraint("unit_price >= 0", name="ck_order_items_unit_price"),
        CheckConstraint("total_price >= 0", name="ck_order_items_total_price"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "skuId": self.sku_id,
            "productName": self.product_name,
            "quantity": self.quantity,
            "unitPrice": self.unit_price,
            "totalPrice": self.total_price,
            "specifications": self.specifications,
        }


class Ticket(TimestampMixin, Base):
    """工单模型"""
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(String(50), nullable=False, unique=True, comment="工单ID")
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, comment="关联订单ID")
    platform = Column(Enum(PlatformEnum), nullable=False, comment="来源平台")

    # 工单详情
    ticket_type = Column(Enum(TicketTypeEnum), nullable=False, comment="工单类型")
    status = Column(Enum(TicketStatusEnum), default=TicketStatusEnum.OPEN, comment="工单状态")
    priority = Column(Integer, default=3, comment="优先级(1-5)")

    # 问题描述
    title = Column(String(200), nullable=False, comment="工单标题")
    description = Column(Text, nullable=False, comment="问题描述")
    customer_complaint = Column(Text, nullable=True, comment="客户投诉内容")

    # 处理信息
    assigned_to = Column(String(50), nullable=True, comment="处理人")
    resolution = Column(Text, nullable=True, comment="解决方案")
    resolution_time = Column(DateTime, nullable=True, comment="解决时间")

    # 退款信息
    refund_amount = Column(Float, nullable=True, comment="退款金额")
    refund_reason = Column(String(500), nullable=True, comment="退款原因")
    refund_status = Column(String(20), nullable=True, comment="退款状态")

    # 时间信息
    due_date = Column(DateTime, nullable=True, comment="截止时间")
    closed_at = Column(DateTime, nullable=True, comment="关闭时间")

    # 扩展字段
    attachments = Column(JSON, default=list, comment="附件列表")
    tags = Column(JSON, default=list, comment="标签")

    # 关系
    order_ref = relationship("Order", back_populates="tickets")

    __table_args__ = (
        Index("idx_tickets_order_id", "order_id"),
        Index("idx_tickets_status", "status"),
        Index("idx_tickets_type", "ticket_type"),
        Index("idx_tickets_platform", "platform"),
        Index("idx_tickets_assigned_to", "assigned_to"),
        Index("idx_tickets_created_at", "created_at"),
        Index("idx_tickets_status_priority", "status", "priority"),
        CheckConstraint("priority >= 1 AND priority <= 5", name="ck_tickets_priority"),
        CheckConstraint("refund_amount IS NULL OR refund_amount >= 0", name="ck_tickets_refund_amount"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "ticketId": self.ticket_id,
            "orderId": self.order_id,
            "platform": self.platform.value if self.platform else None,
            "ticketType": self.ticket_type.value if self.ticket_type else None,
            "status": self.status.value if self.status else None,
            "priority": self.priority,
            "title": self.title,
            "description": self.description,
            "customerComplaint": self.customer_complaint,
            "assignedTo": self.assigned_to,
            "resolution": self.resolution,
            "resolutionTime": self.resolution_time.isoformat() if self.resolution_time else None,
            "refundAmount": self.refund_amount,
            "refundReason": self.refund_reason,
            "refundStatus": self.refund_status,
            "dueDate": self.due_date.isoformat() if self.due_date else None,
            "closedAt": self.closed_at.isoformat() if self.closed_at else None,
            "attachments": self.attachments or [],
            "tags": self.tags or [],
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


class InventoryItem(TimestampMixin, Base):
    """库存项目模型"""
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku_id = Column(String(50), nullable=False, unique=True, comment="SKU ID")
    product_name = Column(String(200), nullable=False, comment="商品名称")
    platform = Column(Enum(PlatformEnum), nullable=False, comment="所属平台")

    # 库存信息
    total_stock = Column(Integer, default=0, comment="总库存")
    available_stock = Column(Integer, default=0, comment="可用库存")
    locked_stock = Column(Integer, default=0, comment="锁定库存")
    in_transit_stock = Column(Integer, default=0, comment="在途库存")

    # 预警设置
    min_stock_alert = Column(Integer, default=10, comment="最低库存预警")
    max_stock_alert = Column(Integer, default=1000, comment="最高库存预警")

    # 风险标签
    risk_tags = Column(JSON, default=list, comment="风险标签")
    risk_level = Column(Enum(RiskLevelEnum), default=RiskLevelEnum.LOW, comment="风险等级")

    # 扩展信息
    category = Column(String(100), nullable=True, comment="商品分类")
    supplier = Column(String(200), nullable=True, comment="供应商")
    cost_price = Column(Float, nullable=True, comment="成本价")
    sale_price = Column(Float, nullable=True, comment="销售价")

    # 关系
    logs = relationship("InventoryChangeLog", back_populates="inventory_ref", order_by="desc(InventoryChangeLog.created_at)")

    __table_args__ = (
        Index("idx_inventory_sku_id", "sku_id"),
        Index("idx_inventory_platform", "platform"),
        Index("idx_inventory_risk_level", "risk_level"),
        Index("idx_inventory_category", "category"),
        CheckConstraint("total_stock >= 0", name="ck_inventory_total_stock"),
        CheckConstraint("available_stock >= 0", name="ck_inventory_available_stock"),
        CheckConstraint("locked_stock >= 0", name="ck_inventory_locked_stock"),
        CheckConstraint("in_transit_stock >= 0", name="ck_inventory_in_transit_stock"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "skuId": self.sku_id,
            "productName": self.product_name,
            "platform": self.platform.value if self.platform else None,
            "totalStock": self.total_stock,
            "availableStock": self.available_stock,
            "lockedStock": self.locked_stock,
            "inTransitStock": self.in_transit_stock,
            "minStockAlert": self.min_stock_alert,
            "maxStockAlert": self.max_stock_alert,
            "riskTags": self.risk_tags or [],
            "riskLevel": self.risk_level.value if self.risk_level else None,
            "category": self.category,
            "supplier": self.supplier,
            "costPrice": self.cost_price,
            "salePrice": self.sale_price,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


class InventoryChangeLog(TimestampMixin, Base):
    """库存变动日志"""
    __tablename__ = "inventory_change_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    inventory_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False, comment="库存项ID")
    change_type = Column(String(20), nullable=False, comment="变动类型: order/return/adjust/restock")
    quantity = Column(Integer, nullable=False, comment="变动数量")
    before_stock = Column(Integer, nullable=False, comment="变动前库存")
    after_stock = Column(Integer, nullable=False, comment="变动后库存")
    order_id = Column(String(50), nullable=True, comment="关联订单ID")
    operator = Column(String(50), default="system", comment="操作人")
    remark = Column(String(500), default="", comment="备注")

    # 关系
    inventory_ref = relationship("InventoryItem", back_populates="logs")

    __table_args__ = (
        Index("idx_inventory_logs_inventory_id", "inventory_id"),
        Index("idx_inventory_logs_change_type", "change_type"),
        Index("idx_inventory_logs_created_at", "created_at"),
        Index("idx_inventory_logs_order_id", "order_id"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "inventoryId": self.inventory_id,
            "changeType": self.change_type,
            "quantity": self.quantity,
            "beforeStock": self.before_stock,
            "afterStock": self.after_stock,
            "orderId": self.order_id,
            "operator": self.operator,
            "remark": self.remark,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }
