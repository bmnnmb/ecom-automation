"""
自动化测试拼多多账号密码登录功能
"""
import asyncio
import logging
import sys
import os

# 添加路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import settings
from playwright_bot import playwright_bot

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_pdd_password_login():
    """测试拼多多账号密码登录"""
    logger.info("=" * 60)
    logger.info("测试拼多多账号密码登录")
    logger.info("=" * 60)

    # 检查配置
    logger.info(f"PDD_USERNAME: {'已配置' if settings.PDD_USERNAME else '未配置'}")
    logger.info(f"PDD_PASSWORD: {'已配置' if settings.PDD_PASSWORD else '未配置'}")
    logger.info(f"PDD_DATA_DIR: {settings.PDD_DATA_DIR}")
    logger.info(f"BROWSER_HEADLESS: {settings.BROWSER_HEADLESS}")

    if not settings.PDD_USERNAME or not settings.PDD_PASSWORD:
        logger.error("✗ 未配置拼多多账号密码，测试失败")
        return False

    try:
        logger.info("开始执行登录...")
        success = await playwright_bot.login()

        if success:
            logger.info("✓ 拼多多账号密码登录成功")

            # 检查会话文件是否生成
            if playwright_bot.storage_state_path.exists():
                logger.info(f"✓ 会话文件已保存: {playwright_bot.storage_state_path}")
            else:
                logger.warning("⚠ 会话文件未找到")

        else:
            logger.error("✗ 拼多多账号密码登录失败")

        # 等待几秒再关闭浏览器
        logger.info("等待5秒后关闭浏览器...")
        await asyncio.sleep(5)

        await playwright_bot.close()
        logger.info("✓ 浏览器已关闭")

        return success

    except Exception as e:
        logger.error(f"✗ 测试异常: {e}")
        import traceback
        logger.error(traceback.format_exc())

        try:
            await playwright_bot.close()
        except:
            pass

        return False


async def main():
    """主测试函数"""
    logger.info("\n开始自动化测试\n")

    result = await test_pdd_password_login()

    logger.info("\n" + "=" * 60)
    if result:
        logger.info("测试结果: ✓ 成功")
    else:
        logger.info("测试结果: ✗ 失败")
    logger.info("=" * 60)

    return result


if __name__ == "__main__":
    # Windows平台修复
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    success = asyncio.run(main())
    sys.exit(0 if success else 1)
