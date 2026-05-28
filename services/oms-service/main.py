"""
OMS订单中台服务 - FastAPI主入口

提供统一的订单管理、库存管理、工单管理和运营看板功能。
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import uvicorn
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger("oms-service")
logger.setLevel(logging.INFO)
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(_handler)

from pydantic_models import Order, OrderStatus, Platform, InventoryItem, Ticket, TicketStatus
from order_manager import OrderManager
from inventory_manager import InventoryManager
from ticket_manager import TicketManager
from routes import order_router, inventory_router, ticket_router, dashboard_router
from database import DATABASE_URL, init_db


# ============================================================
# 全局管理器实例
# ============================================================
order_manager = OrderManager()
inventory_manager = InventoryManager()
ticket_manager = TicketManager()


# ============================================================
# 统一错误处理
# ============================================================

class OmsError(Exception):
    """OMS业务异常基类"""
    def __init__(self, code: int = 500, message: str = "内部服务错误", detail=None):
        self.code = code
        self.message = message
        self.detail = detail
        super().__init__(message)


class NotFoundError(OmsError):
    """资源不存在"""
    def __init__(self, resource: str = "资源", resource_id: Optional[str] = None):
        message = f"{resource}不存在"
        if resource_id:
            message = f"{resource} '{resource_id}' 不存在"
        super().__init__(code=404, message=message)


class ValidationError(OmsError):
    """参数验证失败"""
    def __init__(self, message: str = "请求参数验证失败", detail=None):
        super().__init__(code=422, message=message, detail=detail)


# ============================================================
# 应用生命周期
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 OMS订单中台服务启动中...")
    logger.info(f"📦 数据库: {DATABASE_URL}")
    init_db()
    logger.info("✅ 数据库表已初始化")
    logger.info("✅ OMS订单中台服务启动完成 — http://0.0.0.0:8005")
    yield
    logger.info("🛑 OMS订单中台服务关闭中...")
    logger.info("✅ OMS订单中台服务已关闭")


# ============================================================
# FastAPI应用
# ============================================================

app = FastAPI(
    title="OMS订单中台服务",
    description="电商订单管理系统中台，提供多平台订单汇总、库存管理、工单处理等功能",
    version="1.1.0",
    lifespan=lifespan,
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# 异常处理器
# ============================================================

@app.exception_handler(OmsError)
async def oms_error_handler(request: Request, exc: OmsError):
    """处理OMS业务异常"""
    logger.warning(f"OMS Error: [{exc.code}] {exc.message} | path={request.url.path}")
    body = {"success": False, "error": {"code": exc.code, "message": exc.message}}
    if exc.detail:
        body["error"]["detail"] = exc.detail
    return JSONResponse(status_code=exc.code, content=body)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """处理请求参数验证异常"""
    errors = exc.errors()
    first = errors[0] if errors else {}
    loc = " -> ".join(str(x) for x in first.get("loc", []))
    msg = first.get("msg", "参数格式错误")
    detail_msg = f"字段 '{loc}': {msg}" if loc else msg
    logger.warning(f"Validation Error: {detail_msg} | path={request.url.path}")
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {"code": 422, "message": "请求参数验证失败", "detail": detail_msg},
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """处理未预期的异常"""
    logger.error(f"Unhandled exception: {type(exc).__name__}: {exc} | path={request.url.path}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {"code": 500, "message": "服务内部错误，请稍后重试"},
        },
    )


# ============================================================
# 注册路由
# ============================================================
app.include_router(order_router, prefix="/api/orders", tags=["订单管理"])
app.include_router(inventory_router, prefix="/api/inventory", tags=["库存管理"])
app.include_router(ticket_router, prefix="/api/tickets", tags=["工单管理"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["运营看板"])


# ============================================================
# 健康检查
# ============================================================

@app.get("/", tags=["健康检查"])
async def root():
    """根路径"""
    return {
        "service": "OMS订单中台服务",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": "1.1.0",
    }


@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "service": "oms-service", "version": "1.1.0"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8005,
        reload=True,
        log_level="info",
    )
