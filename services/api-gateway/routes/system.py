"""
系统管理路由

提供用户管理、角色管理、操作日志、通知管理。
使用内存存储 + 种子数据。
"""
from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime, timedelta
import random

from utils.responses import success_response

router = APIRouter()


def _generate_seed_data():
    """生成系统管理种子数据"""
    random.seed(42)
    now = datetime.now()

    # 角色
    roles = [
        {"id": "ROLE-001", "name": "超级管理员", "code": "super_admin", "description": "拥有系统全部权限", "userCount": 1, "permissions": ["*"], "createdAt": "2025-01-01"},
        {"id": "ROLE-002", "name": "运营主管", "code": "ops_manager", "description": "管理商品、订单、营销等运营模块", "userCount": 2, "permissions": ["products.*", "orders.*", "marketing.*", "customers.*", "analytics.view"], "createdAt": "2025-01-15"},
        {"id": "ROLE-003", "name": "客服专员", "code": "cs_agent", "description": "处理客户咨询和售后服务", "userCount": 3, "permissions": ["service.*", "aftersales.*", "customers.view"], "createdAt": "2025-02-01"},
        {"id": "ROLE-004", "name": "财务专员", "code": "finance", "description": "查看财务数据和处理结算", "userCount": 2, "permissions": ["finance.*", "orders.view"], "createdAt": "2025-02-15"},
        {"id": "ROLE-005", "name": "只读用户", "code": "viewer", "description": "仅可查看数据，无操作权限", "userCount": 5, "permissions": ["*.view"], "createdAt": "2025-03-01"},
    ]

    # 用户
    users = [
        {"id": "USR-001", "username": "admin", "name": "系统管理员", "email": "admin@ecom.com", "phone": "138****0001", "role": "超级管理员", "status": "active", "lastLogin": (now - timedelta(hours=2)).isoformat(), "createdAt": "2025-01-01"},
        {"id": "USR-002", "username": "zhangsan", "name": "张三", "email": "zhangsan@ecom.com", "phone": "138****0002", "role": "运营主管", "status": "active", "lastLogin": (now - timedelta(hours=5)).isoformat(), "createdAt": "2025-01-15"},
        {"id": "USR-003", "username": "lisi", "name": "李四", "email": "lisi@ecom.com", "phone": "138****0003", "role": "客服专员", "status": "active", "lastLogin": (now - timedelta(days=1)).isoformat(), "createdAt": "2025-02-01"},
        {"id": "USR-004", "username": "wangwu", "name": "王五", "email": "wangwu@ecom.com", "phone": "138****0004", "role": "财务专员", "status": "active", "lastLogin": (now - timedelta(days=3)).isoformat(), "createdAt": "2025-02-15"},
        {"id": "USR-005", "username": "zhaoliu", "name": "赵六", "email": "zhaoliu@ecom.com", "phone": "138****0005", "role": "只读用户", "status": "disabled", "lastLogin": (now - timedelta(days=30)).isoformat(), "createdAt": "2025-03-01"},
    ]

    # 操作日志
    logs = []
    actions = [
        ("登录系统", "用户管理"), ("修改商品价格", "商品管理"), ("发货订单", "订单管理"),
        ("创建优惠券", "营销管理"), ("回复客户消息", "客服管理"), ("导出财务报表", "财务管理"),
        ("调整库存", "供应链管理"), ("修改系统设置", "系统管理"), ("查看竞品分析", "竞品分析"),
        ("批量导入商品", "商品管理"),
    ]
    for i in range(50):
        action, module = actions[i % len(actions)]
        user = users[i % len(users)]
        logs.append({
            "id": f"LOG-{i+1:06d}",
            "userId": user["id"],
            "username": user["name"],
            "action": action,
            "module": module,
            "ip": f"192.168.1.{random.randint(100, 200)}",
            "createdAt": (now - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))).isoformat(),
        })

    # 通知
    notifications = [
        {"id": "NTF-001", "type": "warning", "title": "库存预警", "content": "数据线三合一 库存仅剩2件", "read": False, "createdAt": (now - timedelta(hours=1)).isoformat()},
        {"id": "NTF-002", "type": "info", "title": "系统更新", "content": "系统已升级到 v2.1.0 版本", "read": False, "createdAt": (now - timedelta(hours=3)).isoformat()},
        {"id": "NTF-003", "type": "success", "title": "对账完成", "content": "2026年5月上半月对账已完成", "read": True, "createdAt": (now - timedelta(days=1)).isoformat()},
        {"id": "NTF-004", "type": "error", "title": "API 异常", "content": "抖音平台 API 响应超时", "read": True, "createdAt": (now - timedelta(days=2)).isoformat()},
        {"id": "NTF-005", "type": "info", "title": "新功能上线", "content": "竞品分析功能已上线", "read": True, "createdAt": (now - timedelta(days=5)).isoformat()},
    ]

    random.seed()
    return roles, users, logs, notifications


_roles, _users, _logs, _notifications = _generate_seed_data()


@router.get("/stats")
async def get_system_stats():
    """获取系统统计"""
    active_users = sum(1 for u in _users if u['status'] == 'active')
    unread_notifications = sum(1 for n in _notifications if not n['read'])

    return success_response(data={
        "roleCount": len(_roles),
        "userCount": len(_users),
        "activeUsers": active_users,
        "logCount": len(_logs),
        "unreadNotifications": unread_notifications,
    })


@router.get("/roles")
async def list_roles():
    """获取角色列表"""
    return success_response(data={"items": _roles, "total": len(_roles)})


@router.get("/users")
async def list_users(
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取用户列表"""
    items = _users.copy()
    if status:
        items = [u for u in items if u['status'] == status]
    if keyword:
        kw = keyword.lower()
        items = [u for u in items if kw in u['name'].lower() or kw in u['username'].lower()]

    total = len(items)
    start = (page - 1) * page_size
    paged = items[start:start + page_size]
    return success_response(data={"items": paged, "total": total})


@router.get("/logs")
async def list_logs(
    module: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取操作日志"""
    items = _logs.copy()
    if module:
        items = [l for l in items if l['module'] == module]
    if keyword:
        kw = keyword.lower()
        items = [l for l in items if kw in l['action'].lower()]

    total = len(items)
    start = (page - 1) * page_size
    paged = items[start:start + page_size]
    return success_response(data={"items": paged, "total": total})


@router.get("/notifications")
async def list_notifications(
    read: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取通知列表"""
    items = _notifications.copy()
    if read is not None:
        items = [n for n in items if n['read'] == read]

    total = len(items)
    start = (page - 1) * page_size
    paged = items[start:start + page_size]
    return success_response(data={"items": paged, "total": total})
