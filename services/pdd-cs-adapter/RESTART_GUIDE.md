# 🔧 重启服务完整指南

## ✅ 已完成的清理工作

1. ✅ 停止了所有占用8003端口的进程（PID: 14676, 28136, 27860）
2. ✅ 清除了Python缓存文件（__pycache__）
3. ✅ 安装了Playwright浏览器
4. ✅ 验证了二维码生成功能

## 🚀 现在请重启后端服务

### 方法1：使用重启脚本（推荐）

在**新的终端窗口**中：

```batch
D:\phpEnv\www\ecom-automation\services\pdd-cs-adapter\restart.bat
```

这个脚本会：
- 自动停止旧进程
- 清除缓存
- 启动新服务

### 方法2：手动启动

在**新的终端窗口**中：

```batch
cd D:\phpEnv\www\ecom-automation\services\pdd-cs-adapter
uvicorn main:app --reload --port 8003 --host 0.0.0.0
```

## ✅ 验证服务是否正确启动

### 1. 检查服务启动日志

启动后应该看到类似输出：
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8003
```

### 2. 测试API接口

在**另一个终端**中运行：

```bash
# 测试拼多多授权
curl -X POST http://localhost:8003/api/v1/system/pdd-login/start

# 期望看到包含 "success": true 的JSON响应
```

**正确的响应格式**：
```json
{
  "success": true,
  "message": "请使用拼多多商家版APP扫描二维码完成登录",
  "data": {
    "screenshot_url": "/api/v1/system/pdd-login/screenshot",
    "screenshot_path": "/app/data/pdd_login.png",
    "status": "waiting_scan"
  }
}
```

**如果看到旧格式**（没有success字段），说明缓存没清除干净：
```json
{
  "status": "success",  // 旧格式
  "message": "...",
  "screenshot_url": "..."
}
```

### 3. 测试抖音授权

```bash
curl -X POST http://localhost:8003/api/v1/system/douyin-login/start
```

应该看到类似的JSON响应（如果404说明路由没加载）。

### 4. 查看Swagger文档

浏览器打开：
```
http://localhost:8003/docs
```

应该能看到：
- `/api/v1/system/pdd-login/*` 系列接口
- `/api/v1/system/douyin-login/*` 系列接口

## 🧪 测试前端

### 1. 访问系统管理页面

```
http://localhost:5173/system
```

### 2. 测试拼多多授权

1. 找到"拼多多"（🛒图标）
2. 点击"授权"按钮
3. 点击"开始授权"
4. **应该能看到二维码**
5. 用拼多多商家版APP扫码

### 3. 测试抖音授权

1. 找到"抖音"（🎵图标）
2. 点击"授权"按钮  
3. 点击"开始授权"
4. **应该能看到二维码**
5. 用抖音APP扫码

## ❌ 如果还是失败

### 问题1：前端报错"Network Error"或"Failed to fetch"

**原因**：CORS问题或后端没启动

**检查**：
```bash
# 确认后端是否运行
curl http://localhost:8003/

# 应该返回：
# {"service":"拼多多客服自动化服务","version":"1.0.0","status":"running"}
```

### 问题2：点击授权按钮无反应

**打开浏览器开发者工具**（F12）：
1. 切换到 Console 标签
2. 点击"授权"按钮
3. 查看是否有错误信息

常见错误：
- `404 Not Found` → 路由没注册，确认后端重启
- `CORS error` → CORS配置问题
- `500 Internal Server Error` → 查看后端日志

### 问题3：后端报错

**查看后端终端的完整错误信息**，常见问题：

1. **ModuleNotFoundError: No module named 'douyin_bot'**
   - 确认文件存在：`ls services/pdd-cs-adapter/douyin_bot.py`
   - 确认已清除缓存

2. **ImportError in routes/__init__.py**
   - 确认 `routes/douyin_routes.py` 文件存在
   - 确认 `routes/__init__.py` 包含 `from .douyin_routes import router as douyin_router`

3. **Playwright browser not found**
   - 重新运行：`playwright install chromium`

## 🔍 调试命令

```bash
# 1. 确认文件存在
ls D:\phpEnv\www\ecom-automation\services\pdd-cs-adapter\douyin_bot.py
ls D:\phpEnv\www\ecom-automation\services\pdd-cs-adapter\routes\douyin_routes.py

# 2. 确认没有进程占用8003
netstat -ano | findstr :8003

# 3. 测试Python导入
cd D:\phpEnv\www\ecom-automation\services\pdd-cs-adapter
python -c "from douyin_bot import douyin_bot; print('OK')"

# 4. 测试路由导入
python -c "from routes import router; print('OK')"

# 5. 直接生成二维码测试
python -c "
import asyncio
from douyin_bot import douyin_bot
asyncio.run(douyin_bot.start_qr_login())
print('抖音二维码生成成功')
"
```

## 📞 需要帮助

如果按照以上步骤仍然失败，请提供：

1. **后端启动日志**（完整的终端输出）
2. **浏览器控制台错误**（F12 → Console标签的截图）
3. **curl测试结果**（上面的curl命令输出）

---

**当前状态**：
- ✅ Playwright已安装
- ✅ 二维码生成测试通过
- ✅ 旧进程已停止
- ✅ 缓存已清除
- ⏳ 等待重启服务

**下一步**：重启后端服务，然后测试授权流程
