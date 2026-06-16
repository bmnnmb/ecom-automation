#!/bin/bash

echo "============================================"
echo "停止所有8003端口的服务"
echo "============================================"

# 查找并终止所有监听8003端口的进程
lsof -ti:8003 | xargs kill -9 2>/dev/null || echo "没有找到运行在8003端口的进程"

echo ""
echo "等待2秒..."
sleep 2

echo ""
echo "============================================"
echo "启动后端服务"
echo "============================================"
cd "$(dirname "$0")"

# 清除Python缓存
echo "清除Python缓存..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null

echo ""
echo "启动uvicorn..."
uvicorn main:app --reload --port 8003 --host 0.0.0.0
