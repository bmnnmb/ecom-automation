"""
库存管理路由 — 代理到 oms-service (端口 8005)

OMS 服务提供 /api/inventory 的库存查询、盘点、预警等功能。
"""
from utils.proxy import create_proxy_router, resolve_service_url

OMS_SERVICE_URL = resolve_service_url("OMS_INVENTORY_URL", "http://localhost:8005/api/inventory")

router = create_proxy_router(
    target_base=OMS_SERVICE_URL,
    service_name="oms-service",
)
