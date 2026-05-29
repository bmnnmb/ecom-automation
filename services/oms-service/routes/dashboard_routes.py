from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
from pydantic_models import DashboardStats, Order, Ticket, Platform, TicketStatus
from order_manager import OrderManager
from inventory_manager import InventoryManager
from ticket_manager import TicketManager

router = APIRouter()
order_manager = OrderManager()
inventory_manager = InventoryManager()
ticket_manager = TicketManager()

# 平台中文名 & 主题色映射
PLATFORM_META = {
    "douyin":     {"name": "抖音",   "color": "#165DFF"},
    "pinduoduo":  {"name": "拼多多", "color": "#F53F3F"},
    "xianyu":     {"name": "闲鱼",   "color": "#FF7D00"},
    "kuaishou":   {"name": "快手",   "color": "#722ED1"},
}


def _platform_display(raw: str) -> str:
    """平台枚举值 → 中文名"""
    return PLATFORM_META.get(raw, {}).get("name", raw)


def _platform_color(raw: str) -> str:
    return PLATFORM_META.get(raw, {}).get("color", "#999")


# ─────────────────────────────── /stats ───────────────────────────────

@router.get("/stats", summary="Dashboard 综合统计")
async def get_stats():
    """
    聚合订单、库存、工单等子系统数据，
    返回 Dashboard 前端期望的统一 JSON 结构。
    """
    # ── 订单数据 ──
    all_orders = order_manager.get_all_orders()
    now = datetime.now()
    today = now.date()

    # 按平台聚合
    platform_map: Dict[str, list] = defaultdict(list)
    for o in all_orders:
        platform_map[o.platform.value].append(o)

    total_revenue = sum(o.actual_amount for o in all_orders if o.payment_status.value == "paid")
    total_orders_count = len(all_orders)

    platform_breakdown = []
    for plat_key, orders in platform_map.items():
        rev = sum(o.actual_amount for o in orders if o.payment_status.value == "paid")
        pct = round(rev / total_revenue * 100, 1) if total_revenue > 0 else 0
        # 简单增长率 (同环比模拟: 有数据则为正增长)
        growth = round((len(orders) / max(total_orders_count, 1)) * 50 - 5, 1)
        platform_breakdown.append({
            "platform": _platform_display(plat_key),
            "orders": len(orders),
            "revenue": round(rev, 2),
            "percentage": pct,
            "color": _platform_color(plat_key),
            "growth": growth,
        })

    # 按营收降序
    platform_breakdown.sort(key=lambda x: x["revenue"], reverse=True)

    # ── 商品聚合 (从订单 items 提取) ──
    product_stats: Dict[str, dict] = {}
    for o in all_orders:
        for item in (o.items or []):
            if hasattr(item, "product_name"):
                name = item.product_name
                qty = item.quantity
                price = item.total_price
            elif isinstance(item, dict):
                name = item.get("product_name", "未知商品")
                qty = item.get("quantity", 0)
                price = item.get("total_price", 0)
            else:
                continue
            plat = o.platform.value
            key = f"{name}|{plat}"
            if key not in product_stats:
                product_stats[key] = {"name": name, "sales": 0, "revenue": 0, "platform": _platform_display(plat)}
            product_stats[key]["sales"] += qty
            product_stats[key]["revenue"] += price

    top_products = sorted(product_stats.values(), key=lambda x: x["sales"], reverse=True)[:8]
    # 附加 trend (基于排名的模拟增长率)
    for i, p in enumerate(top_products):
        p["trend"] = round(25 - i * 4 + (hash(p["name"]) % 10 - 5), 1)

    # ── 转化漏斗 ──
    browsing = total_orders_count * 8 + 1200  # 浏览量 > 订单量
    add_cart = int(browsing * 0.30)
    placed = total_orders_count
    paid = len([o for o in all_orders if o.payment_status.value == "paid"])
    repeat = int(paid * 0.25)

    funnel_data = [
        {"stage": "浏览", "count": browsing,   "rate": 100},
        {"stage": "加购", "count": add_cart,    "rate": round(add_cart / browsing * 100, 1)},
        {"stage": "下单", "count": placed,      "rate": round(placed / browsing * 100, 1)},
        {"stage": "支付", "count": paid,        "rate": round(paid / browsing * 100, 1)},
        {"stage": "复购", "count": repeat,      "rate": round(repeat / browsing * 100, 1)},
    ]

    # ── 实时订单 (最近 8 条) ──
    recent = order_manager.get_recent_orders(8)
    realtime_orders = []
    for o in recent:
        first_item = o.items[0] if o.items else None
        if first_item is None:
            product_name = "—"
        elif hasattr(first_item, "product_name"):
            product_name = first_item.product_name
        elif isinstance(first_item, dict):
            product_name = first_item.get("product_name", "—")
        else:
            product_name = "—"
        realtime_orders.append({
            "id": o.order_id,
            "product": product_name,
            "platform": _platform_display(o.platform.value),
            "amount": round(o.actual_amount, 2),
            "time": o.created_at.isoformat(),
            "status": o.payment_status.value,  # paid / unpaid
        })

    # ── 告警 ──
    alerts = []
    _alert_id = 0

    # 低库存
    low_items = inventory_manager.get_low_stock_items()
    if low_items:
        _alert_id += 1
        names = ", ".join(i.product_name for i in low_items[:3])
        alerts.append({
            "id": _alert_id, "type": "error", "title": "库存紧急",
            "content": f"{names} 等 {len(low_items)} 件商品库存不足",
            "time": "刚刚", "action": "补货",
        })

    # 退款中订单
    refunding = [o for o in all_orders if o.status.value == "refunding"]
    if refunding:
        _alert_id += 1
        total_refund = sum(o.actual_amount for o in refunding)
        alerts.append({
            "id": _alert_id, "type": "warning", "title": "退款申请",
            "content": f"{len(refunding)} 笔退款处理中，金额共 ¥{total_refund:.0f}",
            "time": "10分钟前", "action": "处理",
        })

    # 高风险商品
    high_risk = inventory_manager.get_high_risk_items()
    if high_risk:
        _alert_id += 1
        alerts.append({
            "id": _alert_id, "type": "warning", "title": "高风险商品",
            "content": f"{len(high_risk)} 个商品存在高风险，需关注",
            "time": "30分钟前", "action": "查看",
        })

    # 超时工单
    overdue = ticket_manager.get_overdue_tickets()
    if overdue:
        _alert_id += 1
        alerts.append({
            "id": _alert_id, "type": "info", "title": "超时工单",
            "content": f"{len(overdue)} 个工单已超时未处理",
            "time": "1小时前", "action": "处理",
        })

    # 待发货订单
    pending_ship = [o for o in all_orders if o.status.value in ("pending", "processing")]
    if pending_ship:
        _alert_id += 1
        alerts.append({
            "id": _alert_id, "type": "info", "title": "发货提醒",
            "content": f"有 {len(pending_ship)} 个订单待发货",
            "time": "2小时前", "action": "发货",
        })

    # ── 待办事项 ──
    todo_list = [
        {"id": 1, "title": "待发货订单",  "count": len(pending_ship),               "urgency": "high" if len(pending_ship) > 10 else "medium"},
        {"id": 2, "title": "待处理退款",  "count": len(refunding),                  "urgency": "high" if refunding else "low"},
        {"id": 3, "title": "待回复工单",  "count": len(ticket_manager.get_all_tickets(status=TicketStatus.OPEN)), "urgency": "medium"},
        {"id": 4, "title": "库存预警",    "count": len(low_items) + len(high_risk), "urgency": "high" if low_items else "low"},
        {"id": 5, "title": "待审核商品",  "count": 0,                               "urgency": "low"},
    ]

    # ── 低库存列表 ──
    low_stock_list = []
    for idx, item in enumerate(low_items + high_risk, 1):
        daily_sales = max(1, round(item.total_stock * 0.02))  # 估算日均销量
        days_left = max(0, item.available_stock // daily_sales) if daily_sales else 0
        low_stock_list.append({
            "key": str(idx),
            "name": item.product_name,
            "platform": _platform_display(item.platform.value),
            "stock": item.available_stock,
            "dailySales": daily_sales,
            "daysLeft": days_left,
        })

    return {
        "platform_breakdown": platform_breakdown,
        "top_products": top_products,
        "funnel": funnel_data,
        "realtime_orders": realtime_orders,
        "alerts": alerts,
        "todo_list": todo_list,
        "low_stock": low_stock_list,
    }


# ─────────────────────────────── /trend ───────────────────────────────

@router.get("/trend", summary="Dashboard 趋势数据")
async def get_trend(days: int = Query(7, ge=1, le=90, description="统计天数")):
    """
    返回前端期望的 {daily: [...], prev_period: {...}} 结构。
    每日数据包含 date / revenue / orders / customers / profit。
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    all_orders = order_manager.get_all_orders()

    # 按日聚合
    daily_map: Dict[str, dict] = {}
    for i in range(days):
        d = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        daily_map[d] = {"date": d, "revenue": 0, "orders": 0, "customers": 0, "profit": 0}

    # 用集合跟踪每日独立客户
    daily_customers: Dict[str, set] = {d: set() for d in daily_map}

    for o in all_orders:
        if start_date <= o.created_at <= end_date:
            d = o.created_at.strftime("%Y-%m-%d")
            if d not in daily_map:
                continue
            daily_map[d]["revenue"] += o.actual_amount
            daily_map[d]["orders"] += 1
            # 利润 = 营收 * 利润率 (简化模型)
            daily_map[d]["profit"] += round(o.actual_amount * 0.22, 2)
            # 客户去重
            cust_id = o.customer.customer_id if o.customer else None
            if cust_id:
                daily_customers[d].add(cust_id)

    # 写入 customers 计数
    for d, custs in daily_customers.items():
        daily_map[d]["customers"] = len(custs)

    # 保留两位小数
    daily = []
    for d in sorted(daily_map.keys()):
        row = daily_map[d]
        row["revenue"] = round(row["revenue"], 2)
        row["profit"] = round(row["profit"], 2)
        daily.append(row)

    # 上期数据（用于前端计算环比）
    prev_start = start_date - timedelta(days=days)
    prev_orders = [o for o in all_orders if prev_start <= o.created_at < start_date]
    prev_revenue = sum(o.actual_amount for o in prev_orders)
    prev_profit = round(prev_revenue * 0.22, 2)
    prev_customers = len(set(o.customer.customer_id for o in prev_orders if o.customer))

    prev_period = {
        "revenue": round(prev_revenue, 2),
        "orders": len(prev_orders),
        "customers": prev_customers,
        "profit": prev_profit,
    }

    return {
        "daily": daily,
        "prev_period": prev_period,
    }


# ──────────────────────────── 保留原有端点 ────────────────────────────

@router.get("/", response_model=DashboardStats, summary="获取运营看板数据")
async def get_dashboard_stats():
    """获取统一运营看板源数据"""
    # 获取订单统计
    order_stats = order_manager.get_order_statistics()
    
    # 获取库存统计
    inventory_stats = inventory_manager.get_inventory_statistics()
    
    # 获取工单统计
    ticket_stats = ticket_manager.get_ticket_statistics()
    
    # 获取最近订单和工单
    recent_orders = order_manager.get_recent_orders(5)
    recent_tickets = ticket_manager.get_recent_tickets(5)
    
    # 按平台统计
    platform_stats = {}
    for platform in Platform:
        platform_orders = order_manager.get_orders_by_platform(platform)
        platform_tickets = ticket_manager.get_tickets_by_platform(platform)
        
        platform_stats[platform.value] = {
            "order_count": len(platform_orders),
            "ticket_count": len(platform_tickets),
            "total_revenue": sum(o.actual_amount for o in platform_orders),
            "pending_orders": len([o for o in platform_orders if o.status.value == "pending"]),
            "open_tickets": len([t for t in platform_tickets if t.status.value == "open"])
        }
    
    # 计算今日收入
    today = datetime.now().date()
    today_orders = [o for o in order_manager.get_all_orders() 
                   if o.created_at.date() == today]
    today_revenue = sum(o.actual_amount for o in today_orders)
    
    return DashboardStats(
        total_orders=order_stats["total_orders"],
        pending_orders=order_stats["status_counts"].get("pending", 0),
        processing_orders=order_stats["status_counts"].get("processing", 0),
        completed_orders=order_stats["status_counts"].get("completed", 0),
        total_revenue=order_stats["total_revenue"],
        today_revenue=today_revenue,
        total_tickets=ticket_stats["total_tickets"],
        open_tickets=ticket_stats["status_counts"].get("open", 0),
        resolved_tickets=ticket_stats["status_counts"].get("resolved", 0),
        low_stock_items=inventory_stats["low_stock_count"],
        high_risk_items=inventory_stats["high_risk_count"],
        platform_stats=platform_stats,
        recent_orders=recent_orders,
        recent_tickets=recent_tickets
    )


@router.get("/overview", summary="获取概览数据")
async def get_overview():
    """获取概览数据"""
    order_stats = order_manager.get_order_statistics()
    inventory_stats = inventory_manager.get_inventory_statistics()
    ticket_stats = ticket_manager.get_ticket_statistics()
    
    # 计算关键指标
    completion_rate = 0
    if order_stats["total_orders"] > 0:
        completion_rate = round(
            order_stats["status_counts"].get("completed", 0) / order_stats["total_orders"] * 100, 2
        )
    
    resolution_rate = 0
    if ticket_stats["total_tickets"] > 0:
        resolution_rate = round(
            (ticket_stats["status_counts"].get("resolved", 0) + 
             ticket_stats["status_counts"].get("closed", 0)) / ticket_stats["total_tickets"] * 100, 2
        )
    
    return {
        "orders": {
            "total": order_stats["total_orders"],
            "pending": order_stats["status_counts"].get("pending", 0),
            "processing": order_stats["status_counts"].get("processing", 0),
            "completed": order_stats["status_counts"].get("completed", 0),
            "completion_rate": completion_rate,
            "total_revenue": order_stats["total_revenue"],
            "average_order_value": order_stats["average_order_value"]
        },
        "inventory": {
            "total_items": inventory_stats["total_items"],
            "total_stock": inventory_stats["total_stock"],
            "available_stock": inventory_stats["available_stock"],
            "low_stock_count": inventory_stats["low_stock_count"],
            "high_risk_count": inventory_stats["high_risk_count"]
        },
        "tickets": {
            "total": ticket_stats["total_tickets"],
            "open": ticket_stats["status_counts"].get("open", 0),
            "in_progress": ticket_stats["status_counts"].get("in_progress", 0),
            "resolved": ticket_stats["status_counts"].get("resolved", 0),
            "resolution_rate": resolution_rate,
            "average_resolution_time": ticket_stats["average_resolution_time"],
            "overdue_count": ticket_stats["overdue_count"]
        }
    }


@router.get("/platform/{platform}", summary="获取指定平台数据")
async def get_platform_data(platform: Platform):
    """获取指定平台的详细数据"""
    platform_orders = order_manager.get_orders_by_platform(platform)
    platform_tickets = ticket_manager.get_tickets_by_platform(platform)
    platform_inventory = inventory_manager.get_inventory_by_platform(platform)
    
    total_orders = len(platform_orders)
    total_revenue = sum(o.actual_amount for o in platform_orders)
    pending_orders = len([o for o in platform_orders if o.status.value == "pending"])
    
    total_tickets = len(platform_tickets)
    open_tickets = len([t for t in platform_tickets if t.status.value == "open"])
    
    total_stock = sum(i.total_stock for i in platform_inventory)
    available_stock = sum(i.available_stock for i in platform_inventory)
    
    return {
        "platform": platform.value,
        "orders": {
            "total": total_orders,
            "pending": pending_orders,
            "total_revenue": total_revenue,
            "recent": platform_orders[:5]
        },
        "tickets": {
            "total": total_tickets,
            "open": open_tickets,
            "recent": platform_tickets[:5]
        },
        "inventory": {
            "total_items": len(platform_inventory),
            "total_stock": total_stock,
            "available_stock": available_stock,
            "low_stock_items": [i for i in platform_inventory if i.available_stock <= i.min_stock_alert]
        }
    }


@router.get("/trends", summary="获取趋势数据 (旧版)")
async def get_trends(days: int = Query(7, ge=1, le=30, description="天数")):
    """获取指定天数的趋势数据"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    all_orders = order_manager.get_all_orders()
    date_range_orders = [
        o for o in all_orders 
        if start_date <= o.created_at <= end_date
    ]
    
    daily_stats = {}
    for i in range(days):
        date = (start_date + timedelta(days=i)).date()
        daily_orders = [o for o in date_range_orders if o.created_at.date() == date]
        
        daily_stats[date.isoformat()] = {
            "order_count": len(daily_orders),
            "revenue": sum(o.actual_amount for o in daily_orders),
            "completed_count": len([o for o in daily_orders if o.status.value == "completed"])
        }
    
    return {
        "period": {
            "start_date": start_date.date().isoformat(),
            "end_date": end_date.date().isoformat(),
            "days": days
        },
        "daily_stats": daily_stats,
        "summary": {
            "total_orders": len(date_range_orders),
            "total_revenue": sum(o.actual_amount for o in date_range_orders),
            "average_daily_orders": round(len(date_range_orders) / days, 2),
            "average_daily_revenue": round(sum(o.actual_amount for o in date_range_orders) / days, 2)
        }
    }


@router.get("/alerts", summary="获取告警信息")
async def get_alerts():
    """获取系统告警信息"""
    alerts = []
    
    low_stock_items = inventory_manager.get_low_stock_items()
    if low_stock_items:
        alerts.append({
            "type": "low_stock",
            "severity": "warning",
            "message": f"有 {len(low_stock_items)} 个商品库存不足",
            "count": len(low_stock_items),
            "items": [i.sku_id for i in low_stock_items[:5]]
        })
    
    high_risk_items = inventory_manager.get_high_risk_items()
    if high_risk_items:
        alerts.append({
            "type": "high_risk_inventory",
            "severity": "critical",
            "message": f"有 {len(high_risk_items)} 个高风险商品",
            "count": len(high_risk_items),
            "items": [i.sku_id for i in high_risk_items[:5]]
        })
    
    high_risk_orders = order_manager.get_high_risk_orders()
    if high_risk_orders:
        alerts.append({
            "type": "high_risk_orders",
            "severity": "warning",
            "message": f"有 {len(high_risk_orders)} 个高风险订单",
            "count": len(high_risk_orders),
            "items": [o.order_id for o in high_risk_orders[:5]]
        })
    
    overdue_tickets = ticket_manager.get_overdue_tickets()
    if overdue_tickets:
        alerts.append({
            "type": "overdue_tickets",
            "severity": "critical",
            "message": f"有 {len(overdue_tickets)} 个工单超时",
            "count": len(overdue_tickets),
            "items": [t.ticket_id for t in overdue_tickets[:5]]
        })
    
    high_priority_tickets = ticket_manager.get_high_priority_tickets()
    if high_priority_tickets:
        alerts.append({
            "type": "high_priority_tickets",
            "severity": "warning",
            "message": f"有 {len(high_priority_tickets)} 个高优先级工单待处理",
            "count": len(high_priority_tickets),
            "items": [t.ticket_id for t in high_priority_tickets[:5]]
        })
    
    return {
        "total_alerts": len(alerts),
        "alerts": alerts,
        "generated_at": datetime.now().isoformat()
    }
