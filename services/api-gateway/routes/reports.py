"""
报表统计路由

使用统一错误处理和标准化响应格式。
"""
from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime, timedelta

from utils.responses import success_response

router = APIRouter()


@router.get("/daily")
async def daily_report(
    platform: Optional[str] = Query(None, description="按平台筛选"),
    date: Optional[str] = Query(None, description="日期 YYYY-MM-DD，默认今天"),
):
    """获取日报数据"""
    target_date = date or datetime.now().strftime("%Y-%m-%d")

    # 模拟日报数据
    report = {
        "date": target_date,
        "platform": platform or "all",
        "summary": {
            "total_orders": 0,
            "total_revenue": 0.0,
            "total_customers": 0,
            "new_customers": 0,
            "returning_customers": 0,
        },
        "by_platform": [],
        "top_products": [],
        "aftersale_stats": {
            "pending": 0,
            "completed": 0,
            "refund_amount": 0.0,
        },
    }

    return success_response(data=report)


@router.get("/weekly")
async def weekly_report(
    platform: Optional[str] = Query(None, description="按平台筛选"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
):
    """获取周报数据"""
    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
    else:
        today = datetime.now()
        start = today - timedelta(days=today.weekday())

    end = start + timedelta(days=6)

    report = {
        "period": {
            "start": start.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d"),
        },
        "platform": platform or "all",
        "summary": {
            "total_orders": 0,
            "total_revenue": 0.0,
            "avg_daily_orders": 0.0,
            "avg_daily_revenue": 0.0,
            "growth_rate": 0.0,
        },
        "daily_breakdown": [],
        "category_breakdown": [],
        "comparison": {
            "previous_week_orders": 0,
            "previous_week_revenue": 0.0,
            "order_growth": 0.0,
            "revenue_growth": 0.0,
        },
    }

    return success_response(data=report)


@router.get("/monthly")
async def monthly_report(
    platform: Optional[str] = Query(None, description="按平台筛选"),
    year: Optional[int] = Query(None, description="年份"),
    month: Optional[int] = Query(None, description="月份"),
):
    """获取月报数据"""
    now = datetime.now()
    target_year = year or now.year
    target_month = month or now.month

    if target_month < 1 or target_month > 12:
        from utils.errors import ValidationError
        raise ValidationError(
            message=f"无效的月份: {target_month}",
            detail="月份必须在 1-12 之间",
        )

    report = {
        "period": {
            "year": target_year,
            "month": target_month,
        },
        "platform": platform or "all",
        "summary": {
            "total_orders": 0,
            "total_revenue": 0.0,
            "total_customers": 0,
            "avg_order_value": 0.0,
        },
        "weekly_breakdown": [],
        "top_categories": [],
        "customer_analysis": {
            "new_customers": 0,
            "returning_customers": 0,
            "churn_rate": 0.0,
        },
    }

    return success_response(data=report)
