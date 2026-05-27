"""
请求追踪中间件

为每个请求生成唯一的 request_id，并注入到 request.state 中。
响应头中也会包含 X-Request-ID，方便日志追踪和前端排查。
"""
import uuid
import time
from fastapi import Request
from loguru import logger


async def request_tracking_middleware(request: Request, call_next):
    """请求追踪 + 日志中间件"""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000

    response.headers["X-Request-ID"] = request_id

    # 慢请求告警 (>2s)
    if duration_ms > 2000:
        logger.warning(
            f"⚡ SLOW {request.method} {request.url.path} "
            f"took {duration_ms:.0f}ms | request_id={request_id}"
        )

    logger.info(
        f"{request.method} {request.url.path} "
        f"status={response.status_code} "
        f"duration={duration_ms:.1f}ms "
        f"| request_id={request_id}"
    )
    return response
