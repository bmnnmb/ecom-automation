"""
启动服务脚本 - 修复Windows Event Loop问题
"""
import asyncio
import sys

# 在导入uvicorn之前设置支持 Playwright subprocess 的事件循环策略
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=False,
        loop="asyncio"  # 使用asyncio事件循环
    )
