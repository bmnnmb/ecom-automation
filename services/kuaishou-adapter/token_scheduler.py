"""
快手OAuth Token自动刷新调度器
后台定时检查token状态，提前刷新即将过期的token
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger


class TokenRefreshScheduler:
    """Token自动刷新调度器
    
    功能：
    1. 后台定时检查token是否即将过期
    2. 提前30分钟自动刷新token
    3. 刷新失败时指数退避重试（最多3次）
    4. 记录刷新历史和状态
    """
    
    # 刷新提前量：token过期前30分钟刷新
    REFRESH_AHEAD_MINUTES = 30
    # 检查间隔：每5分钟检查一次
    CHECK_INTERVAL_SECONDS = 300
    # 重试配置
    MAX_RETRIES = 3
    RETRY_BASE_DELAY = 10  # 秒
    
    def __init__(self, auth_manager):
        """
        Args:
            auth_manager: KuaishouAuthManager实例
        """
        self.auth_manager = auth_manager
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._last_refresh_time: Optional[datetime] = None
        self._last_refresh_success: Optional[bool] = None
        self._consecutive_failures: int = 0
        self._total_refreshes: int = 0
        self._total_failures: int = 0
    
    async def start(self):
        """启动调度器"""
        if self._running:
            logger.warning("Token刷新调度器已在运行")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info(
            f"Token刷新调度器已启动 "
            f"(检查间隔={self.CHECK_INTERVAL_SECONDS}s, "
            f"提前刷新={self.REFRESH_AHEAD_MINUTES}min)"
        )
    
    async def stop(self):
        """停止调度器"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Token刷新调度器已停止")
    
    async def _scheduler_loop(self):
        """调度器主循环"""
        logger.info("Token刷新调度器循环开始")
        
        while self._running:
            try:
                await self._check_and_refresh()
                await asyncio.sleep(self.CHECK_INTERVAL_SECONDS)
            except asyncio.CancelledError:
                logger.info("Token刷新调度器循环被取消")
                break
            except Exception as e:
                logger.error(f"Token刷新调度器异常: {e}")
                # 异常后短暂等待再重试
                await asyncio.sleep(30)
    
    async def _check_and_refresh(self):
        """检查token状态并在需要时刷新"""
        config = self.auth_manager.config
        
        # 没有token时跳过
        if not config.access_token:
            logger.debug("无access_token，跳过检查")
            return
        
        # 没有refresh_token时跳过
        if not config.refresh_token:
            logger.debug("无refresh_token，跳过检查")
            return
        
        # 检查是否即将过期
        if config.token_expires_at:
            time_until_expiry = config.token_expires_at - datetime.now()
            minutes_until_expiry = time_until_expiry.total_seconds() / 60
            
            if minutes_until_expiry > self.REFRESH_AHEAD_MINUTES:
                logger.debug(
                    f"Token还有{minutes_until_expiry:.1f}分钟过期，暂不刷新"
                )
                return
            
            logger.info(
                f"Token将在{minutes_until_expiry:.1f}分钟后过期，开始自动刷新"
            )
        else:
            # 没有过期时间信息，尝试刷新
            logger.info("Token过期时间未知，尝试刷新")
        
        # 执行刷新（带重试）
        await self._refresh_with_retry()
    
    async def _refresh_with_retry(self):
        """带重试的token刷新"""
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                logger.info(f"尝试刷新token (第{attempt}次)...")
                result = await self.auth_manager.refresh_access_token()
                
                # 刷新成功
                self._last_refresh_time = datetime.now()
                self._last_refresh_success = True
                self._consecutive_failures = 0
                self._total_refreshes += 1
                
                new_expires_in = result.get("expires_in", "未知")
                logger.info(
                    f"Token自动刷新成功 (expires_in={new_expires_in}s, "
                    f"总刷新次数={self._total_refreshes})"
                )
                return
                
            except Exception as e:
                logger.warning(f"Token刷新失败 (第{attempt}次): {e}")
                
                if attempt < self.MAX_RETRIES:
                    # 指数退避
                    delay = self.RETRY_BASE_DELAY * (2 ** (attempt - 1))
                    logger.info(f"等待{delay}秒后重试...")
                    await asyncio.sleep(delay)
        
        # 所有重试都失败
        self._last_refresh_time = datetime.now()
        self._last_refresh_success = False
        self._consecutive_failures += 1
        self._total_failures += 1
        self._total_refreshes += 1
        
        logger.error(
            f"Token自动刷新失败（已重试{self.MAX_RETRIES}次），"
            f"连续失败{self._consecutive_failures}次，"
            f"将在下次检查时重试"
        )
    
    async def force_refresh(self) -> bool:
        """强制立即刷新token
        
        Returns:
            是否刷新成功
        """
        logger.info("强制刷新token...")
        await self._refresh_with_retry()
        return self._last_refresh_success or False
    
    def get_status(self) -> dict:
        """获取调度器状态"""
        config = self.auth_manager.config
        
        token_expires_in = None
        if config.token_expires_at:
            delta = config.token_expires_at - datetime.now()
            token_expires_in = max(0, int(delta.total_seconds()))
        
        return {
            "running": self._running,
            "check_interval_seconds": self.CHECK_INTERVAL_SECONDS,
            "refresh_ahead_minutes": self.REFRESH_AHEAD_MINUTES,
            "token_expires_in_seconds": token_expires_in,
            "has_access_token": bool(config.access_token),
            "has_refresh_token": bool(config.refresh_token),
            "last_refresh_time": self._last_refresh_time.isoformat() if self._last_refresh_time else None,
            "last_refresh_success": self._last_refresh_success,
            "consecutive_failures": self._consecutive_failures,
            "total_refreshes": self._total_refreshes,
            "total_failures": self._total_failures,
        }


# 全局调度器实例
_scheduler: Optional[TokenRefreshScheduler] = None


def get_token_scheduler() -> Optional[TokenRefreshScheduler]:
    """获取token调度器实例"""
    return _scheduler


def init_token_scheduler(auth_manager) -> TokenRefreshScheduler:
    """初始化token调度器"""
    global _scheduler
    _scheduler = TokenRefreshScheduler(auth_manager)
    return _scheduler
