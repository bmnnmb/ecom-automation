"""
工单管理路由 — 代理到 oms-service (端口 8005)

OMS 服务提供 /api/tickets 的工单创建、流转、处理等功能。
"""
from utils.proxy import create_proxy_router, resolve_service_url

OMS_SERVICE_URL = resolve_service_url("OMS_TICKETS_URL", "http://localhost:8005/api/tickets")

router = create_proxy_router(
    target_base=OMS_SERVICE_URL,
    service_name="oms-service",
)
