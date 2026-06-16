"""
拼多多 Playwright Bot 测试套件
测试浏览器自动化功能：登录、客服、订单、商品操作
"""
import asyncio
import logging
import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from playwright_bot import PlaywrightBot
from config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PlaywrightBotTester:
    """Playwright Bot 测试类"""

    def __init__(self):
        self.bot = PlaywrightBot()
        self.test_results = []

    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """记录测试结果"""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = f"{status} | {test_name}"
        if message:
            result += f" | {message}"
        logger.info(result)
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "message": message
        })

    async def test_1_browser_startup(self):
        """测试1: 浏览器启动"""
        try:
            await self.bot.start()
            is_running = self.bot.page is not None and self.bot.browser is not None
            self.log_test("浏览器启动", is_running)
            return is_running
        except Exception as e:
            self.log_test("浏览器启动", False, str(e))
            return False

    async def test_2_qr_login_init(self):
        """测试2: 二维码登录页面"""
        try:
            screenshot_path = await self.bot.start_qr_login()
            exists = Path(screenshot_path).exists()
            self.log_test(
                "二维码登录初始化",
                exists,
                f"截图路径: {screenshot_path}" if exists else "截图未生成"
            )

            if exists:
                logger.info(f"📸 请查看二维码截图: {screenshot_path}")
                logger.info("请在30秒内扫码登录...")
                await asyncio.sleep(30)  # 等待用户扫码

            return exists
        except Exception as e:
            self.log_test("二维码登录初始化", False, str(e))
            return False

    async def test_3_login_status(self):
        """测试3: 检查登录状态"""
        try:
            is_logged_in = await self.bot.check_login_status()
            self.log_test("登录状态检查", True, f"登录状态: {is_logged_in}")
            return is_logged_in
        except Exception as e:
            self.log_test("登录状态检查", False, str(e))
            return False

    async def test_4_navigate_customer_service(self):
        """测试4: 导航到客服页面"""
        try:
            await self.bot.navigate_to_customer_service()
            current_url = self.bot.page.url if self.bot.page else ""
            success = 'chat' in current_url or 'message' in current_url
            self.log_test(
                "导航到客服页面",
                success,
                f"当前URL: {current_url}"
            )

            # 截图保存当前页面
            screenshot_path = "data/pdd_customer_service.png"
            await self.bot.take_screenshot(screenshot_path)
            logger.info(f"📸 客服页面截图: {screenshot_path}")

            return success
        except Exception as e:
            self.log_test("导航到客服页面", False, str(e))
            return False

    async def test_5_get_unread_messages(self):
        """测试5: 获取未读消息"""
        try:
            messages = await self.bot.get_unread_messages()
            self.log_test(
                "获取未读消息",
                True,
                f"找到 {len(messages)} 条未读消息"
            )

            if messages:
                logger.info("未读消息列表:")
                for idx, msg in enumerate(messages[:3]):  # 只显示前3条
                    logger.info(f"  {idx+1}. {msg.get('user_name')} : {msg.get('last_message')[:30]}...")

            return True
        except Exception as e:
            self.log_test("获取未读消息", False, str(e))
            return False

    async def test_6_navigate_to_orders(self):
        """测试6: 导航到订单页面"""
        try:
            # 直接访问订单页面
            orders_url = f"{settings.PDD_WORKBENCH_URL}/order"
            await self.bot.page.goto(orders_url, wait_until='networkidle', timeout=15000)
            await asyncio.sleep(2)

            current_url = self.bot.page.url
            success = 'order' in current_url.lower()
            self.log_test(
                "导航到订单页面",
                success,
                f"URL: {current_url}"
            )

            # 截图
            screenshot_path = "data/pdd_orders.png"
            await self.bot.take_screenshot(screenshot_path)
            logger.info(f"📸 订单页面截图: {screenshot_path}")

            return success
        except Exception as e:
            self.log_test("导航到订单页面", False, str(e))
            return False

    async def test_7_navigate_to_products(self):
        """测试7: 导航到商品页面"""
        try:
            # 直接访问商品页面
            products_url = f"{settings.PDD_WORKBENCH_URL}/goods"
            await self.bot.page.goto(products_url, wait_until='networkidle', timeout=15000)
            await asyncio.sleep(2)

            current_url = self.bot.page.url
            success = 'goods' in current_url.lower() or 'product' in current_url.lower()
            self.log_test(
                "导航到商品页面",
                success,
                f"URL: {current_url}"
            )

            # 截图
            screenshot_path = "data/pdd_products.png"
            await self.bot.take_screenshot(screenshot_path)
            logger.info(f"📸 商品页面截图: {screenshot_path}")

            return success
        except Exception as e:
            self.log_test("导航到商品页面", False, str(e))
            return False

    async def test_8_page_elements_inspection(self):
        """测试8: 页面元素检查（商品页）"""
        try:
            # 检查常见的页面元素
            page = self.bot.page

            # 尝试查找表格、列表等元素
            table_count = await page.locator('table').count()
            list_count = await page.locator('[class*="list"]').count()
            button_count = await page.locator('button').count()

            self.log_test(
                "页面元素检查",
                True,
                f"表格:{table_count}, 列表:{list_count}, 按钮:{button_count}"
            )

            return True
        except Exception as e:
            self.log_test("页面元素检查", False, str(e))
            return False

    async def test_9_storage_state_persistence(self):
        """测试9: Session持久化"""
        try:
            # 保存当前session
            await self.bot.save_storage_state()

            # 检查文件是否存在
            exists = self.bot.storage_state_path.exists()
            file_size = self.bot.storage_state_path.stat().st_size if exists else 0

            self.log_test(
                "Session持久化",
                exists and file_size > 0,
                f"文件大小: {file_size} bytes"
            )

            return exists
        except Exception as e:
            self.log_test("Session持久化", False, str(e))
            return False

    async def test_10_browser_cleanup(self):
        """测试10: 浏览器清理"""
        try:
            await self.bot.close()
            is_closed = self.bot.page is None and self.bot.browser is None
            self.log_test("浏览器清理", is_closed)
            return is_closed
        except Exception as e:
            self.log_test("浏览器清理", False, str(e))
            return False

    def print_summary(self):
        """打印测试摘要"""
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['passed'])
        failed = total - passed

        logger.info("\n" + "="*60)
        logger.info("测试摘要")
        logger.info("="*60)
        logger.info(f"总计: {total} | 通过: {passed} | 失败: {failed}")
        logger.info(f"通过率: {passed/total*100:.1f}%")

        if failed > 0:
            logger.info("\n失败的测试:")
            for r in self.test_results:
                if not r['passed']:
                    logger.info(f"  ❌ {r['test']}: {r['message']}")

        logger.info("="*60)

    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("\n" + "="*60)
        logger.info("开始拼多多 Playwright Bot 测试")
        logger.info("="*60 + "\n")

        # 确保data目录存在
        Path("data").mkdir(exist_ok=True)

        # 运行测试序列
        await self.test_1_browser_startup()
        await self.test_2_qr_login_init()

        login_status = await self.test_3_login_status()

        if login_status:
            logger.info("\n✅ 已登录，继续测试...")
            await self.test_4_navigate_customer_service()
            await self.test_5_get_unread_messages()
            await self.test_6_navigate_to_orders()
            await self.test_7_navigate_to_products()
            await self.test_8_page_elements_inspection()
            await self.test_9_storage_state_persistence()
        else:
            logger.warning("\n⚠️  未登录，跳过后续测试")

        await self.test_10_browser_cleanup()

        # 打印摘要
        self.print_summary()


async def main():
    """主函数"""
    tester = PlaywrightBotTester()

    try:
        await tester.run_all_tests()
    except KeyboardInterrupt:
        logger.info("\n测试被用户中断")
    except Exception as e:
        logger.error(f"\n测试过程中出现异常: {e}", exc_info=True)
    finally:
        # 确保清理
        if tester.bot.page:
            await tester.bot.close()


if __name__ == "__main__":
    asyncio.run(main())
