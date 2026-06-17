"""
抖音商家后台自动化
使用Playwright处理抖音商家后台扫码登录和账号密码登录
"""
import asyncio
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

# 导入配置
try:
    from .config import settings
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from config import settings

logger = logging.getLogger(__name__)


class DouyinBot:
    """抖音商家后台自动化机器人"""

    # 抖音商家后台地址
    DOUYIN_MERCHANT_URL = "https://fxg.jinritemai.com/login/common?channel=zhaoshang"

    def __init__(self, data_dir: Optional[str] = None):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.is_logged_in = False
        self.data_dir = Path(data_dir) if data_dir else Path(settings.PDD_DATA_DIR)
        self.storage_state_path = self.data_dir / "douyin_storage_state.json"
        self.login_screenshot_path = self.data_dir / "douyin_login.png"
        self.headless = settings.BROWSER_HEADLESS
        self._playwright_context_manager = None

    def _page_is_closed(self) -> bool:
        try:
            return self.page is not None and self.page.is_closed()
        except Exception:
            return True

    @staticmethod
    def _is_target_closed_error(error: Exception) -> bool:
        return (
            error.__class__.__name__ == "TargetClosedError"
            or "has been closed" in str(error)
        )

    async def start(self, headless: Optional[bool] = None):
        """启动浏览器"""
        if self.page:
            logger.info("浏览器已启动")
            return

        try:
            # Windows下修复事件循环问题
            import sys
            if sys.platform == 'win32':
                import asyncio
                # 检查当前事件循环
                try:
                    loop = asyncio.get_running_loop()
                    if isinstance(loop, asyncio.ProactorEventLoop):
                        # 在Windows上，ProactorEventLoop不支持subprocess
                        # Playwright需要subprocess支持
                        pass
                except:
                    pass

            # 使用上下文管理器方式启动playwright
            self._playwright_context_manager = async_playwright()
            self.playwright = await self._playwright_context_manager.__aenter__()

            launch_headless = self.headless if headless is None else headless
            self.browser = await self.playwright.chromium.launch(
                headless=launch_headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            self.headless = launch_headless

            # 准备上下文参数
            context_kwargs = {
                'viewport': {'width': 1920, 'height': 1080},
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'locale': 'zh-CN',
                'timezone_id': 'Asia/Shanghai',
            }

            # 如果存在会话文件，加载它
            if self.storage_state_path.exists():
                context_kwargs["storage_state"] = str(self.storage_state_path)
                logger.info(f"加载已保存的会话: {self.storage_state_path}")

            self.context = await self.browser.new_context(**context_kwargs)

            # 添加初始化脚本，隐藏自动化特征
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            self.page = await self.context.new_page()
            logger.info("抖音浏览器启动成功")
        except Exception as e:
            logger.error(f"浏览器启动失败: {e}")
            raise

    async def close(self):
        """关闭浏览器"""
        close_errors = []

        if self.page:
            try:
                await self.page.close()
            except Exception as e:
                close_errors.append(e)
        if self.context:
            try:
                await self.context.close()
            except Exception as e:
                close_errors.append(e)
        if self.browser:
            try:
                await self.browser.close()
            except Exception as e:
                close_errors.append(e)
        if self._playwright_context_manager:
            try:
                await self._playwright_context_manager.__aexit__(None, None, None)
            except Exception as e:
                close_errors.append(e)

        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None
        self._playwright_context_manager = None
        self.is_logged_in = False
        self.headless = settings.BROWSER_HEADLESS

        if close_errors:
            logger.error(f"关闭浏览器时出错: {close_errors[0]}")
        else:
            logger.info("抖音浏览器已关闭")

    async def start_qr_login(self) -> str:
        """启动二维码登录并返回截图路径"""
        self.data_dir.mkdir(parents=True, exist_ok=True)

        if self.page and (self.headless is not False or self._page_is_closed()):
            await self.close()
        if not self.page:
            await self.start(headless=False)

        try:
            logger.info(f"正在访问抖音商家后台: {self.DOUYIN_MERCHANT_URL}")
            try:
                await self.page.goto(self.DOUYIN_MERCHANT_URL, wait_until='networkidle', timeout=30000)
            except Exception as e:
                if not self._is_target_closed_error(e):
                    raise
                logger.info("检测到抖音登录浏览器已关闭，重新打开")
                await self.close()
                await self.start(headless=False)
                await self.page.goto(self.DOUYIN_MERCHANT_URL, wait_until='networkidle', timeout=30000)

            # 等待页面加载
            await asyncio.sleep(2)

            # 检查是否已经登录
            if await self.check_login_status():
                logger.info("已经登录，无需扫码")
                return str(self.login_screenshot_path)

            # 等待二维码加载
            await asyncio.sleep(1)
            await self.capture_login_screenshot()

            logger.info(f"二维码截图已保存: {self.login_screenshot_path}")
            return str(self.login_screenshot_path)

        except Exception as e:
            logger.error(f"启动二维码登录失败: {e}")
            if self._is_target_closed_error(e) or self._page_is_closed():
                await self.close()
            else:
                try:
                    await self.capture_login_screenshot()
                except Exception:
                    pass
            raise

    async def capture_login_screenshot(self) -> str:
        """保存登录页截图"""
        if not self.page or self._page_is_closed():
            raise RuntimeError("浏览器未启动")

        self.data_dir.mkdir(parents=True, exist_ok=True)
        await self.page.screenshot(path=str(self.login_screenshot_path), full_page=False)
        logger.info(f"截图已保存: {self.login_screenshot_path}")
        return str(self.login_screenshot_path)

    async def check_login_status(self) -> bool:
        """检查当前是否已登录"""
        if not self.page:
            return False
        if self._page_is_closed():
            await self.close()
            return False

        try:
            # 检查登录页面的特征元素
            login_markers = [
                'text=扫码登录',
                'text=账号登录',
                'text=验证码登录',
                '.qrcode-wrap',
                '[class*="qrcode"]',
                '[class*="login"]',
            ]

            for marker in login_markers:
                try:
                    count = await self.page.locator(marker).count()
                    if count > 0:
                        logger.info(f"检测到登录标识: {marker}")
                        await self.capture_login_screenshot()
                        return False
                except Exception:
                    continue

            # 检查已登录的特征元素
            auth_markers = [
                'text=店铺',
                'text=数据',
                'text=商品',
                'text=订单',
                'text=推广',
                'text=营销',
                'text=客服',
                'text=店铺概况',
                '[class*="avatar"]',
                '[class*="user-info"]',
                '[class*="merchant"]',
            ]

            for marker in auth_markers:
                try:
                    count = await self.page.locator(marker).count()
                    if count > 0:
                        logger.info(f"检测到已登录标识: {marker}")
                        await self.save_storage_state()
                        self.is_logged_in = True
                        return True
                except Exception:
                    continue

            # 检查URL
            current_url = self.page.url.lower()
            logger.info(f"当前URL: {current_url}")

            # 如果URL包含这些路径，说明已登录
            logged_in_url_markers = ['/shop/', '/data/', '/order/', '/goods/', '/dashboard', '/home']
            if any(fragment in current_url for fragment in logged_in_url_markers):
                logger.info("URL表明已登录")
                await self.save_storage_state()
                self.is_logged_in = True
                return True

            # 如果URL还在登录页面
            if 'login' in current_url or 'passport' in current_url:
                logger.info("仍在登录页面")
                await self.capture_login_screenshot()
                return False

            # 默认为未登录
            await self.capture_login_screenshot()
            return False

        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            if self._is_target_closed_error(e) or self._page_is_closed():
                await self.close()
            else:
                try:
                    await self.capture_login_screenshot()
                except Exception:
                    pass
            return False

    async def save_storage_state(self) -> None:
        """持久化浏览器会话"""
        if not self.context:
            raise RuntimeError("浏览器上下文未启动")

        self.data_dir.mkdir(parents=True, exist_ok=True)
        await self.context.storage_state(path=str(self.storage_state_path))
        logger.info(f"会话已保存: {self.storage_state_path}")

    async def wait_for_login(self, timeout: int = 120) -> bool:
        """等待用户扫码登录

        Args:
            timeout: 超时时间（秒）

        Returns:
            bool: 是否登录成功
        """
        if not self.page:
            return False

        start_time = asyncio.get_event_loop().time()
        check_interval = 2  # 每2秒检查一次

        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                logger.warning(f"等待登录超时（{timeout}秒）")
                return False

            if await self.check_login_status():
                logger.info("登录成功！")
                return True

            await asyncio.sleep(check_interval)

    async def get_shop_info(self) -> Dict[str, Any]:
        """获取店铺信息"""
        if not self.is_logged_in:
            raise RuntimeError("未登录")

        # 这里可以实现获取店铺信息的逻辑
        # 例如：解析页面DOM、调用抖音开放平台API等
        return {
            "shop_name": "待实现",
            "shop_id": "待实现"
        }

    async def login_with_password(self) -> bool:
        """使用账号密码登录抖音商家后台"""
        if not self.page:
            await self.start()

        try:
            logger.info("正在访问抖音商家后台...")
            await self.page.goto(self.DOUYIN_MERCHANT_URL, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(2)

            # 检查是否已经登录
            if await self.check_login_status():
                logger.info("已经登录")
                self.is_logged_in = True
                return True

            # 需要登录
            if not settings.DOUYIN_USERNAME or not settings.DOUYIN_PASSWORD:
                logger.error("未配置抖音登录凭据")
                return False

            # 尝试切换到账号密码登录
            try:
                account_login_selectors = [
                    'text=账号登录',
                    'text=密码登录',
                    '[data-testid="password-login"]',
                ]
                for selector in account_login_selectors:
                    locator = self.page.locator(selector)
                    if await locator.count() > 0:
                        await locator.first.click()
                        await asyncio.sleep(1)
                        logger.info("已切换到账号密码登录")
                        break
            except Exception as e:
                logger.warning(f"未找到账号登录切换按钮: {e}")

            # 输入用户名
            try:
                username_selectors = [
                    'input[name="username"]',
                    'input[name="mobile"]',
                    'input[name="account"]',
                    'input[placeholder*="手机号"]',
                    'input[placeholder*="账号"]',
                    'input[type="text"]',
                ]

                username_input = None
                for selector in username_selectors:
                    locator = self.page.locator(selector)
                    count = await locator.count()
                    if count > 0:
                        # 找到可见的输入框
                        for i in range(count):
                            try:
                                if await locator.nth(i).is_visible(timeout=1000):
                                    username_input = locator.nth(i)
                                    break
                            except:
                                continue
                    if username_input:
                        break

                if not username_input:
                    logger.error("未找到用户名输入框")
                    await self.page.screenshot(path=str(self.data_dir / "douyin_login_error.png"))
                    return False

                await username_input.fill(settings.DOUYIN_USERNAME)
                logger.info("已填入用户名")

                # 输入密码
                password_selectors = [
                    'input[name="password"]',
                    'input[type="password"]',
                    'input[placeholder*="密码"]',
                ]

                password_input = None
                for selector in password_selectors:
                    locator = self.page.locator(selector)
                    count = await locator.count()
                    if count > 0:
                        for i in range(count):
                            try:
                                if await locator.nth(i).is_visible(timeout=1000):
                                    password_input = locator.nth(i)
                                    break
                            except:
                                continue
                    if password_input:
                        break

                if not password_input:
                    logger.error("未找到密码输入框")
                    await self.page.screenshot(path=str(self.data_dir / "douyin_login_error.png"))
                    return False

                await password_input.fill(settings.DOUYIN_PASSWORD)
                logger.info("已填入密码")

                # 查找并点击登录按钮
                login_button_selectors = [
                    'button[type="submit"]',
                    'button:has-text("登录")',
                    'button:has-text("立即登录")',
                    'text=登录',
                ]

                login_button = None
                for selector in login_button_selectors:
                    locator = self.page.locator(selector)
                    count = await locator.count()
                    if count > 0:
                        for i in range(count):
                            try:
                                if await locator.nth(i).is_visible(timeout=1000):
                                    login_button = locator.nth(i)
                                    break
                            except:
                                continue
                    if login_button:
                        break

                if not login_button:
                    logger.error("未找到登录按钮")
                    await self.page.screenshot(path=str(self.data_dir / "douyin_login_error.png"))
                    return False

                await login_button.click()
                logger.info("已点击登录按钮")

                # 等待登录完成（最多等待30秒）
                for _ in range(15):
                    await asyncio.sleep(2)
                    if await self.check_login_status():
                        logger.info("抖音账号密码登录成功")
                        self.is_logged_in = True
                        await self.save_storage_state()
                        return True

                logger.error("登录超时，可能需要验证码或登录失败")
                await self.page.screenshot(path=str(self.data_dir / "douyin_login_timeout.png"))
                return False

            except Exception as e:
                logger.error(f"填写登录表单失败: {e}")
                await self.page.screenshot(path=str(self.data_dir / "douyin_login_form_error.png"))
                return False

        except Exception as e:
            logger.error(f"登录失败: {e}")
            return False


# 创建全局实例
douyin_bot = DouyinBot()
