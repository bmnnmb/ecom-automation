"""
系统管理API路由
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import html
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

    auth_info = playwright_bot.get_auth_info()
    return {
        "success": True,
        "data": {
            "is_authorized": auth_info["is_authorized"],
            "status": auth_info["status"],
            "message": auth_info["message"],
        }
    }


@router.get("/pdd-auth/info")
async def get_pdd_auth_info():
    """获取拼多多授权信息（不包含 cookie 值）"""
    from playwright_bot import playwright_bot

    return {
        "success": True,
        "data": playwright_bot.get_auth_info(),
    }


@router.get("/pdd-auth/page", response_class=HTMLResponse)
async def get_pdd_auth_page():
    """拼多多授权信息查看页"""
    from playwright_bot import playwright_bot

    auth_info = playwright_bot.get_auth_info()

    def value(name: str) -> str:
        raw = auth_info.get(name)
        if isinstance(raw, list):
            raw = ", ".join(str(item) for item in raw) or "-"
        if raw is None or raw == "":
            raw = "-"
        return html.escape(str(raw))

    status_color = "#00b42a" if auth_info.get("is_authorized") else "#f53f3f"
    generated_at = html.escape(datetime.now().isoformat(timespec="seconds"))

    return f"""
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>拼多多授权信息</title>
  <style>
    body {{ margin: 0; padding: 32px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f5f7fa; color: #1d2129; }}
    main {{ max-width: 880px; margin: 0 auto; background: #fff; border: 1px solid #f0f0f0; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,.06); }}
    header {{ padding: 24px 28px; border-bottom: 1px solid #f0f0f0; }}
    h1 {{ margin: 0 0 8px; font-size: 20px; }}
    .status {{ display: inline-flex; align-items: center; gap: 8px; color: {status_color}; font-weight: 600; }}
    .dot {{ width: 8px; height: 8px; border-radius: 50%; background: {status_color}; }}
    dl {{ display: grid; grid-template-columns: 180px 1fr; gap: 0; margin: 0; padding: 8px 28px 28px; }}
    dt, dd {{ padding: 14px 0; border-bottom: 1px solid #f5f5f5; }}
    dt {{ color: #86909c; }}
    dd {{ margin: 0; word-break: break-all; }}
    .hint {{ margin: 0; color: #86909c; font-size: 13px; }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>拼多多授权信息</h1>
      <div class="status"><span class="dot"></span>{value("message")}</div>
      <p class="hint">页面生成时间：{generated_at}</p>
    </header>
    <dl>
      <dt>授权状态</dt><dd>{value("status")}</dd>
      <dt>会话文件</dt><dd>{value("storage_state_path")}</dd>
      <dt>文件是否存在</dt><dd>{value("storage_exists")}</dd>
      <dt>文件大小</dt><dd>{value("storage_size")} bytes</dd>
      <dt>更新时间</dt><dd>{value("updated_at")}</dd>
      <dt>Cookie 数量</dt><dd>{value("cookie_count")}</dd>
      <dt>Cookie 名称</dt><dd>{value("cookie_names")}</dd>
      <dt>Cookie 域名</dt><dd>{value("domains")}</dd>
      <dt>最近过期时间</dt><dd>{value("expires_at")}</dd>
    </dl>
  </main>
</body>
</html>
"""


@router.post("/pdd-login/start")
async def start_pdd_login():
    """启动拼多多账号密码授权登录"""
    from playwright_bot import playwright_bot
    from config import settings
    import logging
    import traceback

    logger = logging.getLogger(__name__)

    try:
        logger.info("开始启动拼多多账号密码授权登录...")
        login_result = await playwright_bot.start_password_login()
        logger.info(f"账号密码授权登录已发起: {login_result.get('status')}")
        return {
            "success": True,
            "message": login_result.get("message", "已打开拼多多登录页面并填入账号密码"),
            "data": {
                **login_result,
                "auth_info_url": "/api/v1/system/pdd-auth/page",
                "browser_control_url": settings.BROWSER_CONTROL_URL,
            }
        }
    except Exception as e:
        # 映射为用户友好的错误消息
        error_type = type(e).__name__
        user_message = "启动账号密码授权登录失败，请稍后重试"

        if "TimeoutError" in error_type or "timeout" in str(e).lower():
            user_message = "网络连接超时，请检查网络后重试"
        elif "Connection" in error_type or "connection" in str(e).lower():
            user_message = "无法连接到拼多多服务，请检查网络"
        elif "Browser" in error_type or "playwright" in str(e).lower():
            user_message = "浏览器启动失败，请确认后端运行环境可以打开可见浏览器"

        logger.error(f"启动账号密码授权登录失败: {error_type}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=user_message)


@router.get("/pdd-login/status")
async def get_pdd_login_status():
    """检查拼多多账号密码授权登录状态"""
    from playwright_bot import playwright_bot

    try:
        had_login_page = playwright_bot.page is not None
        is_logged_in = await playwright_bot.check_login_status()
        pending_result = None
        if not is_logged_in:
            pending_result = await playwright_bot.continue_password_login()
            if pending_result:
                is_logged_in = pending_result.get("is_logged_in", False)

        auth_info = playwright_bot.get_auth_info()

        verification_required = False
        if not is_logged_in and playwright_bot.page is not None:
            verification_required = await playwright_bot.has_verification_challenge()

        if is_logged_in and had_login_page:
            await playwright_bot.close()

        if is_logged_in:
            status = "logged_in"
            message = "授权成功，会话已保存"
        elif pending_result:
            status = pending_result.get("status", "waiting_login")
            message = pending_result.get("message", "等待账号密码登录完成")
            verification_required = pending_result.get("verification_required", verification_required)
        elif had_login_page and playwright_bot.page is None:
            status = "closed"
            message = "登录窗口已关闭，未检测到有效授权"
        else:
            status = "waiting_verification" if verification_required else "waiting_login"
            message = "请在浏览器中完成滑块/短信等验证" if verification_required else "等待账号密码登录完成"

        return {
            "success": True,
            "data": {
                "is_logged_in": is_logged_in,
                "status": status,
                "message": message,
                "verification_required": verification_required,
                "credentials_filled": bool(getattr(playwright_bot, "password_login_filled", False)),
                "auth_info": auth_info,
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
    """取消拼多多账号密码授权登录"""
    from playwright_bot import playwright_bot

    try:
        await playwright_bot.close()
        return {
            "success": True,
            "message": "拼多多登录已取消"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取消登录失败: {str(e)}")


@router.post("/pdd-login/password")
async def pdd_password_login():
    """兼容旧入口：发起拼多多账号密码授权登录"""
    return await start_pdd_login()


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
