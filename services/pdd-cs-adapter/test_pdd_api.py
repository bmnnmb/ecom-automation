"""
拼多多 API 客户端测试
测试官方开放平台API调用
"""
import asyncio
import logging
import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from pdd_client import PDDClient
from config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PDDAPITester:
    """拼多多API测试类"""

    def __init__(self):
        self.client = PDDClient()
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

    async def test_1_client_init(self):
        """测试1: 客户端初始化"""
        try:
            has_credentials = bool(
                self.client.client_id and
                self.client.client_secret
            )
            self.log_test(
                "客户端初始化",
                True,
                f"凭据配置: {'✓' if has_credentials else '✗'} | "
                f"Access Token: {'✓' if self.client.access_token else '✗'}"
            )
            return True
        except Exception as e:
            self.log_test("客户端初始化", False, str(e))
            return False

    async def test_2_shop_info(self):
        """测试2: 获取店铺信息"""
        try:
            result = await self.client.get_shop_info()
            success = "error_response" not in result

            if success and result:
                shop_name = result.get('mall_info_response', {}).get('mall_name', 'N/A')
                self.log_test("获取店铺信息", True, f"店铺名: {shop_name}")
            else:
                error_msg = result.get('error_response', {}).get('error_msg', 'Unknown')
                self.log_test("获取店铺信息", False, f"API错误: {error_msg}")

            return success
        except Exception as e:
            self.log_test("获取店铺信息", False, str(e))
            return False

    async def test_3_product_list(self):
        """测试3: 获取商品列表"""
        try:
            result = await self.client.get_product_list(page=1, page_size=10)
            success = "error_response" not in result

            if success:
                goods_list = result.get('goods_list_get_response', {}).get('goods_list', [])
                total = result.get('goods_list_get_response', {}).get('total_count', 0)
                self.log_test(
                    "获取商品列表",
                    True,
                    f"商品总数: {total}, 本页: {len(goods_list)}"
                )

                # 显示前3个商品
                if goods_list:
                    logger.info("  前3个商品:")
                    for idx, goods in enumerate(goods_list[:3]):
                        logger.info(f"    {idx+1}. {goods.get('goods_name', 'N/A')}")
            else:
                error_msg = result.get('error_response', {}).get('error_msg', 'Unknown')
                self.log_test("获取商品列表", False, f"API错误: {error_msg}")

            return success
        except Exception as e:
            self.log_test("获取商品列表", False, str(e))
            return False

    async def test_4_order_list(self):
        """测试4: 获取订单列表"""
        try:
            result = await self.client.get_order_list(page=1, page_size=10)
            success = "error_response" not in result

            if success:
                orders = result.get('order_list_get_response', {}).get('order_list', [])
                total = result.get('order_list_get_response', {}).get('total_count', 0)
                self.log_test(
                    "获取订单列表",
                    True,
                    f"订单总数: {total}, 本页: {len(orders)}"
                )

                # 显示前3个订单
                if orders:
                    logger.info("  前3个订单:")
                    for idx, order in enumerate(orders[:3]):
                        order_sn = order.get('order_sn', 'N/A')
                        order_status = order.get('order_status_desc', 'N/A')
                        logger.info(f"    {idx+1}. {order_sn} - {order_status}")
            else:
                error_msg = result.get('error_response', {}).get('error_msg', 'Unknown')
                self.log_test("获取订单列表", False, f"API错误: {error_msg}")

            return success
        except Exception as e:
            self.log_test("获取订单列表", False, str(e))
            return False

    async def test_5_conversation_list(self):
        """测试5: 获取客服会话列表"""
        try:
            result = await self.client.get_conversation_list()
            success = "error_response" not in result

            if success:
                conversations = result.get('pop_chat_conversation_list_response', {}).get('conversation_list', [])
                self.log_test(
                    "获取客服会话列表",
                    True,
                    f"会话数: {len(conversations)}"
                )

                # 显示前3个会话
                if conversations:
                    logger.info("  前3个会话:")
                    for idx, conv in enumerate(conversations[:3]):
                        user = conv.get('buyer_name', 'N/A')
                        last_msg = conv.get('last_message', 'N/A')[:30]
                        logger.info(f"    {idx+1}. {user}: {last_msg}...")
            else:
                error_msg = result.get('error_response', {}).get('error_msg', 'Unknown')
                self.log_test("获取客服会话列表", False, f"API错误: {error_msg}")

            return success
        except Exception as e:
            self.log_test("获取客服会话列表", False, str(e))
            return False

    async def test_6_refund_list(self):
        """测试6: 获取退款列表"""
        try:
            result = await self.client.get_refund_list(page=1, page_size=10)
            success = "error_response" not in result

            if success:
                refunds = result.get('refund_list_increment_get_response', {}).get('refund_list', [])
                self.log_test(
                    "获取退款列表",
                    True,
                    f"退款数: {len(refunds)}"
                )

                if refunds:
                    logger.info("  前3个退款:")
                    for idx, refund in enumerate(refunds[:3]):
                        refund_id = refund.get('refund_id', 'N/A')
                        status = refund.get('refund_status_desc', 'N/A')
                        logger.info(f"    {idx+1}. {refund_id} - {status}")
            else:
                error_msg = result.get('error_response', {}).get('error_msg', 'Unknown')
                self.log_test("获取退款列表", False, f"API错误: {error_msg}")

            return success
        except Exception as e:
            self.log_test("获取退款列表", False, str(e))
            return False

    async def test_7_close_client(self):
        """测试7: 关闭客户端"""
        try:
            await self.client.close()
            self.log_test("关闭客户端", True)
            return True
        except Exception as e:
            self.log_test("关闭客户端", False, str(e))
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
        logger.info("开始拼多多 API 客户端测试")
        logger.info("="*60 + "\n")

        # 配置检查
        logger.info("配置信息:")
        logger.info(f"  Client ID: {self.client.client_id[:10]}..." if self.client.client_id else "  Client ID: 未配置")
        logger.info(f"  Client Secret: {'已配置' if self.client.client_secret else '未配置'}")
        logger.info(f"  Access Token: {'已配置' if self.client.access_token else '未配置'}")
        logger.info(f"  API Base URL: {self.client.base_url}\n")

        # 运行测试
        await self.test_1_client_init()
        await self.test_2_shop_info()
        await self.test_3_product_list()
        await self.test_4_order_list()
        await self.test_5_conversation_list()
        await self.test_6_refund_list()
        await self.test_7_close_client()

        # 打印摘要
        self.print_summary()


async def main():
    """主函数"""
    tester = PDDAPITester()

    try:
        await tester.run_all_tests()
    except KeyboardInterrupt:
        logger.info("\n测试被用户中断")
    except Exception as e:
        logger.error(f"\n测试过程中出现异常: {e}", exc_info=True)
    finally:
        # 确保清理
        await tester.client.close()


if __name__ == "__main__":
    asyncio.run(main())
