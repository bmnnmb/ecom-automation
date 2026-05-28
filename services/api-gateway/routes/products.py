"""
商品管理路由 — 代理到 product-service (端口 8006)

API 网关统一入口，将商品相关请求转发给独立的商品微服务。
开发环境 Vite 直连 8006，生产环境通过此路由代理。
"""
import os
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8006")


async def _proxy(request: Request, path: str = ""):
    """将请求代理到 product-service"""
    target = f"{PRODUCT_SERVICE_URL}/api/products"
    if path:
        target += f"/{path}"
    if request.url.query:
        target += f"?{request.url.query}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            body = await request.body()
            resp = await client.request(
                method=request.method,
                url=target,
                headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
                content=body if body else None,
            )
            return JSONResponse(
                status_code=resp.status_code,
                content=resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"detail": resp.text},
            )
        except httpx.ConnectError:
            return JSONResponse(
                status_code=503,
                content={"success": False, "detail": "商品服务不可用，请确认 product-service 已启动 (端口 8006)"},
            )
        except Exception as e:
            return JSONResponse(
                status_code=502,
                content={"success": False, "detail": f"代理请求失败: {str(e)}"},
            )


@router.api_route("/", methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
async def proxy_root(request: Request):
    """代理 /api/products 根路径"""
    return await _proxy(request)


@router.api_route("/{path:path}", methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
async def proxy_subpath(request: Request, path: str):
    """代理 /api/products/{path} 子路径"""
    return await _proxy(request, path)
