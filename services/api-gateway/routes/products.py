"""
商品管理路由 — 代理到 product-service (端口 8006)

API 网关统一入口，将商品相关请求转发给独立的商品微服务。
开发环境 Vite 直连 8006，生产环境通过此路由代理。
"""
from utils.proxy import create_proxy_router, resolve_service_url

PRODUCT_SERVICE_URL = resolve_service_url("PRODUCT_SERVICE_URL", "http://product-service:8006/api/products")

router = create_proxy_router(
    target_base=PRODUCT_SERVICE_URL,
    service_name="product-service",
)
