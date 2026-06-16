"""
抖音平台授权API路由
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# 使用请求级别的Bot实例，而不是全局单例
_active_bot = None


def get_bot():
    """获取或创建Bot实例"""
    global _active_bot
    if _active_bot is None:
        from douyin_bot import DouyinBot
        _active_bot = DouyinBot()
    return _active_bot


@router.post("/douyin-login/start")
async def start_douyin_login():
    """启动抖音扫码登录"""
    import traceback
    try:
        logger.info("开始启动抖音扫码登录...")
        bot = get_bot()
        screenshot_path = await bot.start_qr_login()
        logger.info(f"抖音二维码生成成功: {screenshot_path}")
        return {
            "success": True,
            "message": "请使用抖音APP扫描二维码完成登录",
            "data": {
                "screenshot_url": "/api/v1/system/douyin-login/screenshot",
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
            user_message = "无法连接到抖音服务，请检查网络"
        elif "Browser" in error_type or "playwright" in str(e).lower():
            user_message = "浏览器启动失败，请联系管理员"

        logger.error(f"启动抖音扫码登录失败: {error_type}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=user_message)


@router.get("/douyin-login/screenshot")
async def get_douyin_login_screenshot():
    """获取抖音二维码截图"""
    bot = get_bot()
    path = bot.login_screenshot_path
    if not path.exists():
        raise HTTPException(status_code=404, detail="登录二维码截图不存在")
    return FileResponse(str(path), media_type="image/png")


@router.get("/douyin-login/status")
async def get_douyin_login_status():
    """检查抖音扫码登录状态"""
    try:
        bot = get_bot()
        is_logged_in = await bot.check_login_status()
        return {
            "success": True,
            "data": {
                "is_logged_in": is_logged_in,
                "status": "logged_in" if is_logged_in else "waiting_scan",
                "message": "已登录" if is_logged_in else "等待扫码确认"
            }
        }
    except Exception as e:
        logger.error(f"检查抖音登录状态失败: {e}", exc_info=True)
        return {
            "success": False,
            "data": {
                "is_logged_in": False,
                "status": "failed",
                "message": f"检查登录状态失败: {str(e)}"
            }
        }


@router.post("/douyin-login/cancel")
async def cancel_douyin_login():
    """取消抖音扫码登录"""
    global _active_bot
    try:
        if _active_bot:
            await _active_bot.close()
            _active_bot = None
        return {
            "success": True,
            "message": "扫码登录已取消"
        }
    except Exception as e:
        logger.error(f"取消抖音登录失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"取消登录失败: {str(e)}")


@router.get("/douyin-login/shop-info")
async def get_douyin_shop_info():
    """获取抖音店铺信息"""
    bot = get_bot()
    if not bot.is_logged_in:
        raise HTTPException(status_code=401, detail="未登录")

    try:
        shop_info = await bot.get_shop_info()
        return {
            "success": True,
            "data": shop_info
        }
    except Exception as e:
        logger.error(f"获取抖音店铺信息失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取店铺信息失败: {str(e)}")


@router.post("/douyin-logout")
async def douyin_logout():
    """抖音登出"""
    global _active_bot
    try:
        bot = get_bot()
        # 关闭浏览器
        await bot.close()
        _active_bot = None

        # 删除会话文件
        if bot.storage_state_path.exists():
            bot.storage_state_path.unlink()
            logger.info(f"已删除会话文件: {bot.storage_state_path}")

        return {
            "success": True,
            "message": "抖音授权已解绑"
        }
    except Exception as e:
        logger.error(f"抖音登出失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"登出失败: {str(e)}")
