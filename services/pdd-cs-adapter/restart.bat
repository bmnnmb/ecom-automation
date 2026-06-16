@echo off
chcp 65001 >nul
echo ============================================
echo 停止所有8003端口的服务
echo ============================================

REM 查找并终止所有监听8003端口的进程
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8003 ^| findstr LISTENING') do (
    echo 终止进程 PID: %%a
    taskkill /F /PID %%a 2>nul
)

echo.
echo 等待2秒...
timeout /t 2 /nobreak >nul

echo.
echo ============================================
echo 启动后端服务
echo ============================================
cd /d D:\phpEnv\www\ecom-automation\services\pdd-cs-adapter

REM 清除Python缓存
echo 清除Python缓存...
if exist __pycache__ rd /s /q __pycache__
if exist routes\__pycache__ rd /s /q routes\__pycache__

echo.
echo 启动uvicorn...
uvicorn main:app --port 8003 --host 0.0.0.0

pause
