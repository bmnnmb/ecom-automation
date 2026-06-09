"""
客户管理路由 — 代理到 product-service (端口 8006)

API 网关统一入口，将客户相关请求转发给独立的商品微服务。
开发环境 Vite 直连 8006，生产环境通过此路由代理。
"""
from utils.proxy import create_proxy_router, resolve_service_url

CUSTOMER_SERVICE_URL = resolve_service_url("PRODUCT_CUSTOMERS_URL", "http://localhost:8006/api/customers")

router = create_proxy_router(
    target_base=CUSTOMER_SERVICE_URL,
    service_name="product-service (customers)",
)
