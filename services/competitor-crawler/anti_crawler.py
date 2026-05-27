"""
反爬虫策略模块
提供请求限速、代理轮换、UA管理、重试退避等反爬能力
"""
import asyncio
import random
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from loguru import logger


@dataclass
class RateLimitConfig:
    """限速配置"""
    requests_per_minute: int = 20        # 每分钟最大请求数
    requests_per_hour: int = 300         # 每小时最大请求数
    min_delay_seconds: float = 1.0       # 最小请求间隔
    max_delay_seconds: float = 5.0       # 最大请求间隔
    burst_limit: int = 5                 # 突发请求限制


@dataclass
class ProxyConfig:
    """代理配置"""
    enabled: bool = False
    proxy_list: List[str] = field(default_factory=list)
    rotate_interval: int = 10            # 每N次请求轮换一次
    health_check_url: str = "https://httpbin.org/ip"
    timeout: float = 10.0


class RateLimiter:
    """令牌桶限速器"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.minute_requests: List[float] = []
        self.hour_requests: List[float] = []
        self.last_request_time: float = 0
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> Tuple[bool, float]:
        """
        获取请求许可
        返回: (是否允许, 需等待秒数)
        """
        async with self._lock:
            now = time.time()
            
            # 清理过期记录
            self.minute_requests = [
                t for t in self.minute_requests 
                if now - t < 60
            ]
            self.hour_requests = [
                t for t in self.hour_requests 
                if now - t < 3600
            ]
            
            # 检查分钟限制
            if len(self.minute_requests) >= self.config.requests_per_minute:
                wait_time = 60 - (now - self.minute_requests[0])
                return False, max(0, wait_time)
            
            # 检查小时限制
            if len(self.hour_requests) >= self.config.requests_per_hour:
                wait_time = 3600 - (now - self.hour_requests[0])
                return False, max(0, wait_time)
            
            # 检查最小间隔
            elapsed = now - self.last_request_time
            if elapsed < self.config.min_delay_seconds:
                wait_time = self.config.min_delay_seconds - elapsed
                return False, wait_time
            
            # 允许请求
            self.minute_requests.append(now)
            self.hour_requests.append(now)
            self.last_request_time = now
            
            return True, 0
    
    def get_stats(self) -> Dict:
        """获取限速统计"""
        now = time.time()
        return {
            "minute_requests": len([t for t in self.minute_requests if now - t < 60]),
            "hour_requests": len([t for t in self.hour_requests if now - t < 3600]),
            "config": {
                "rpm": self.config.requests_per_minute,
                "rph": self.config.requests_per_hour
            }
        }


class ProxyRotator:
    """代理轮换器"""
    
    def __init__(self, config: ProxyConfig):
        self.config = config
        self.current_index: int = 0
        self.request_count: int = 0
        self.failed_proxies: set = set()
        self.proxy_stats: Dict[str, Dict] = defaultdict(lambda: {"success": 0, "fail": 0})
    
    def get_proxy(self) -> Optional[str]:
        """获取当前代理"""
        if not self.config.enabled or not self.config.proxy_list:
            return None
        
        # 跳过失败的代理
        available = [
            p for p in self.config.proxy_list 
            if p not in self.failed_proxies
        ]
        
        if not available:
            # 重置失败列表
            self.failed_proxies.clear()
            available = self.config.proxy_list
        
        # 轮换代理
        self.request_count += 1
        if self.request_count % self.config.rotate_interval == 0:
            self.current_index = (self.current_index + 1) % len(available)
        
        return available[self.current_index % len(available)]
    
    def report_success(self, proxy: str):
        """报告代理成功"""
        self.proxy_stats[proxy]["success"] += 1
    
    def report_failure(self, proxy: str):
        """报告代理失败"""
        self.proxy_stats[proxy]["fail"] += 1
        # 连续失败3次则标记为不可用
        if self.proxy_stats[proxy]["fail"] >= 3:
            self.failed_proxies.add(proxy)
            logger.warning(f"Proxy {proxy} marked as failed")
    
    def get_stats(self) -> Dict:
        """获取代理统计"""
        return {
            "total_proxies": len(self.config.proxy_list),
            "failed_proxies": len(self.failed_proxies),
            "current_proxy": self.get_proxy(),
            "stats": dict(self.proxy_stats)
        }


class UserAgentManager:
    """User-Agent管理器"""
    
    # 常见桌面浏览器UA
    DESKTOP_UAS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    ]
    
    # 移动端UA
    MOBILE_UAS = [
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    ]
    
    def __init__(self, mobile_ratio: float = 0.2):
        self.mobile_ratio = mobile_ratio
        self._last_ua: Optional[str] = None
    
    def get_random_ua(self, force_desktop: bool = False) -> str:
        """获取随机UA"""
        if force_desktop or random.random() > self.mobile_ratio:
            ua = random.choice(self.DESKTOP_UAS)
        else:
            ua = random.choice(self.MOBILE_UAS)
        
        # 避免连续使用相同UA
        while ua == self._last_ua and len(self.DESKTOP_UAS) > 1:
            ua = random.choice(self.DESKTOP_UAS)
        
        self._last_ua = ua
        return ua


class AntiCrawlerManager:
    """反爬虫管理器 - 统一管理所有反爬策略"""
    
    def __init__(
        self,
        rate_config: Optional[RateLimitConfig] = None,
        proxy_config: Optional[ProxyConfig] = None,
        mobile_ratio: float = 0.2
    ):
        self.rate_config = rate_config or RateLimitConfig()
        self.proxy_config = proxy_config or ProxyConfig()
        
        self.rate_limiter = RateLimiter(self.rate_config)
        self.proxy_rotator = ProxyRotator(self.proxy_config)
        self.ua_manager = UserAgentManager(mobile_ratio)
        
        # 请求统计
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "rate_limited_count": 0,
            "captcha_detected": 0,
            "start_time": datetime.now().isoformat()
        }
        
        # CAPTCHA检测关键词
        self.captcha_keywords = [
            "验证码", "captcha", "verify", "人机验证",
            "滑动验证", "点击验证", "图形验证"
        ]
    
    async def prepare_request(self) -> Dict:
        """
        准备请求 - 获取限速许可、代理、UA等
        返回请求头和代理配置
        """
        # 获取限速许可
        allowed, wait_time = await self.rate_limiter.acquire()
        if not allowed:
            self.stats["rate_limited_count"] += 1
            logger.info(f"Rate limited, waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)
            # 重新获取许可
            await self.rate_limiter.acquire()
        
        # 添加随机延迟（模拟人类行为）
        delay = random.uniform(
            self.rate_config.min_delay_seconds,
            self.rate_config.max_delay_seconds
        )
        await asyncio.sleep(delay)
        
        # 获取UA和代理
        ua = self.ua_manager.get_random_ua()
        proxy = self.proxy_rotator.get_proxy()
        
        self.stats["total_requests"] += 1
        
        return {
            "user_agent": ua,
            "proxy": proxy,
            "headers": {
                "User-Agent": ua,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0",
            }
        }
    
    def report_success(self, proxy: Optional[str] = None):
        """报告请求成功"""
        self.stats["successful_requests"] += 1
        if proxy:
            self.proxy_rotator.report_success(proxy)
    
    def report_failure(self, proxy: Optional[str] = None):
        """报告请求失败"""
        self.stats["failed_requests"] += 1
        if proxy:
            self.proxy_rotator.report_failure(proxy)
    
    def detect_captcha(self, page_content: str) -> bool:
        """检测页面是否包含验证码"""
        content_lower = page_content.lower()
        for keyword in self.captcha_keywords:
            if keyword in content_lower:
                self.stats["captcha_detected"] += 1
                logger.warning(f"CAPTCHA detected: found keyword '{keyword}'")
                return True
        return False
    
    def get_backoff_delay(self, retry_count: int) -> float:
        """获取指数退避延迟"""
        base_delay = 2.0
        max_delay = 60.0
        delay = min(base_delay * (2 ** retry_count), max_delay)
        # 添加随机抖动
        jitter = random.uniform(0, delay * 0.3)
        return delay + jitter
    
    def get_stats(self) -> Dict:
        """获取完整统计"""
        return {
            **self.stats,
            "rate_limiter": self.rate_limiter.get_stats(),
            "proxy_rotator": self.proxy_rotator.get_stats(),
            "uptime_hours": (
                datetime.now() - datetime.fromisoformat(self.stats["start_time"])
            ).total_seconds() / 3600
        }


# 全局反爬管理器实例
_anti_crawler: Optional[AntiCrawlerManager] = None


def get_anti_crawler() -> AntiCrawlerManager:
    """获取反爬管理器单例"""
    global _anti_crawler
    if _anti_crawler is None:
        _anti_crawler = AntiCrawlerManager()
    return _anti_crawler


def init_anti_crawler(
    rate_config: Optional[RateLimitConfig] = None,
    proxy_config: Optional[ProxyConfig] = None
) -> AntiCrawlerManager:
    """初始化反爬管理器"""
    global _anti_crawler
    _anti_crawler = AntiCrawlerManager(
        rate_config=rate_config,
        proxy_config=proxy_config
    )
    return _anti_crawler
