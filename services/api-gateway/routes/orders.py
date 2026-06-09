"""
订单管理路由 — 代理到 oms-service (端口 8005)

API 网关统一入口，将订单相关请求转发给 OMS 订单中台服务。
OMS 服务提供完整的订单 CRUD、状态机流转、发货/退款等业务逻辑。
"""
from utils.proxy import create_proxy_router, resolve_service_url

OMS_SERVICE_URL = resolve_service_url("OMS_ORDERS_URL", "http://localhost:8005/api/orders")

router = create_proxy_router(
    target_base=OMS_SERVICE_URL,
    service_name="oms-service",
)
