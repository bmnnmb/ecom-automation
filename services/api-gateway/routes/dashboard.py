"""
Dashboard 运营看板路由

提供 /api/dashboard/stats（综合统计）和 /api/dashboard/trend（趋势数据）两个端点，
前端 Dashboard 页面通过这两个接口获取真实数据。

数据来源: 汇聚订单、商品、库存等子系统的统计结果。
后续替换为真实数据库查询，当前使用内存模拟数据。
"""
from fastapi import APIRouter, Query
from datetime import datetime, timedelta
import random
import math

from utils.responses import success_response

router = APIRouter()

# ============================================================
# 辅助: 确定性随机（基于日期种子，保证同一天返回一致数据）
# ============================================================

def _seeded_rand(seed_str: str):
    """基于字符串种子创建确定性随机数生成器"""
    h = 0
    for ch in seed_str:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return random.Random(h)


def _generate_daily_series(days: int, end_date: datetime | None = None):
    """生成 days 天的日趋势数据，带合理波动"""
    if end_date is None:
        end_date = datetime.now()
    data = []
    base_revenue = 22000
    for i in range(days):
        dt = end_date - timedelta(days=days - 1 - i)
        date_str = dt.strftime("%Y-%m-%d")
        rng = _seeded_rand(date_str)
        # 周末略高
        weekday_boost = 1.15 if dt.weekday() >= 5 else 1.0
        trend_factor = 1 + i * 0.006  # 缓慢增长趋势
        revenue = round((base_revenue + rng.uniform(-6000, 8000)) * weekday_boost * trend_factor)
        orders = max(5, round(revenue / (70 + rng.random() * 50)))
        customers = max(2, round(orders * (0.3 + rng.random() * 0.25)))
        profit = round(revenue * (0.18 + rng.random() * 0.17))
        data.append({
            "date": date_str,
            "revenue": revenue,
            "orders": orders,
            "customers": customers,
            "profit": profit,
        })
    return data


def _platform_breakdown():
    """各平台经营数据"""
    return [
        {"platform": "抖音", "orders": 1245, "revenue": 125680, "percentage": 35, "color": "#165DFF", "growth": 12.3},
        {"platform": "拼多多", "orders": 986, "revenue": 89420, "percentage": 25, "color": "#F53F3F", "growth": -2.1},
        {"platform": "闲鱼", "orders": 754, "revenue": 67850, "percentage": 20, "color": "#FF7D00", "growth": 8.7},
        {"platform": "快手", "orders": 632, "revenue": 58790, "percentage": 20, "color": "#722ED1", "growth": 15.4},
    ]


def _top_products():
    """热销商品 TOP 8"""
    return [
        {"name": "蓝牙耳机Pro Max", "sales": 523, "revenue": 156900, "trend": 18.5, "platform": "抖音"},
        {"name": "智能手表S3", "sales": 412, "revenue": 123600, "trend": 12.3, "platform": "拼多多"},
        {"name": "充电宝20000mAh", "sales": 389, "revenue": 77800, "trend": -3.2, "platform": "闲鱼"},
        {"name": "手机支架磁吸款", "sales": 356, "revenue": 35600, "trend": 25.1, "platform": "快手"},
        {"name": "降噪耳机TWS", "sales": 298, "revenue": 119200, "trend": 8.7, "platform": "抖音"},
        {"name": "数据线三合一", "sales": 678, "revenue": 20340, "trend": -1.5, "platform": "拼多多"},
        {"name": "无线充电器15W", "sales": 245, "revenue": 49000, "trend": 32.4, "platform": "抖音"},
        {"name": "手机壳防摔款", "sales": 534, "revenue": 16020, "trend": 5.3, "platform": "闲鱼"},
    ]


def _funnel_data():
    """转化漏斗"""
    return [
        {"stage": "浏览", "count": 28560, "rate": 100},
        {"stage": "加购", "count": 8568, "rate": 30},
        {"stage": "下单", "count": 3713, "rate": 13},
        {"stage": "支付", "count": 3142, "rate": 11},
        {"stage": "复购", "count": 943, "rate": 3.3},
    ]


def _realtime_orders():
    """实时订单（最近8条）"""
    now = datetime.now()
    templates = [
        {"id": "DD20260529001", "product": "蓝牙耳机Pro Max", "platform": "抖音", "amount": 299, "status": "paid", "minutes_ago": 2},
        {"id": "DD20260529002", "product": "智能手表S3", "platform": "拼多多", "amount": 459, "status": "paid", "minutes_ago": 5},
        {"id": "DD20260529003", "product": "充电宝20000mAh", "platform": "闲鱼", "amount": 129, "status": "pending", "minutes_ago": 8},
        {"id": "DD20260529004", "product": "手机支架磁吸款", "platform": "快手", "amount": 39.9, "status": "paid", "minutes_ago": 12},
        {"id": "DD20260529005", "product": "降噪耳机TWS", "platform": "抖音", "amount": 399, "status": "shipped", "minutes_ago": 15},
        {"id": "DD20260529006", "product": "数据线三合一", "platform": "拼多多", "amount": 19.9, "status": "paid", "minutes_ago": 18},
        {"id": "DD20260529007", "product": "无线充电器15W", "platform": "抖音", "amount": 89, "status": "paid", "minutes_ago": 22},
        {"id": "DD20260529008", "product": "手机壳防摔款", "platform": "闲鱼", "amount": 29.9, "status": "pending", "minutes_ago": 28},
    ]
    result = []
    for t in templates:
        result.append({
            "id": t["id"],
            "product": t["product"],
            "platform": t["platform"],
            "amount": t["amount"],
            "status": t["status"],
            "time": (now - timedelta(minutes=t["minutes_ago"])).isoformat(),
        })
    return result


