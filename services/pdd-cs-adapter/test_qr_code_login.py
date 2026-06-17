"""
测试扫码登录功能
"""
import asyncio
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import settings
from playwright_bot import playwright_bot
from douyin_bot import douyin_bot

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_pdd_authorization_login():
    """测试拼多多账号密码授权登录"""
    logger.info("=" * 60)
    logger.info("测试拼多多账号密码授权登录")
    logger.info("=" * 60)

    try:
        result = await playwright_bot.start_password_login()
        logger.info(f"授权已发起: {result.get('message', result.get('status'))}")
        logger.info("请在打开的浏览器中完成滑块、短信或扫码确认")

        # 轮询检查登录状态（最多60秒）
        is_logged_in = bool(result.get("is_logged_in"))
        for i in range(30):
            if is_logged_in:
                break
            await asyncio.sleep(2)
            is_logged_in = await playwright_bot.check_login_status()
            if not is_logged_in:
                pending = await playwright_bot.continue_password_login()
            else:
                pending = None
            logger.info(
                f"登录状态检查 {i+1}/30: "
                f"{'✓ 已授权' if is_logged_in else pending.get('message') if pending else '等待用户完成验证'}"
            )

            if is_logged_in:
                # 检查会话文件
                if playwright_bot.storage_state_path.exists():
                    logger.info(f"✓ 会话文件已保存: {playwright_bot.storage_state_path}")
                logger.info("✓ 拼多多账号密码授权成功")
                await playwright_bot.close()
                return True

        logger.warning("⚠ 账号密码授权超时（60秒）")
        await playwright_bot.close()
        return False

    except Exception as e:
        logger.error(f"✗ 测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        await playwright_bot.close()
        return False


async def test_douyin_qr_login():
    """测试抖音扫码登录"""
    logger.info("=" * 60)
    logger.info("测试抖音扫码登录")
    logger.info("=" * 60)

    try:
        # 启动扫码登录
        screenshot_path = await douyin_bot.start_qr_login()
        logger.info(f"✓ 二维码截图已生成: {screenshot_path}")
        logger.info("请使用抖音APP扫描二维码登录")

        # 轮询检查登录状态（最多60秒）
        for i in range(30):
            await asyncio.sleep(2)
            is_logged_in = await douyin_bot.check_login_status()
            logger.info(f"登录状态检查 {i+1}/30: {'✓ 已登录' if is_logged_in else '等待扫码...'}")

            if is_logged_in:
                # 检查会话文件
                if douyin_bot.storage_state_path.exists():
                    logger.info(f"✓ 会话文件已保存: {douyin_bot.storage_state_path}")
                logger.info("✓ 抖音扫码登录成功")
                await douyin_bot.close()
                return True

        logger.warning("⚠ 扫码登录超时（60秒）")
        await douyin_bot.close()
        return False

    except Exception as e:
        logger.error(f"✗ 测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        await douyin_bot.close()
        return False


async def main():
    """主测试函数"""
    logger.info("\n开始测试登录功能\n")

    print("请选择要测试的功能：")
    print("1. 测试拼多多账号密码授权登录")
    print("2. 测试抖音扫码登录")
    print("3. 测试拼多多账号密码登录（注意：拼多多可能不支持）")

    # 默认测试拼多多账号密码授权登录
    result = await test_pdd_authorization_login()

    logger.info("\n" + "=" * 60)
    logger.info(f"测试结果: {'✓ 成功' if result else '✗ 失败或超时'}")
    logger.info("=" * 60)

    return result


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    success = asyncio.run(main())
    sys.exit(0 if success else 1)
