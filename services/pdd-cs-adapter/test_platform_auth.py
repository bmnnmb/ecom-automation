#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平台授权功能测试脚本
"""
import asyncio
import httpx
import json
import sys

# 设置输出编码为UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_BASE = "http://localhost:8003/api/v1/system"

async def test_api_endpoints():
    """测试所有授权相关的API端点"""

    async with httpx.AsyncClient() as client:
        print("=" * 60)
        print("平台授权API测试")
        print("=" * 60)

        # 测试拼多多接口
        print("\n【拼多多授权接口】")

        endpoints = [
            ("GET", f"{API_BASE}/status", "系统状态"),
            ("GET", f"{API_BASE}/config", "系统配置"),
        ]

        for method, url, name in endpoints:
            try:
                if method == "GET":
                    response = await client.get(url, timeout=5.0)
                else:
                    response = await client.post(url, json={}, timeout=5.0)

                if response.status_code == 200:
                    print(f"[OK] {name}: {url}")
                    if name == "系统配置":
                        data = response.json()
                        print(f"   - 工作台URL: {data.get('workbench_url', 'N/A')}")
                        print(f"   - 数据目录: {data.get('pdd_data_dir', 'N/A')}")
                else:
                    print(f"[WARN] {name}: {url} (状态码: {response.status_code})")
            except Exception as e:
                print(f"[ERROR] {name}: {url} - {str(e)}")

        # 测试API文档访问
        print("\n【API文档访问】")
        try:
            response = await client.get("http://localhost:8003/docs", timeout=5.0)
            if response.status_code == 200:
                print(f"[OK] Swagger文档: http://localhost:8003/docs")
            else:
                print(f"[WARN] Swagger文档访问失败 (状态码: {response.status_code})")
        except Exception as e:
            print(f"[ERROR] Swagger文档: {str(e)}")

        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)

        print("\n下一步操作：")
        print("1. 访问前端页面: http://localhost:5173/system")
        print("2. 点击拼多多或抖音的'授权'按钮")
        print("3. 扫码完成授权流程")
        print("\n提示：")
        print("- 拼多多使用: 拼多多商家版APP")
        print("- 抖音使用: 抖音APP")
        print("\n查看详细文档：")
        print("- 平台授权指南: services/pdd-cs-adapter/PLATFORM_AUTH_GUIDE.md")
        print("- 系统管理说明: admin/src/pages/System/README.md")


if __name__ == "__main__":
    asyncio.run(test_api_endpoints())
