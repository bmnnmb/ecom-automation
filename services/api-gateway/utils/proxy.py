"""
通用反向代理工具

API Gateway 使用此模块将请求透传到后端微服务。
每个路由模块只需声明目标服务 URL，代理逻辑由本模块统一处理。

用法:
    from utils.proxy import create_proxy_router

    router = create_proxy_router(
        target_base="http://oms-service:8005/api/orders",
        service_name="oms-service",
    )
"""
import os
from typing import Optional
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import httpx
from loguru import logger


def create_proxy_router(
    target_base: str,
    service_name: str,
    timeout: float = 30.0,
    strip_prefix: Optional[str] = None,
) -> APIRouter:
    """
    创建一个透传路由，将所有 HTTP 方法转发到 target_base。

    Args:
        target_base: 目标服务基础 URL (如 "http://oms-service:8005/api/orders")
        service_name: 服务名称，用于错误信息和日志
        timeout: HTTP 请求超时(秒)
        strip_prefix: 从请求路径中剥离的前缀 (如 "/api/orders")
    """
    router = APIRouter()

    async def _proxy(request: Request, path: str = ""):
        target = target_base.rstrip("/")
        if path:
            target += f"/{path}"
        if request.url.query:
            target += f"?{request.url.query}"

        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                body = await request.body()
                resp = await client.request(
                    method=request.method,
                    url=target,
                    headers={
                        k: v
                        for k, v in request.headers.items()
                        if k.lower() not in ("host", "content-length")
                    },
                    content=body if body else None,
                )
                # 透传响应
                content_type = resp.headers.get("content-type", "")
                if "application/json" in content_type:
                    return JSONResponse(
                        status_code=resp.status_code,
                        content=resp.json(),
                    )
                else:
                    return JSONResponse(
                        status_code=resp.status_code,
                        content={"detail": resp.text},
                    )
            except httpx.ConnectError:
                logger.warning(f"服务不可达: {service_name} ({target_base})")
                return JSONResponse(
                    status_code=503,
                    content={
                        "success": False,
                        "error": {
                            "code": "SERVICE_UNAVAILABLE",
                            "message": f"{service_name} 服务不可用，请确认服务已启动",
                        },
                    },
                )
            except httpx.TimeoutException:
                logger.warning(f"请求超时: {service_name} -> {target}")
                return JSONResponse(
                    status_code=504,
                    content={
                        "success": False,
                        "error": {
                            "code": "TIMEOUT",
                            "message": f"{service_name} 请求超时",
                        },
                    },
                )
            except Exception as e:
                logger.error(f"代理异常: {service_name} -> {e}")
                return JSONResponse(
                    status_code=502,
                    content={
                        "success": False,
                        "error": {
                            "code": "PROXY_ERROR",
                            "message": f"代理请求失败: {str(e)}",
                        },
                    },
                )

    @router.api_route("/", methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
    async def proxy_root(request: Request):
        return await _proxy(request)

    @router.api_route("/{path:path}", methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
    async def proxy_subpath(request: Request, path: str):
        return await _proxy(request, path)

    return router


def resolve_service_url(env_key: str, default_url: str) -> str:
    """从环境变量解析服务 URL，不存在则使用默认值"""
    return os.getenv(env_key, default_url)