def _alert_data():
    """预警信息"""
    return [
        {"id": 1, "type": "error", "title": "库存紧急", "content": "数据线三合一 库存仅剩2件，日均销量3件", "time": "5分钟前", "action": "补货"},
        {"id": 2, "type": "warning", "title": "退款申请", "content": "订单#DD20260527089 申请退款，金额¥459", "time": "18分钟前", "action": "处理"},
        {"id": 3, "type": "warning", "title": "差评预警", "content": '"蓝牙耳机Pro Max" 收到2条差评，均提及音质问题', "time": "42分钟前", "action": "回复"},
        {"id": 4, "type": "info", "title": "发货提醒", "content": "有23个订单已超过24小时未发货", "time": "1小时前", "action": "发货"},
        {"id": 5, "type": "info", "title": "价格变动", "content": '竞品"XX蓝牙耳机"降价15%，建议跟进', "time": "2小时前", "action": "查看"},
    ]


def _todo_data():
    """待办事项"""
    return [
        {"id": 1, "title": "待发货订单", "count": 23, "urgency": "high"},
        {"id": 2, "title": "待处理退款", "count": 5, "urgency": "high"},
        {"id": 3, "title": "待回复消息", "count": 12, "urgency": "medium"},
        {"id": 4, "title": "库存预警", "count": 7, "urgency": "medium"},
        {"id": 5, "title": "待审核商品", "count": 3, "urgency": "low"},
    ]


def _low_stock_items():
    """库存预警商品"""
    return [
        {"key": "1", "name": "蓝牙耳机A1", "platform": "抖音", "stock": 8, "dailySales": 2, "daysLeft": 4},
        {"key": "2", "name": "智能手表S2", "platform": "拼多多", "stock": 3, "dailySales": 1, "daysLeft": 3},
        {"key": "3", "name": "充电宝20000mAh", "platform": "闲鱼", "stock": 12, "dailySales": 3, "daysLeft": 4},
        {"key": "4", "name": "手机壳透明款", "platform": "快手", "stock": 5, "dailySales": 2, "daysLeft": 2},
        {"key": "5", "name": "数据线快充", "platform": "抖音", "stock": 2, "dailySales": 1, "daysLeft": 2},
        {"key": "6", "name": "降噪耳机TWS", "platform": "拼多多", "stock": 6, "dailySales": 2, "daysLeft": 3},
        {"key": "7", "name": "无线充电器", "platform": "快手", "stock": 4, "dailySales": 1, "daysLeft": 4},
    ]


# ============================================================
# 路由
# ============================================================

@router.get("/stats")
async def get_dashboard_stats():
    """
    获取 Dashboard 综合统计数据

    返回前端工作台所需全部数据:
    - platform_breakdown: 各平台经营数据
    - top_products: 热销商品 TOP 8
    - funnel: 转化漏斗
    - realtime_orders: 最近订单
    - alerts: 预警信息
    - todo_list: 待办事项
    - low_stock: 库存预警
    """
    return success_response(data={
        "platform_breakdown": _platform_breakdown(),
        "top_products": _top_products(),
        "funnel": _funnel_data(),
        "realtime_orders": _realtime_orders(),
        "alerts": _alert_data(),
        "todo_list": _todo_data(),
        "low_stock": _low_stock_items(),
        "updated_at": datetime.now().isoformat(),
    })


@router.get("/trend")
async def get_dashboard_trend(
    days: int = Query(7, ge=1, le=90, description="趋势天数，默认 7"),
):
    """
    获取 Dashboard 趋势数据

    参数:
        days: 回溯天数 (1-90)，默认 7

    返回:
        - daily: 每日 {date, revenue, orders, customers, profit}
        - summary: 汇总统计 {totalRevenue, totalOrders, ...}
        - prev_period: 上期对比数据
    """
    current_data = _generate_daily_series(days)

    # 汇总
    total_revenue = sum(d["revenue"] for d in current_data)
    total_orders = sum(d["orders"] for d in current_data)
    total_customers = sum(d["customers"] for d in current_data)
    total_profit = sum(d["profit"] for d in current_data)
    avg_order_value = round(total_revenue / total_orders, 2) if total_orders else 0
    profit_margin = round(total_profit / total_revenue * 100, 2) if total_revenue else 0

    # 上期对比
    prev_end = datetime.now() - timedelta(days=days)
    prev_data = _generate_daily_series(days, prev_end)
    prev_revenue = sum(d["revenue"] for d in prev_data)
    prev_orders = sum(d["orders"] for d in prev_data)
    prev_customers = sum(d["customers"] for d in prev_data)
    prev_profit = sum(d["profit"] for d in prev_data)

    def _growth(current, previous):
        if previous == 0:
            return 0.0
        return round((current - previous) / previous * 100, 1)

    return success_response(data={
        "daily": current_data,
        "summary": {
            "totalRevenue": total_revenue,
            "totalOrders": total_orders,
            "totalCustomers": total_customers,
            "totalProfit": total_profit,
            "avgOrderValue": avg_order_value,
            "profitMargin": profit_margin,
        },
        "prev_period": {
            "totalRevenue": prev_revenue,
            "totalOrders": prev_orders,
            "totalCustomers": prev_customers,
            "totalProfit": prev_profit,
        },
        "growth": {
            "revenue": _growth(total_revenue, prev_revenue),
            "orders": _growth(total_orders, prev_orders),
            "customers": _growth(total_customers, prev_customers),
            "profit": _growth(total_profit, prev_profit),
        },
    })
