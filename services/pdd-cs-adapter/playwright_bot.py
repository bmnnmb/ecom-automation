"""
浏览器自动化
使用Playwright处理拼多多工作台
"""
import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

# 导入配置和消息处理器
try:
    from .config import settings
    from .message_handler import MessageContext, MessageHandler
except ImportError:
    # 当直接运行时
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from config import settings
    from message_handler import MessageContext, MessageHandler

logger = logging.getLogger(__name__)


class PlaywrightBot:
    """Playwright自动化机器人"""

    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.is_logged_in = False
        self.headless: Optional[bool] = None
        self.message_handler: Optional[MessageHandler] = None
        self.data_dir = Path(os.getenv("PDD_DATA_DIR", settings.PDD_DATA_DIR))
        self.storage_state_path = self.data_dir / "pdd_storage_state.json"
        self.password_login_pending = False
        self.password_login_submitted = False
        self.password_login_filled = False

    def _page_is_closed(self) -> bool:
        """检查页面是否已关闭"""
        try:
            return self.page is not None and self.page.is_closed()
        except Exception:
            return True

    @staticmethod
    def _cookie_is_unexpired(cookie: Dict[str, Any]) -> bool:
        """Playwright session cookie may have no positive expires value."""
        expires = cookie.get("expires")
        if isinstance(expires, (int, float)) and expires > 0:
            return expires > datetime.now().timestamp()
        return True

    @classmethod
    def _has_auth_cookies(cls, cookies: List[Dict[str, Any]], current_url: str = "") -> bool:
        """基于关键 cookie 判断是否已有登录态"""
        valid_cookies = [cookie for cookie in cookies if cls._cookie_is_unexpired(cookie)]
        cookie_names = {cookie.get("name") for cookie in valid_cookies}
        if "PASS_ID" in cookie_names:
            return True

        login_url_markers = ("login", "passport")
        if "mms_sid" in cookie_names and current_url:
            return all(marker not in current_url.lower() for marker in login_url_markers)

        return False

    async def _has_visible_locator(self, selector: str) -> bool:
        """检查指定选择器是否有可见元素

        Args:
            selector: CSS选择器或文本选择器

        Returns:
            bool: 是否存在可见元素
        """
        if not self.page:
            return False

        locator = self.page.locator(selector)
        count = await locator.count()
        for index in range(min(count, 20)):
            try:
                if await locator.nth(index).is_visible(timeout=500):
                    return True
            except Exception:
                continue
        return False

    async def _dismiss_browser_warning(self) -> None:
        """关闭拼多多的浏览器版本提示弹窗"""
        if not self.page or self._page_is_closed():
            return

        dismiss_selectors = [
            'button:has-text("已安装去使用")',
            'text=已安装去使用',
        ]
        for selector in dismiss_selectors:
            try:
                if await self._has_visible_locator(selector):
                    await self.page.locator(selector).nth(0).click(timeout=1000)
                    await self.page.wait_for_timeout(500)
                    return
            except Exception:
                continue

    async def _first_visible_locator(self, selectors: List[str], timeout: int = 500):
        """返回第一项可见的 locator"""
        if not self.page:
            return None

        for selector in selectors:
            try:
                locator = self.page.locator(selector)
                count = await locator.count()
                for index in range(min(count, 20)):
                    item = locator.nth(index)
                    if await item.is_visible(timeout=timeout):
                        return item
            except Exception:
                continue
        return None

    async def _click_first_visible(self, selectors: List[str], timeout: int = 1000) -> bool:
        locator = await self._first_visible_locator(selectors, timeout=timeout)
        if not locator:
            return False

        await locator.click(timeout=timeout)
        return True

    async def _fill_first_visible(self, selectors: List[str], value: str, field_name: str) -> bool:
        locator = await self._first_visible_locator(selectors)
        if not locator:
            logger.error(f"未找到{field_name}输入框")
            return False

        await locator.fill(value)
        logger.info(f"已填入{field_name}")
        return True

    async def has_verification_challenge(self) -> bool:
        """检测是否出现滑块/验证码等人工验证"""
        verification_selectors = [
            '.geetest_panel',
            '.geetest_box',
            '.geetest_slider_button',
            '.yidun_slider',
            '.yidun_panel',
            '[class*="geetest"]',
            '[class*="captcha"]',
            '[class*="Captcha"]',
            '[class*="verify"]',
            '[class*="Verify"]',
            '[class*="slider"]',
            '[class*="Slider"]',
            'text=拖动滑块',
            'text=滑块',
            'text=完成拼图',
            'text=验证码',
            'text=安全验证',
        ]
        return await self._first_visible_locator(verification_selectors, timeout=300) is not None

    async def _switch_to_password_login(self) -> None:
        selectors = [
            'text=账号登录',
            'text=密码登录',
            'text=账号密码登录',
            '[data-testid="password-login"]',
        ]
        if await self._click_first_visible(selectors):
            await self.page.wait_for_timeout(500)
            logger.info("已切换到账号密码登录")

    async def _accept_login_agreement(self) -> None:
        checkbox = await self._first_visible_locator([
            'input[type="checkbox"]',
            '[class*="checkbox"]',
            '[class*="agreement"]',
        ], timeout=300)
        if not checkbox:
            return

        try:
            await checkbox.click(timeout=500)
            logger.info("已尝试勾选登录协议")
        except Exception:
            return

    async def _submit_password_login(self) -> Dict[str, Any]:
        """填入 .env 账号密码并提交，验证码由用户人工处理"""
        if not self.page or self._page_is_closed():
            raise RuntimeError("browser is not started")

        if await self.check_login_status():
            return {
                "is_logged_in": True,
                "status": "logged_in",
                "verification_required": False,
                "credentials_filled": self.password_login_filled,
                "message": "已检测到有效登录态",
            }

        if not settings.PDD_USERNAME or not settings.PDD_PASSWORD:
            raise RuntimeError("未配置 PDD_USERNAME 或 PDD_PASSWORD")

        if await self.has_verification_challenge() and not self.password_login_filled:
            return {
                "is_logged_in": False,
                "status": "waiting_verification",
                "verification_required": True,
                "credentials_filled": False,
                "message": "请先在浏览器中完成滑块验证，系统随后会自动填入账号密码",
            }

        await self._switch_to_password_login()

        username_ok = await self._fill_first_visible([
            'input[name="username"]',
            'input[name="mobile"]',
            'input[name="account"]',
            'input[placeholder*="手机号"]',
            'input[placeholder*="账号"]',
            'input[placeholder*="用户名"]',
            'input[autocomplete="username"]',
            'input[type="tel"]',
            'input[type="text"]',
        ], settings.PDD_USERNAME, "账号")
        password_ok = await self._fill_first_visible([
            'input[name="password"]',
            'input[type="password"]',
            'input[placeholder*="密码"]',
            'input[autocomplete="current-password"]',
        ], settings.PDD_PASSWORD, "密码")
        self.password_login_filled = username_ok and password_ok

        if not self.password_login_filled:
            return {
                "is_logged_in": False,
                "status": "waiting_login_form",
                "verification_required": await self.has_verification_challenge(),
                "credentials_filled": False,
                "message": "未找到账号密码输入框，请确认登录页已正常显示",
            }

        await self._accept_login_agreement()

        if not await self._click_first_visible([
            'button[type="submit"]',
            'button:has-text("登录")',
            'button:has-text("立即登录")',
            'button:has-text("登 录")',
            '[class*="login-button"]',
            '[class*="submit-btn"]',
        ], timeout=3000):
            return {
                "is_logged_in": False,
                "status": "waiting_login_form",
                "verification_required": await self.has_verification_challenge(),
                "credentials_filled": True,
                "message": "未找到登录按钮，请在浏览器中手动点击登录",
            }

        self.password_login_submitted = True
        logger.info("已提交拼多多账号密码登录")
        await self.page.wait_for_timeout(1000)

        if await self.check_login_status():
            return {
                "is_logged_in": True,
                "status": "logged_in",
                "verification_required": False,
                "credentials_filled": True,
                "message": "账号密码登录成功，会话已保存",
            }

        verification_required = await self.has_verification_challenge()
        return {
            "is_logged_in": False,
            "status": "waiting_verification" if verification_required else "waiting_login",
            "verification_required": verification_required,
            "credentials_filled": True,
            "message": "请在浏览器中完成滑块/短信等验证" if verification_required else "已提交账号密码，等待登录完成",
        }

    async def start(self, headless: Optional[bool] = None):
        """启动浏览器"""
        if self.page and not self._page_is_closed():
            return
        if self.page and self._page_is_closed():
            await self.close()

        try:
            launch_headless = settings.BROWSER_HEADLESS if headless is None else headless
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=launch_headless,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            self.headless = launch_headless
            context_kwargs = {
                'viewport': {'width': 1920, 'height': 1080},
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            if self.storage_state_path.exists():
                context_kwargs["storage_state"] = str(self.storage_state_path)
            self.context = await self.browser.new_context(**context_kwargs)
            self.page = await self.context.new_page()
            logger.info("浏览器启动成功")
        except Exception as e:
            logger.error(f"浏览器启动失败: {e}")
            raise

    async def start_password_login(self) -> Dict[str, Any]:
        """打开可见浏览器并用 .env 中的账号密码发起登录"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if self.page and (self.headless is not False or self._page_is_closed()):
            await self.close()
        if not self.page:
            await self.start(headless=False)

        try:
            await self.page.goto(settings.PDD_WORKBENCH_URL, wait_until='domcontentloaded')
            await self._dismiss_browser_warning()
            self.password_login_pending = True
            self.password_login_submitted = False
            self.password_login_filled = False
            result = await self._submit_password_login()
            result["login_url"] = getattr(self.page, "url", settings.PDD_WORKBENCH_URL)
            logger.info(f"拼多多账号密码登录已发起: {result['status']}")
            return result
        except Exception:
            await self.close()
            raise

    async def continue_password_login(self) -> Optional[Dict[str, Any]]:
        """轮询阶段继续未完成的账号密码登录流程"""
        if not self.password_login_pending or self.password_login_submitted:
            return None
        if not self.page or self._page_is_closed():
            return None

        result = await self._submit_password_login()
        result["login_url"] = getattr(self.page, "url", settings.PDD_WORKBENCH_URL)
        return result

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
        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception as e:
                close_errors.append(e)

        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None
        self.is_logged_in = False
        self.headless = None
        self.password_login_pending = False
        self.password_login_submitted = False
        self.password_login_filled = False

        if close_errors:
            logger.error(f"关闭浏览器时出错: {close_errors[0]}")
        else:
            logger.info("浏览器已关闭")

    async def check_login_status(self) -> bool:
        """检查当前是否已登录工作台（基于 cookies 检测，不依赖页面元素）"""
        if not self.page and not self.context:
            return False
        if self._page_is_closed():
            try:
                await self.save_storage_state()
                auth_info = self.get_auth_info()
                if auth_info.get("has_auth_cookies"):
                    self.is_logged_in = True
                    return True
            except Exception as e:
                logger.warning(f"页面关闭后保存会话失败: {e}")
            await self.close()
            return False

        # 优先检查关键 cookies（参考 pdd_auto 项目的实现）
        if self.context:
            try:
                cookies = await self.context.cookies()
                current_url = getattr(self.page, "url", "").lower()

                # 如果有关键 cookies 且不在登录页面，判定为已登录
                if self._has_auth_cookies(cookies, current_url):
                    logger.info("检测到有效的登录 cookies（PASS_ID 或 mms_sid）")
                    await self.save_storage_state()
                    self.is_logged_in = True
                    return True
            except Exception as e:
                logger.warning(f"检查 cookies 时出错: {e}")

        # 降级到页面元素检测（可能被滑块遮罩影响）
        auth_markers = [
            '.user-avatar',
            '[data-testid="user-avatar"]',
            'text=店铺概况',
            'text=消息中心',
            'text=多多客服',
            'text=商品管理',
            'text=订单查询',
        ]
        for marker in auth_markers:
            try:
                if await self._has_visible_locator(marker):
                    await self.save_storage_state()
                    self.is_logged_in = True
                    return True
            except Exception:
                continue

        current_url = getattr(self.page, "url", "").lower()
        logged_in_url_markers = ['/chat', '/message', '/goods', '/order', '/dashboard', '/home']
        if current_url and all(fragment not in current_url for fragment in ['login', 'passport']) and any(
            fragment in current_url for fragment in logged_in_url_markers
        ):
            await self.save_storage_state()
            self.is_logged_in = True
            return True

        login_markers = ['text=账号登录', 'text=验证码登录', 'text=扫码登录', 'text=手机扫码登录']
        for marker in login_markers:
            try:
                if await self._has_visible_locator(marker):
                    return False
            except Exception:
                continue

        return False

    async def save_storage_state(self) -> None:
        """持久化浏览器会话"""
        if not self.context:
            raise RuntimeError("browser context is not started")

        self.data_dir.mkdir(parents=True, exist_ok=True)
        await self.context.storage_state(path=str(self.storage_state_path))

    def get_auth_info(self) -> Dict[str, Any]:
        """读取已保存的拼多多授权信息（不返回 cookie 值）"""
        exists = self.storage_state_path.exists()
        info: Dict[str, Any] = {
            "is_authorized": False,
            "status": "unauthorized",
            "message": "未授权",
            "storage_state_path": str(self.storage_state_path),
            "storage_exists": exists,
            "storage_size": 0,
            "updated_at": None,
            "cookie_count": 0,
            "cookie_names": [],
            "domains": [],
            "expires_at": None,
            "has_auth_cookies": False,
            "expired_auth_cookie_names": [],
        }

        if not exists:
            return info

        stat = self.storage_state_path.stat()
        info["storage_size"] = stat.st_size
        info["updated_at"] = datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")

        try:
            state = json.loads(self.storage_state_path.read_text(encoding="utf-8"))
            cookies = state.get("cookies") or []
            info["cookie_count"] = len(cookies)
            info["cookie_names"] = sorted(
                {cookie.get("name") for cookie in cookies if cookie.get("name")}
            )
            info["domains"] = sorted(
                {cookie.get("domain") for cookie in cookies if cookie.get("domain")}
            )

            expires_values = [
                cookie.get("expires")
                for cookie in cookies
                if isinstance(cookie.get("expires"), (int, float)) and cookie.get("expires", 0) > 0
            ]
            if expires_values:
                info["expires_at"] = datetime.fromtimestamp(min(expires_values)).isoformat(timespec="seconds")

            auth_cookie_names = {"PASS_ID", "mms_sid"}
            info["expired_auth_cookie_names"] = sorted({
                cookie.get("name")
                for cookie in cookies
                if cookie.get("name") in auth_cookie_names and not self._cookie_is_unexpired(cookie)
            })
            info["has_auth_cookies"] = self._has_auth_cookies(cookies)
            if info["has_auth_cookies"]:
                info["is_authorized"] = True
                info["status"] = "authorized"
                info["message"] = "已授权"
            elif info["expired_auth_cookie_names"]:
                info["status"] = "invalid"
                info["message"] = "授权 cookie 已过期，请重新授权"
            else:
                info["status"] = "invalid"
                info["message"] = "会话文件存在，但未检测到有效登录 cookie"
        except Exception as e:
            info["status"] = "invalid"
            info["message"] = f"授权信息读取失败: {e}"

        return info

    async def login(self) -> bool:
        """登录拼多多工作台"""
        try:
            result = await self.start_password_login()
            if result.get("is_logged_in"):
                return True

            for i in range(60):
                await asyncio.sleep(2)
                if await self.check_login_status():
                    return True
                await self.continue_password_login()
                logger.info(f"等待账号密码登录完成... ({i+1}/60)")
            return False
        except Exception as e:
            logger.error(f"登录失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def navigate_to_customer_service(self):
        """导航到客服页面"""
        if not self.is_logged_in:
            success = await self.login()
            if not success:
                raise Exception("无法登录")
        
        try:
            # 点击客服图标或导航到客服页面
            customer_service_link = self.page.locator('text=客服')
            if await customer_service_link.count() > 0:
                await customer_service_link.click()
                await self.page.wait_for_load_state('networkidle')
                logger.info("已进入客服页面")
            else:
                # 直接导航到客服URL
                await self.page.goto(f"{settings.PDD_WORKBENCH_URL}/chat", wait_until='networkidle')
        except Exception as e:
            logger.error(f"导航到客服页面失败: {e}")
            raise
    
    async def get_unread_messages(self) -> List[Dict[str, Any]]:
        """获取未读消息列表"""
        try:
            # 等待消息列表加载
            await self.page.wait_for_selector('.conversation-list', timeout=10000)
            
            # 获取所有会话项
            conversation_items = self.page.locator('.conversation-item')
            count = await conversation_items.count()
            
            messages = []
            for i in range(count):
                item = conversation_items.nth(i)
                
                # 检查是否有未读标记
                unread_badge = item.locator('.unread-badge')
                if await unread_badge.count() > 0:
                    # 提取信息
                    user_name = await item.locator('.user-name').text_content()
                    last_message = await item.locator('.last-message').text_content()
                    time_text = await item.locator('.time').text_content()
                    
                    messages.append({
                        'index': i,
                        'user_name': user_name,
                        'last_message': last_message,
                        'time': time_text
                })
            
            logger.info(f"找到 {len(messages)} 条未读消息")
            return messages
            
        except Exception as e:
            logger.error(f"获取未读消息失败: {e}")
            return []
    
    async def read_conversation_messages(self, conversation_index: int) -> List[Dict[str, Any]]:
        """读取会话中的消息"""
        try:
            # 点击会话
            conversation_items = self.page.locator('.conversation-item')
            await conversation_items.nth(conversation_index).click()
            
            # 等待消息加载
            await self.page.wait_for_selector('.message-list', timeout=10000)
            
            # 获取消息列表
            message_items = self.page.locator('.message-item')
            count = await message_items.count()
            
            messages = []
            for i in range(count):
                item = message_items.nth(i)
                content = await item.locator('.message-content').text_content()
                sender = await item.locator('.sender').text_content()
                time_text = await item.locator('.time').text_content()
                
                messages.append({
                    'content': content,
                    'sender': sender,
                    'time': time_text
                })
            
            return messages
            
        except Exception as e:
            logger.error(f"读取会话消息失败: {e}")
            return []
    
    async def send_reply(self, conversation_index: int, content: str) -> bool:
        """发送回复"""
        try:
            # 确保在正确的会话
            conversation_items = self.page.locator('.conversation-item')
            await conversation_items.nth(conversation_index).click()
            
            # 输入回复内容
            input_box = self.page.locator('.chat-input textarea')
            await input_box.fill(content)
            
            # 点击发送按钮
            send_button = self.page.locator('.send-button')
            await send_button.click()
            
            logger.info(f"发送回复成功: {content[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"发送回复失败: {e}")
            return False
    
    async def auto_reply_loop(self, message_handler: MessageHandler):
        """自动回复循环"""
        self.message_handler = message_handler
        
        try:
            while True:
                # 获取未读消息
                unread_messages = await self.get_unread_messages()
                
                for msg_info in unread_messages:
                    # 读取完整消息
                    messages = await self.read_conversation_messages(msg_info['index'])
                    
                    # 处理最后一条消息
                    if messages:
                        last_msg = messages[-1]
                        message_ctx = MessageContext(
                            conversation_id=str(msg_info['index']),
                            message_id=f"{msg_info['index']}_{len(messages)}",
                            content=last_msg['content'],
                            sender_id=msg_info['user_name'],
                            sender_name=msg_info['user_name'],
                            timestamp=0  # 实际应解析时间
                        )
                        
                        # 处理消息
                        result = await message_handler.process_message(message_ctx)
                        
                        # 如果有自动回复，发送回复
                        if result.auto_reply and not result.need_human:
                            await self.send_reply(msg_info['index'], result.auto_reply)
                        elif result.need_human:
                            # 标记需要人工处理
                            logger.warning(f"会话 {msg_info['index']} 需要人工处理")
                
                # 等待一段时间再检查
                await asyncio.sleep(settings.POLL_INTERVAL)
                
        except asyncio.CancelledError:
            logger.info("自动回复循环已取消")
        except Exception as e:
            logger.error(f"自动回复循环出错: {e}")
    
    async def take_screenshot(self, path: str = "screenshot.png"):
        """截图"""
        if self.page:
            await self.page.screenshot(path=path)
            logger.info(f"截图已保存: {path}")


# 创建全局机器人实例
playwright_bot = PlaywrightBot()
