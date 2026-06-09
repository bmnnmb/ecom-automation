"""
供应链路由

提供供应商管理、采购单、库存、出入库记录。
使用内存存储 + 种子数据。
"""
from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime, timedelta
import random

from utils.responses import success_response

router = APIRouter()


def _generate_seed_data():
    """生成供应链种子数据"""
    random.seed(42)
    now = datetime.now()

    # 供应商
    suppliers = [
        {"id": "SUP-001", "name": "深圳华强北电子有限公司", "contact": "张经理", "phone": "138****1234", "category": "数码配件", "rating": 4.8, "cooperation": "2024-03-15", "status": "合作中", "products": 45, "totalOrders": 320},
        {"id": "SUP-002", "name": "义乌小商品批发市场A区", "contact": "李总", "phone": "139****5678", "category": "生活用品", "rating": 4.5, "cooperation": "2024-06-20", "status": "合作中", "products": 32, "totalOrders": 256},
        {"id": "SUP-003", "name": "广州智能家居科技", "contact": "王工", "phone": "137****9012", "category": "智能家居", "rating": 4.9, "cooperation": "2023-11-08", "status": "合作中", "products": 28, "totalOrders": 189},
        {"id": "SUP-004", "name": "杭州服饰供应链", "contact": "赵姐", "phone": "136****3456", "category": "服饰鞋包", "rating": 4.3, "cooperation": "2025-01-10", "status": "合作中", "products": 56, "totalOrders": 412},
        {"id": "SUP-005", "name": "东莞数码配件工厂", "contact": "陈老板", "phone": "135****7890", "category": "数码配件", "rating": 4.6, "cooperation": "2024-08-25", "status": "暂停合作", "products": 18, "totalOrders": 95},
    ]

    # 采购单
    purchase_orders = []
    statuses = ['待确认', '已确认', '已发货', '已入库', '已完成']
    for i in range(20):
        supplier = suppliers[i % len(suppliers)]
        amount = round(random.uniform(2000, 30000), 2)
        purchase_orders.append({
            "id": f"PO-{i+1:06d}",
            "supplierId": supplier["id"],
            "supplierName": supplier["name"],
            "products": random.randint(1, 10),
            "totalAmount": amount,
            "status": statuses[min(i, 4)] if i < 5 else random.choice(statuses),
            "createdAt": (now - timedelta(days=random.randint(0, 30))).isoformat(),
            "expectedDate": (now + timedelta(days=random.randint(3, 15))).isoformat(),
        })

    # 库存数据
    inventory = []
    products = [
        '智能降噪蓝牙耳机', '便携式迷你投影仪', '磁吸无线充电宝', '超轻碳纤维行李箱',
        '人体工学办公椅', '智能恒温保温杯', '空气净化器', '电动牙刷',
        '智能手表', '降噪头戴式耳机', '机械键盘', 'USB-C扩展坞',
    ]
    for i, name in enumerate(products):
        stock = random.randint(0, 500)
        daily_sales = random.randint(1, 20)
        inventory.append({
            "id": f"INV-{i+1:04d}",
            "name": name,
            "sku": f"SKU-{1000 + i}",
            "platform": ['douyin', 'pdd', 'xianyu', 'kuaishou'][i % 4],
            "stock": stock,
            "warningLine": 20,
            "dailySales": daily_sales,
            "daysLeft": stock // max(daily_sales, 1),
            "status": '缺货' if stock == 0 else '预警' if stock < 20 else '正常',
            "lastInbound": (now - timedelta(days=random.randint(1, 15))).isoformat(),
        })

    # 出入库记录
    stock_records = []
    for i in range(30):
        is_in = random.choice([True, True, False])
        stock_records.append({
            "id": f"SR-{i+1:06d}",
            "type": '入库' if is_in else '出库',
            "product": products[i % len(products)],
            "quantity": random.randint(5, 200),
            "operator": random.choice(['张三', '李四', '王五', '系统自动']),
            "reason": random.choice(['采购入库', '销售出库', '退货入库', '盘点调整', '调拨']) if is_in else random.choice(['销售出库', '退货出库', '盘点调整', '调拨']),
            "createdAt": (now - timedelta(days=random.randint(0, 20), hours=random.randint(0, 23))).isoformat(),
        })

    random.seed()
    return suppliers, purchase_orders, inventory, stock_records


_suppliers, _purchase_orders, _inventory, _stock_records = _generate_seed_data()


@router.get("/stats")
async def get_supply_chain_stats():
    """获取供应链统计"""
    total_stock = sum(i['stock'] for i in _inventory)
    warning_count = sum(1 for i in _inventory if i['status'] == '预警')
    out_of_stock = sum(1 for i in _inventory if i['status'] == '缺货')
    pending_po = sum(1 for p in _purchase_orders if p['status'] in ['待确认', '已确认'])

    return success_response(data={
        "totalStock": total_stock,
        "warningCount": warning_count,
        "outOfStock": out_of_stock,
        "pendingPurchaseOrders": pending_po,
        "supplierCount": len([s for s in _suppliers if s['status'] == '合作中']),
    })


@router.get("/suppliers")
async def list_suppliers(
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取供应商列表"""
    items = _suppliers.copy()
    if status:
        items = [s for s in items if s['status'] == status]
    if keyword:
        kw = keyword.lower()
        items = [s for s in items if kw in s['name'].lower() or kw in s['category'].lower()]

    total = len(items)
    start = (page - 1) * page_size
    paged = items[start:start + page_size]
    return success_response(data={"items": paged, "total": total})


@router.get("/purchase-orders")
async def list_purchase_orders(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取采购单列表"""
    items = _purchase_orders.copy()
    if status:
        items = [p for p in items if p['status'] == status]

    total = len(items)
    start = (page - 1) * page_size
    paged = items[start:start + page_size]
    return success_response(data={"items": paged, "total": total})


@router.get("/inventory")
async def list_inventory(
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取库存列表"""
    items = _inventory.copy()
    if status:
        items = [i for i in items if i['status'] == status]
    if keyword:
        kw = keyword.lower()
        items = [i for i in items if kw in i['name'].lower()]

    total = len(items)
    start = (page - 1) * page_size
    paged = items[start:start + page_size]
    return success_response(data={"items": paged, "total": total})


@router.get("/stock-records")
async def list_stock_records(
    type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取出入库记录"""
    items = _stock_records.copy()
    if type:
        items = [r for r in items if r['type'] == type]

    total = len(items)
    start = (page - 1) * page_size
    paged = items[start:start + page_size]
    return success_response(data={"items": paged, "total": total})
