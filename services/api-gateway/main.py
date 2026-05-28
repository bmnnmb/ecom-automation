"""
Hermes 多平台电商自动化系统 - API网关
统一入口，提供鉴权、路由转发、错误处理、请求追踪
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from loguru import logger
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入路由
from routes import shops, products, orders, messages, aftersales, competitors, reports, dashboard, settings
from routes.auth import oauth

# 导入统一错误处理和中间件
from utils.errors import setup_error_handlers
from utils.middleware import request_tracking_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 API网关启动中...")
    yield
    logger.info("🛑 API网关关闭")


# 创建FastAPI应用
app = FastAPI(
    title="Hermes 电商自动化 API",
    description="多平台电商自动化系统统一API网关",
    version="1.1.0",
    lifespan=lifespan,
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求追踪中间件（包含日志和 request_id 注入）
app.middleware("http")(request_tracking_middleware)

# ============================================================
# 注册统一异常处理器
# ============================================================
setup_error_handlers(app)

# ============================================================
# 注册路由
# ============================================================
app.include_router(oauth.router, prefix="/api/auth", tags=["统一鉴权管理"])
app.include_router(shops.router, prefix="/api/shops", tags=["店铺管理"])
app.include_router(products.router, prefix="/api/products", tags=["商品管理"])
app.include_router(orders.router, prefix="/api/orders", tags=["订单管理"])
app.include_router(messages.router, prefix="/api/messages", tags=["客服消息"])
app.include_router(aftersales.router, prefix="/api/aftersales", tags=["售后服务"])
app.include_router(competitors.router, prefix="/api/competitors", tags=["竞品分析"])
app.include_router(reports.router, prefix="/api/reports", tags=["报表统计"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["运营看板"])
app.include_router(settings.router, prefix="/api/settings", tags=["系统设置"])


# ============================================================
# 健康检查 & 根路径
# ============================================================
@app.get("/")
async def root():
    return {
        "service": "ecom-api-gateway",
        "version": "1.1.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ecom-api-gateway",
        "version": "1.1.0",
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
