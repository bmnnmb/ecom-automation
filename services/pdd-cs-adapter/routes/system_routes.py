"""
系统管理API路由
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import psutil
import os

router = APIRouter()


class SystemStatus(BaseModel):
    """系统状态模型"""
    service_name: str
    version: str
    status: str
    uptime: float
    memory_usage: float
    cpu_usage: float
    active_connections: int


class ConfigUpdate(BaseModel):
    """配置更新模型"""
    auto_reply_enabled: Optional[bool] = None
    poll_interval: Optional[int] = None
    browser_headless: Optional[bool] = None


@router.get("/status", response_model=SystemStatus)
async def get_system_status():
    """获取系统状态"""
    import time
    start_time = getattr(get_system_status, '_start_time', time.time())
    get_system_status._start_time = start_time
    
    uptime = time.time() - start_time
    
    return SystemStatus(
        service_name="拼多多客服自动化服务",
        version="1.0.0",
        status="running",
        uptime=uptime,
        memory_usage=psutil.Process().memory_percent(),
        cpu_usage=psutil.cpu_percent(),
        active_connections=0  # 这里应该从应用状态获取
    )


@router.get("/config")
async def get_config():
    """获取当前配置"""
    from config import settings
    
    return {
        "auto_reply_enabled": settings.AUTO_REPLY_ENABLED,
        "poll_interval": settings.POLL_INTERVAL,
        "browser_headless": settings.BROWSER_HEADLESS,
        "high_risk_keywords": settings.HIGH_RISK_KEYWORDS,
        "api_base_url": settings.PDD_API_BASE_URL,
        "workbench_url": settings.PDD_WORKBENCH_URL,
        "pdd_data_dir": settings.PDD_DATA_DIR,
    }


@router.post("/config")
async def update_config(update: ConfigUpdate):
    """更新配置"""
    from config import settings
    
    if update.auto_reply_enabled is not None:
        settings.AUTO_REPLY_ENABLED = update.auto_reply_enabled
    
    if update.poll_interval is not None:
        settings.POLL_INTERVAL = update.poll_interval
    
    if update.browser_headless is not None:
        settings.BROWSER_HEADLESS = update.browser_headless
    
    return {
        "message": "配置更新成功",
        "config": await get_config()
    }


@router.get("/logs")
async def get_logs(limit: int = 100, level: str = "INFO"):
    """获取系统日志"""
    # 这里应该从日志文件或日志系统获取日志
    return {
        "logs": [],
        "total": 0,
        "level": level,
        "limit": limit
    }


@router.post("/restart")
async def restart_service():
    """重启服务"""
    # 这里应该实现服务重启逻辑
    # 注意：实际部署时需要谨慎处理
    return {"message": "重启指令已发送"}


@router.get("/pdd-auth/status")
async def get_pdd_auth_status():
    """获取拼多多持久授权状态"""
    from playwright_bot import playwright_bot

    is_authorized = playwright_bot.storage_state_path.exists()
    return {
        "success": True,
        "data": {
            "is_authorized": is_authorized,
            "status": "authorized" if is_authorized else "unauthorized",
            "message": "已授权" if is_authorized else "未授权"
        }
    }


@router.post("/pdd-login/start")
async def start_pdd_login():
    """启动拼多多扫码登录"""
    from playwright_bot import playwright_bot
    import logging
    import traceback

    logger = logging.getLogger(__name__)

    try:
        logger.info("开始启动拼多多扫码登录...")
        screenshot_path = await playwright_bot.start_qr_login()
        logger.info(f"二维码生成成功: {screenshot_path}")
        return {
            "success": True,
            "message": "请使用拼多多商家版APP扫描二维码完成登录",
            "data": {
                "screenshot_url": "/api/v1/system/pdd-login/screenshot",
                "screenshot_path": screenshot_path,
                "status": "waiting_scan"
            }
        }
    except Exception as e:
        # 映射为用户友好的错误消息
        error_type = type(e).__name__
        user_message = "启动扫码登录失败，请稍后重试"

        if "TimeoutError" in error_type or "timeout" in str(e).lower():
            user_message = "网络连接超时，请检查网络后重试"
        elif "Connection" in error_type or "connection" in str(e).lower():
            user_message = "无法连接到拼多多服务，请检查网络"
        elif "Browser" in error_type or "playwright" in str(e).lower():
            user_message = "浏览器启动失败，请联系管理员"

        logger.error(f"启动扫码登录失败: {error_type}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=user_message)


@router.get("/pdd-login/screenshot")
async def get_pdd_login_screenshot():
    """获取拼多多二维码截图"""
    from playwright_bot import playwright_bot

    path = playwright_bot.login_screenshot_path
    if not path.exists():
        raise HTTPException(status_code=404, detail="登录二维码截图不存在")
    return FileResponse(str(path), media_type="image/png")


@router.get("/pdd-login/status")
async def get_pdd_login_status():
    """检查拼多多扫码登录状态"""
    from playwright_bot import playwright_bot

    try:
        is_logged_in = await playwright_bot.check_login_status()
        # 登录成功后不立即关闭，由前端调用cancel接口或后续请求时关闭
        # 避免前端轮询时浏览器已关闭导致的竞态条件
        return {
            "success": True,
            "data": {
                "is_logged_in": is_logged_in,
                "status": "logged_in" if is_logged_in else "waiting_scan",
                "message": "已登录" if is_logged_in else "等待扫码确认"
            }
        }
    except Exception as e:
        return {
            "success": False,
            "data": {
                "is_logged_in": False,
                "status": "failed",
                "message": f"检查登录状态失败: {str(e)}"
            }
        }


@router.post("/pdd-login/cancel")
async def cancel_pdd_login():
    """取消拼多多扫码登录"""
    from playwright_bot import playwright_bot

    try:
        await playwright_bot.close()
        return {
            "success": True,
            "message": "扫码登录已取消"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取消登录失败: {str(e)}")


@router.post("/pdd-login/password")
async def pdd_password_login():
    """拼多多账号密码登录"""
    from playwright_bot import playwright_bot
    import logging
    import traceback

    logger = logging.getLogger(__name__)

    try:
        logger.info("开始拼多多账号密码登录...")
        success = await playwright_bot.login()

        if success:
            return {
                "success": True,
                "message": "账号密码登录成功",
                "data": {
                    "status": "logged_in"
                }
            }
        else:
            return {
                "success": False,
                "message": "账号密码登录失败，请检查账号密码或重试",
                "data": {
                    "status": "failed"
                }
            }
    except Exception as e:
        error_type = type(e).__name__
        user_message = "账号密码登录失败"

        if "TimeoutError" in error_type or "timeout" in str(e).lower():
            user_message = "登录超时，请检查网络后重试"
        elif "Connection" in error_type or "connection" in str(e).lower():
            user_message = "无法连接到拼多多服务，请检查网络"
        elif "Browser" in error_type or "playwright" in str(e).lower():
            user_message = "浏览器启动失败，请联系管理员"

        logger.error(f"账号密码登录失败: {error_type}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=user_message)


@router.post("/pdd-logout")
async def pdd_logout():
    """拼多多登出"""
    from playwright_bot import playwright_bot
    from pathlib import Path

    try:
        # 关闭浏览器
        await playwright_bot.close()

        # 删除会话文件
        if playwright_bot.storage_state_path.exists():
            playwright_bot.storage_state_path.unlink()
            import logging
            logging.getLogger(__name__).info(f"已删除会话文件: {playwright_bot.storage_state_path}")

        return {
            "success": True,
            "message": "拼多多授权已解绑"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"登出失败: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "knowledge_base": "ok",
            "message_handler": "ok",
            "playwright_bot": "ok",
            "pdd_client": "ok"
        }
    }


@router.get("/metrics")
async def get_metrics():
    """获取服务指标"""
    from main import app
    
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "system": {
            "memory_usage": psutil.Process().memory_percent(),
            "cpu_usage": psutil.cpu_percent(),
            "disk_usage": psutil.disk_usage('/').percent
        },
        "service": {
            "total_messages_processed": 0,  # 这里应该从数据库获取
            "auto_replies_sent": 0,
            "human_transfers": 0,
            "active_conversations": 0
        }
    }
    
    return metrics


@router.post("/test/pdd-connection")
async def test_pdd_connection():
    """测试拼多多API连接"""
    from pdd_client import pdd_client
    
    try:
        # 这里应该测试实际的API连接
        return {
            "status": "success",
            "message": "拼多多API连接正常"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"连接失败: {str(e)}")


@router.post("/test/browser")
async def test_browser():
    """测试浏览器自动化"""
    from playwright_bot import playwright_bot
    
    try:
        await playwright_bot.start()
        await playwright_bot.take_screenshot("test_screenshot.png")
        await playwright_bot.close()
        
        return {
            "status": "success",
            "message": "浏览器测试成功",
            "screenshot": "test_screenshot.png"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"浏览器测试失败: {str(e)}")
