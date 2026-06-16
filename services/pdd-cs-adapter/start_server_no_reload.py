"""
启动服务脚本 - 修复Windows Event Loop问题（无reload模式）
"""
import asyncio
import sys

# 在导入uvicorn之前设置支持 Playwright subprocess 的事件循环策略
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    print("已设置 WindowsProactorEventLoopPolicy")

if __name__ == "__main__":
    import uvicorn
    print(f"当前事件循环策略: {asyncio.get_event_loop_policy()}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=False,  # 禁用reload以确保事件循环策略生效
        loop="asyncio"
    )
