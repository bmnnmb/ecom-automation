"""
订单管理器 - SQLite 持久化版
首次启动自动建表 + 种子数据；后续启动数据不丢失。
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import uuid

from sqlalchemy import func as sqlfunc
from database import SessionLocal, init_db, engine
from order_db_models import OrderRecord
from pydantic_models import Order, OrderStatus, Platform, PaymentStatus, RiskLevel, OrderItem, CustomerInfo, ShippingInfo, PaymentInfo


class OrderManager:
    """订单管理器 — 基于 SQLite"""

    _initialized = False

    def __init__(self):
        if not OrderManager._initialized:
            init_db()
            self._seed_if_empty()
            OrderManager._initialized = True

    # ─── 种子数据 ──────────────────────────────────────────
    def _seed_if_empty(self):
        db = SessionLocal()
        try:
            count = db.query(OrderRecord).count()
            if count > 0:
                return
            now = datetime.now()
            seeds = [
                OrderRecord(
                    order_id="ORD-2024-001",
                    platform="douyin",
                    platform_order_id="DY123456789",
                    status="processing",
                    payment_status="paid",
                    items=[{"sku_id": "SKU-001", "product_name": "夏季新款T恤", "quantity": 2, "unit_price": 99.0, "total_price": 198.0, "specifications": {"颜色": "白色", "尺码": "L"}}],
                    total_amount=198.0,
                    discount_amount=20.0,
                    actual_amount=178.0,
                    customer={"customer_id": "CUST-001", "name": "张三", "phone": "13800138001", "address": "北京市朝阳区xxx街道", "platform_uid": "DY-USER-001"},
                    shipping={"carrier": "顺丰速运", "tracking_number": "SF1234567890", "shipping_method": "快递"},
                    payment={"payment_method": "支付宝", "transaction_id": "ALI20240001", "payment_time": (now - timedelta(hours=2)).isoformat(), "amount": 178.0},
                    paid_at=now - timedelta(hours=2),
                    tags=["VIP客户", "加急"],
                    risk_level="low",
                    created_at=now - timedelta(hours=3),
                ),
                OrderRecord(
                    order_id="ORD-2024-002",
                    platform="kuaishou",
                    platform_order_id="KS987654321",
                    status="pending",
                    payment_status="paid",
                    items=[{"sku_id": "SKU-002", "product_name": "运动鞋", "quantity": 1, "unit_price": 299.0, "total_price": 299.0, "specifications": {"颜色": "黑色", "尺码": "42"}}],
                    total_amount=299.0,
                    discount_amount=0,
                    actual_amount=299.0,
                    customer={"customer_id": "CUST-002", "name": "李四", "phone": "13900139002", "address": "上海市浦东新区xxx路", "platform_uid": "KS-USER-002"},
                    paid_at=now - timedelta(minutes=30),
                    tags=["新客户"],
                    risk_level="low",
                    created_at=now - timedelta(hours=1),
                ),
                OrderRecord(
                    order_id="ORD-2024-003",
                    platform="pinduoduo",
                    platform_order_id="PDD111222333",
                    status="refunding",
                    payment_status="paid",
                    items=[{"sku_id": "SKU-003", "product_name": "蓝牙耳机", "quantity": 1, "unit_price": 159.0, "total_price": 159.0, "specifications": {"颜色": "白色"}}],
                    total_amount=159.0,
                    discount_amount=10.0,
                    actual_amount=149.0,
                    customer={"customer_id": "CUST-003", "name": "王五", "phone": "13700137003", "address": "广州市天河区xxx号", "platform_uid": "PDD-USER-003"},
                    paid_at=now - timedelta(days=1),
                    tags=["退款中", "质量投诉"],
                    risk_level="medium",
                    remarks="客户反映耳机有杂音",
                    created_at=now - timedelta(days=1),
                ),
                OrderRecord(
                    order_id="ORD-2024-004",
                    platform="douyin",
                    platform_order_id="DY987123456",
                    status="shipped",
                    payment_status="paid",
                    items=[{"sku_id": "SKU-004", "product_name": "无线充电器", "quantity": 3, "unit_price": 49.0, "total_price": 147.0}],
                    total_amount=147.0,
                    discount_amount=15.0,
                    actual_amount=132.0,
                    customer={"customer_id": "CUST-004", "name": "赵六", "phone": "13600136004", "address": "深圳市南山区xxx路", "platform_uid": "DY-USER-004"},
                    shipping={"carrier": "中通快递", "tracking_number": "ZT7890123456", "shipping_method": "快递"},
                    paid_at=now - timedelta(hours=6),
                    shipped_at=now - timedelta(hours=4),
                    tags=["老客户"],
                    risk_level="low",
                    created_at=now - timedelta(hours=8),
                ),
                OrderRecord(
                    order_id="ORD-2024-005",
                    platform="xianyu",
                    platform_order_id="XY555666777",
                    status="completed",
                    payment_status="paid",
                    items=[{"sku_id": "SKU-005", "product_name": "机械键盘", "quantity": 1, "unit_price": 359.0, "total_price": 359.0}],
                    total_amount=359.0,
                    discount_amount=0,
                    actual_amount=359.0,
                    customer={"customer_id": "CUST-005", "name": "孙七", "phone": "13500135005", "address": "杭州市西湖区xxx号", "platform_uid": "XY-USER-005"},
                    paid_at=now - timedelta(days=3),
                    shipped_at=now - timedelta(days=2),
                    completed_at=now - timedelta(hours=12),
                    tags=[],
                    risk_level="low",
                    created_at=now - timedelta(days=3),
                ),
                OrderRecord(
                    order_id="ORD-2024-006",
                    platform="pinduoduo",
                    platform_order_id="PDD444555666",
                    status="processing",
                    payment_status="paid",
                    items=[{"sku_id": "SKU-006", "product_name": "智能手表", "quantity": 1, "unit_price": 599.0, "total_price": 599.0}],
                    total_amount=599.0,
                    discount_amount=50.0,
                    actual_amount=549.0,
                    customer={"customer_id": "CUST-006", "name": "周八", "phone": "13400134006", "address": "成都市锦江区xxx路", "platform_uid": "PDD-USER-006"},
                    paid_at=now - timedelta(minutes=45),
                    tags=["大额订单"],
                    risk_level="low",
                    created_at=now - timedelta(hours=1),
                ),
            ]
            db.add_all(seeds)
            db.commit()
        finally:
            db.close()

    # ─── 查询 ──────────────────────────────────────────────
    def get_all_orders(self, platform=None, status=None,
                       start_date=None, end_date=None) -> List[Order]:
        db = SessionLocal()
        try:
            q = db.query(OrderRecord)
            if platform:
                q = q.filter(OrderRecord.platform == (platform.value if hasattr(platform, 'value') else platform))
            if status:
                q = q.filter(OrderRecord.status == (status.value if hasattr(status, 'value') else status))
            if start_date:
                q = q.filter(OrderRecord.created_at >= start_date)
            if end_date:
                q = q.filter(OrderRecord.created_at <= end_date)
            q = q.order_by(OrderRecord.created_at.desc())
            return [self._to_pydantic(r) for r in q.all()]
        finally:
            db.close()

    def get_order_by_id(self, order_id: str) -> Optional[Order]:
        db = SessionLocal()
        try:
            rec = db.query(OrderRecord).filter(OrderRecord.order_id == order_id).first()
            return self._to_pydantic(rec) if rec else None
        finally:
            db.close()

    def get_orders_by_platform(self, platform: Platform) -> List[Order]:
        return self.get_all_orders(platform=platform)

    def get_orders_by_status(self, status: OrderStatus) -> List[Order]:
        return self.get_all_orders(status=status)

    def get_recent_orders(self, limit: int = 10) -> List[Order]:
        db = SessionLocal()
        try:
            recs = db.query(OrderRecord).order_by(OrderRecord.created_at.desc()).limit(limit).all()
            return [self._to_pydantic(r) for r in recs]
        finally:
            db.close()

    def get_high_risk_orders(self) -> List[Order]:
        db = SessionLocal()
        try:
            recs = db.query(OrderRecord).filter(
                OrderRecord.risk_level.in_(["high", "critical"])
            ).all()
            return [self._to_pydantic(r) for r in recs]
        finally:
            db.close()

    def get_refunding_orders(self) -> List[Order]:
        db = SessionLocal()
        try:
            recs = db.query(OrderRecord).filter(OrderRecord.status == "refunding").all()
            return [self._to_pydantic(r) for r in recs]
        finally:
            db.close()

    def search_orders(self, keyword: str) -> List[Order]:
        db = SessionLocal()
        try:
            kw = f"%{keyword.lower()}%"
            recs = db.query(OrderRecord).filter(
                (OrderRecord.order_id.ilike(kw)) |
                (OrderRecord.platform_order_id.ilike(kw))
            ).all()
            # Also search in customer name (JSON field — filter in Python)
            all_recs = db.query(OrderRecord).all()
            results = []
            for r in recs:
                results.append(r.order_id)
            for r in all_recs:
                if r.order_id in results:
                    continue
                cname = (r.customer or {}).get("name", "").lower()
                if keyword.lower() in cname:
                    results.append(r.order_id)
            if results:
                recs = db.query(OrderRecord).filter(OrderRecord.order_id.in_(results)).all()
            return [self._to_pydantic(r) for r in recs]
        finally:
            db.close()

    # ─── 创建 ──────────────────────────────────────────────
    def create_order(self, order_data: Dict[str, Any]) -> Order:
        db = SessionLocal()
        try:
            if "order_id" not in order_data:
                order_data["order_id"] = f"ORD-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            now = datetime.now()
            rec = OrderRecord(
                order_id=order_data["order_id"],
                platform=order_data.get("platform", "douyin"),
                platform_order_id=order_data.get("platform_order_id", ""),
                status=order_data.get("status", "pending"),
                payment_status=order_data.get("payment_status", "unpaid"),
                items=order_data.get("items", []),
                total_amount=order_data.get("total_amount", 0),
                discount_amount=order_data.get("discount_amount", 0),
                actual_amount=order_data.get("actual_amount", 0),
                customer=order_data.get("customer"),
                shipping=order_data.get("shipping"),
                payment=order_data.get("payment"),
                remarks=order_data.get("remarks"),
                tags=order_data.get("tags", []),
                risk_level=order_data.get("risk_level", "low"),
                created_at=order_data.get("created_at", now),
            )
            db.add(rec)
            db.commit()
            db.refresh(rec)
            return self._to_pydantic(rec)
        finally:
            db.close()

    # ─── 更新 ──────────────────────────────────────────────
    def update_order_status(self, order_id: str, new_status: OrderStatus) -> Optional[Order]:
        db = SessionLocal()
        try:
            rec = db.query(OrderRecord).filter(OrderRecord.order_id == order_id).first()
            if not rec:
                return None
            status_val = new_status.value if hasattr(new_status, 'value') else new_status
            rec.status = status_val
            rec.updated_at = datetime.now()
            if status_val == "shipped":
                rec.shipped_at = datetime.now()
            elif status_val == "completed":
                rec.completed_at = datetime.now()
            db.commit()
            db.refresh(rec)
            return self._to_pydantic(rec)
        finally:
            db.close()

    def update_payment_status(self, order_id: str, payment_status: PaymentStatus) -> Optional[Order]:
        db = SessionLocal()
        try:
            rec = db.query(OrderRecord).filter(OrderRecord.order_id == order_id).first()
            if not rec:
                return None
            ps_val = payment_status.value if hasattr(payment_status, 'value') else payment_status
            rec.payment_status = ps_val
            rec.updated_at = datetime.now()
            if ps_val == "paid":
                rec.paid_at = datetime.now()
            db.commit()
            db.refresh(rec)
            return self._to_pydantic(rec)
        finally:
            db.close()

    def add_order_tag(self, order_id: str, tag: str) -> Optional[Order]:
        db = SessionLocal()
        try:
            rec = db.query(OrderRecord).filter(OrderRecord.order_id == order_id).first()
            if not rec:
                return None
            tags = rec.tags or []
            if tag not in tags:
                tags.append(tag)
                rec.tags = tags
                rec.updated_at = datetime.now()
                db.commit()
                db.refresh(rec)
            return self._to_pydantic(rec)
        finally:
            db.close()

    def remove_order_tag(self, order_id: str, tag: str) -> Optional[Order]:
        db = SessionLocal()
        try:
            rec = db.query(OrderRecord).filter(OrderRecord.order_id == order_id).first()
            if not rec:
                return None
            tags = rec.tags or []
            if tag in tags:
                tags.remove(tag)
                rec.tags = tags
                rec.updated_at = datetime.now()
                db.commit()
                db.refresh(rec)
            return self._to_pydantic(rec)
        finally:
            db.close()

    def set_order_risk_level(self, order_id: str, risk_level: RiskLevel) -> Optional[Order]:
        db = SessionLocal()
        try:
            rec = db.query(OrderRecord).filter(OrderRecord.order_id == order_id).first()
            if not rec:
                return None
            rec.risk_level = risk_level.value if hasattr(risk_level, 'value') else risk_level
            rec.updated_at = datetime.now()
            db.commit()
            db.refresh(rec)
            return self._to_pydantic(rec)
        finally:
            db.close()

    # ─── 删除 ──────────────────────────────────────────────
    def delete_order(self, order_id: str) -> bool:
        db = SessionLocal()
        try:
            rec = db.query(OrderRecord).filter(OrderRecord.order_id == order_id).first()
            if not rec:
                return False
            db.delete(rec)
            db.commit()
            return True
        finally:
            db.close()

    # ─── 统计 ──────────────────────────────────────────────
    def get_order_statistics(self) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            total = db.query(OrderRecord).count()
            if total == 0:
                return {"total_orders": 0, "status_counts": {}, "platform_counts": {}, "total_revenue": 0, "average_order_value": 0}
            # status counts
            status_rows = db.query(OrderRecord.status, sqlfunc.count()).group_by(OrderRecord.status).all()
            status_counts = {s: c for s, c in status_rows}
            # platform counts
            plat_rows = db.query(OrderRecord.platform, sqlfunc.count()).group_by(OrderRecord.platform).all()
            platform_counts = {p: c for p, c in plat_rows}
            # revenue
            total_revenue = db.query(sqlfunc.sum(OrderRecord.actual_amount)).filter(
                OrderRecord.payment_status == "paid"
            ).scalar() or 0
            return {
                "total_orders": total,
                "status_counts": status_counts,
                "platform_counts": platform_counts,
                "total_revenue": float(total_revenue),
                "average_order_value": float(total_revenue) / total if total else 0,
            }
        finally:
            db.close()

    # ─── ORM → Pydantic 转换 ───────────────────────────────
    @staticmethod
    def _to_pydantic(rec: OrderRecord) -> Order:
        """将 ORM 记录转换为 Pydantic Order 模型"""
        items = rec.items or []
        order_items = []
        for it in items:
            if isinstance(it, dict):
                order_items.append(OrderItem(**it))
            else:
                order_items.append(it)

        customer = rec.customer or {}
        cust_obj = CustomerInfo(**customer) if customer and isinstance(customer, dict) else customer

        shipping = rec.shipping
        ship_obj = ShippingInfo(**shipping) if shipping and isinstance(shipping, dict) else shipping

        payment = rec.payment
        pay_obj = PaymentInfo(**payment) if payment and isinstance(payment, dict) else payment

        return Order(
            order_id=rec.order_id,
            platform=Platform(rec.platform),
            platform_order_id=rec.platform_order_id,
            status=OrderStatus(rec.status),
            payment_status=PaymentStatus(rec.payment_status),
            items=order_items,
            total_amount=rec.total_amount,
            discount_amount=rec.discount_amount or 0,
            actual_amount=rec.actual_amount,
            customer=cust_obj,
            shipping=ship_obj,
            payment=pay_obj,
            created_at=rec.created_at,
            updated_at=rec.updated_at,
            paid_at=rec.paid_at,
            shipped_at=rec.shipped_at,
            completed_at=rec.completed_at,
            remarks=rec.remarks,
            tags=rec.tags or [],
            risk_level=RiskLevel(rec.risk_level) if rec.risk_level else RiskLevel.LOW,
        )
