"""
财务中心路由

提供交易流水、提现记录、对账数据、趋势统计。
使用内存存储 + 种子数据。
"""
from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime, timedelta
import random

from utils.responses import success_response

router = APIRouter()


def _generate_seed_data():
    """生成财务种子数据"""
    random.seed(42)
    now = datetime.now()

    # 交易流水
    transactions = []
    statuses = ['已完成', '处理中', '已退款']
    channels = ['支付宝', '微信支付', '银行卡', '平台结算']
    platforms = ['douyin', 'pdd', 'xianyu', 'kuaishou']
    for i in range(50):
        amount = round(random.uniform(50, 5000), 2)
        fee = round(amount * random.uniform(0.003, 0.015), 2)
        transactions.append({
            "id": f"TXN-{i+1:06d}",
            "orderId": f"ORD-{random.randint(100000, 999999)}",
            "platform": platforms[i % 4],
            "type": random.choice(['收入', '退款', '提现']),
            "amount": amount,
            "fee": fee,
            "net": round(amount - fee, 2),
            "channel": random.choice(channels),
            "status": statuses[0] if i < 40 else random.choice(statuses),
            "createdAt": (now - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))).isoformat(),
        })

    # 提现记录
    withdrawals = []
    for i in range(10):
        amount = round(random.uniform(1000, 50000), 2)
        withdrawals.append({
            "id": f"WD-{i+1:06d}",
            "amount": amount,
            "fee": round(amount * 0.001, 2),
            "bank": random.choice(['工商银行', '建设银行', '招商银行', '支付宝']),
            "account": f"****{random.randint(1000, 9999)}",
            "status": random.choice(['已到账', '处理中', '已提交']),
            "createdAt": (now - timedelta(days=random.randint(0, 15))).isoformat(),
        })

    # 对账数据
    reconciliations = []
    for i in range(8):
        reconciliations.append({
            "id": f"REC-{i+1:04d}",
            "period": f"2026-{5 - i // 2:02d} {(i % 2) * 15 + 1:02d}-{(i % 2) * 15 + 15:02d}",
            "platform": platforms[i % 4],
            "orderCount": random.randint(50, 500),
            "totalAmount": round(random.uniform(10000, 200000), 2),
            "settledAmount": round(random.uniform(9000, 190000), 2),
            "fee": round(random.uniform(100, 3000), 2),
            "status": random.choice(['已对账', '待对账', '有差异']),
            "createdAt": (now - timedelta(days=i * 3)).isoformat(),
        })

    # 趋势数据
    trend = []
    for i in range(30):
        date = (now - timedelta(days=29 - i)).strftime('%Y-%m-%d')
        revenue = round(random.uniform(5000, 50000), 2)
        cost = round(revenue * random.uniform(0.4, 0.7), 2)
        trend.append({
            "date": date,
            "revenue": revenue,
            "cost": cost,
            "profit": round(revenue - cost, 2),
            "orders": random.randint(20, 200),
        })

    random.seed()
    return transactions, withdrawals, reconciliations, trend


# 初始化种子数据
_transactions, _withdrawals, _reconciliations, _trend = _generate_seed_data()


@router.get("/stats")
async def get_finance_stats():
    """获取财务统计概览"""
    total_revenue = sum(t['amount'] for t in _transactions if t['type'] == '收入' and t['status'] == '已完成')
    total_refund = sum(t['amount'] for t in _transactions if t['type'] == '退款')
    total_fee = sum(t['fee'] for t in _transactions)
    pending_withdrawal = sum(w['amount'] for w in _withdrawals if w['status'] == '处理中')

    return success_response(data={
        "totalRevenue": round(total_revenue, 2),
        "totalRefund": round(total_refund, 2),
        "totalFee": round(total_fee, 2),
        "netIncome": round(total_revenue - total_refund - total_fee, 2),
        "pendingWithdrawal": round(pending_withdrawal, 2),
        "transactionCount": len(_transactions),
    })


@router.get("/transactions")
async def list_transactions(
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取交易流水"""
    items = _transactions.copy()
    if status:
        items = [t for t in items if t['status'] == status]
    if type:
        items = [t for t in items if t['type'] == type]

    total = len(items)
    start = (page - 1) * page_size
    paged = items[start:start + page_size]
    return success_response(data={"items": paged, "total": total})


@router.get("/withdrawals")
async def list_withdrawals(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取提现记录"""
    items = _withdrawals.copy()
    if status:
        items = [w for w in items if w['status'] == status]

    total = len(items)
    start = (page - 1) * page_size
    paged = items[start:start + page_size]
    return success_response(data={"items": paged, "total": total})


@router.get("/reconciliations")
async def list_reconciliations(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取对账数据"""
    items = _reconciliations.copy()
    if status:
        items = [r for r in items if r['status'] == status]

    total = len(items)
    start = (page - 1) * page_size
    paged = items[start:start + page_size]
    return success_response(data={"items": paged, "total": total})


@router.get("/trend")
async def get_finance_trend(days: int = Query(30, ge=1, le=90)):
    """获取财务趋势数据"""
    return success_response(data={"items": _trend[-days:]})
