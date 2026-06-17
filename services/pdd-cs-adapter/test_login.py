"""
测试拼多多和抖音登录功能
"""
import asyncio
import logging
import sys
import os

# 添加路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import settings
from playwright_bot import playwright_bot
from douyin_bot import douyin_bot

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_pdd_config():
    """测试拼多多配置"""
    logger.info("=" * 50)
    logger.info("测试拼多多配置")
    logger.info("=" * 50)
    logger.info(f"PDD_USERNAME: {'已配置' if settings.PDD_USERNAME else '未配置'}")
    logger.info(f"PDD_PASSWORD: {'已配置' if settings.PDD_PASSWORD else '未配置'}")
    logger.info(f"PDD_DATA_DIR: {settings.PDD_DATA_DIR}")
    logger.info(f"BROWSER_HEADLESS: {settings.BROWSER_HEADLESS}")


async def test_douyin_config():
    """测试抖音配置"""
    logger.info("=" * 50)
    logger.info("测试抖音配置")
    logger.info("=" * 50)
    logger.info(f"DOUYIN_USERNAME: {'已配置' if settings.DOUYIN_USERNAME else '未配置'}")
    logger.info(f"DOUYIN_PASSWORD: {'已配置' if settings.DOUYIN_PASSWORD else '未配置'}")


async def test_pdd_authorization_login():
    """测试拼多多账号密码授权登录"""
    logger.info("=" * 50)
    logger.info("测试拼多多账号密码授权登录")
    logger.info("=" * 50)

    try:
        result = await playwright_bot.start_password_login()
        logger.info(f"授权已发起: {result.get('message', result.get('status'))}")

        # 等待用户完成滑块、短信或扫码确认
        is_logged_in = bool(result.get("is_logged_in"))
        for i in range(30):
            if is_logged_in:
                logger.info("✓ 拼多多账号密码授权成功")
                break
            await asyncio.sleep(2)
            is_logged_in = await playwright_bot.check_login_status()
            if is_logged_in:
                logger.info("✓ 拼多多账号密码授权成功")
                break
            pending = await playwright_bot.continue_password_login()
            logger.info(f"授权状态检查 {i+1}/30: {pending.get('message') if pending else '等待用户完成验证'}")

        await playwright_bot.close()
        logger.info("✓ 拼多多账号密码授权测试完成")
        return is_logged_in
    except Exception as e:
        logger.error(f"✗ 拼多多账号密码授权测试失败: {e}")
        await playwright_bot.close()
        return False


async def test_pdd_password_login():
    """测试拼多多账号密码登录"""
    logger.info("=" * 50)
    logger.info("测试拼多多账号密码登录")
    logger.info("=" * 50)

    if not settings.PDD_USERNAME or not settings.PDD_PASSWORD:
        logger.warning("⊘ 未配置拼多多账号密码，跳过测试")
        return False

    try:
        success = await playwright_bot.login()
        if success:
            logger.info("✓ 拼多多账号密码登录成功")
        else:
            logger.error("✗ 拼多多账号密码登录失败")

        await playwright_bot.close()
        return success
    except Exception as e:
        logger.error(f"✗ 拼多多账号密码登录测试异常: {e}")
        await playwright_bot.close()
        return False


async def test_douyin_qr_login():
    """测试抖音扫码登录"""
    logger.info("=" * 50)
    logger.info("测试抖音扫码登录")
    logger.info("=" * 50)

    try:
        screenshot_path = await douyin_bot.start_qr_login()
        logger.info(f"✓ 二维码截图已生成: {screenshot_path}")

        # 等待5秒检查登录状态
        for i in range(5):
            await asyncio.sleep(1)
            is_logged_in = await douyin_bot.check_login_status()
            logger.info(f"登录状态检查 {i+1}/5: {'已登录' if is_logged_in else '未登录'}")
            if is_logged_in:
                break

        await douyin_bot.close()
        logger.info("✓ 抖音扫码登录测试完成")
        return True
    except Exception as e:
        logger.error(f"✗ 抖音扫码登录测试失败: {e}")
        await douyin_bot.close()
        return False


async def test_douyin_password_login():
    """测试抖音账号密码登录"""
    logger.info("=" * 50)
    logger.info("测试抖音账号密码登录")
    logger.info("=" * 50)

    if not settings.DOUYIN_USERNAME or not settings.DOUYIN_PASSWORD:
        logger.warning("⊘ 未配置抖音账号密码，跳过测试")
        return False

    try:
        success = await douyin_bot.login_with_password()
        if success:
            logger.info("✓ 抖音账号密码登录成功")
        else:
            logger.error("✗ 抖音账号密码登录失败")

        await douyin_bot.close()
        return success
    except Exception as e:
        logger.error(f"✗ 抖音账号密码登录测试异常: {e}")
        await douyin_bot.close()
        return False


async def main():
    """主测试函数"""
    logger.info("\n" + "=" * 50)
    logger.info("开始测试登录功能")
    logger.info("=" * 50 + "\n")

    # 测试配置
    await test_pdd_config()
    await test_douyin_config()

    # 选择测试项
    print("\n请选择要测试的功能：")
    print("1. 拼多多账号密码授权登录")
    print("2. 拼多多账号密码阻塞登录")
    print("3. 抖音扫码登录")
    print("4. 抖音账号密码登录")
    print("5. 全部测试")
    print("0. 退出")

    try:
        choice = input("\n请输入选项 (0-5): ").strip()

        if choice == "1":
            await test_pdd_authorization_login()
        elif choice == "2":
            await test_pdd_password_login()
        elif choice == "3":
            await test_douyin_qr_login()
        elif choice == "4":
            await test_douyin_password_login()
        elif choice == "5":
            await test_pdd_authorization_login()
            await asyncio.sleep(2)
            await test_pdd_password_login()
            await asyncio.sleep(2)
            await test_douyin_qr_login()
            await asyncio.sleep(2)
            await test_douyin_password_login()
        elif choice == "0":
            logger.info("退出测试")
        else:
            logger.error("无效选项")
    except KeyboardInterrupt:
        logger.info("\n测试被中断")

    logger.info("\n" + "=" * 50)
    logger.info("测试完成")
    logger.info("=" * 50)


if __name__ == "__main__":
    # Windows平台修复
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(main())
