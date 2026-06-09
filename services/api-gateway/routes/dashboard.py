"""
Dashboard 运营看板路由 — 代理到 oms-service (端口 8005)

OMS 服务提供 /api/dashboard/stats 和 /api/dashboard/trend 端点，
聚合订单、商品、库存等子系统的统计结果。
"""
from utils.proxy import create_proxy_router, resolve_service_url

OMS_SERVICE_URL = resolve_service_url("OMS_DASHBOARD_URL", "http://localhost:8005/api/dashboard")

router = create_proxy_router(
    target_base=OMS_SERVICE_URL,
    service_name="oms-service",
)
