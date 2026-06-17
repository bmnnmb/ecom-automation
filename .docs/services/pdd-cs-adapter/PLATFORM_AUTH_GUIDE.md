# 平台授权完整链路测试文档

## 概述

本文档描述拼多多和抖音平台的授权完整实现，包括前端UI、后端API和Playwright自动化。

## 技术架构

### 后端服务 (pdd-cs-adapter)
- **框架**: FastAPI + Playwright
- **端口**: 8003
- **平台支持**: 拼多多、抖音

### 前端管理后台
- **框架**: React + Ant Design
- **端口**: 5173
- **入口**: http://localhost:5173/system

## 一、拼多多授权

### 1.1 后端实现

#### 核心文件
- `playwright_bot.py` - 拼多多浏览器自动化
- `routes/system_routes.py` - 拼多多授权API

#### API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/system/pdd-login/start` | POST | 启动扫码登录 |
| `/api/v1/system/pdd-login/screenshot` | GET | 获取二维码截图 |
| `/api/v1/system/pdd-login/status` | GET | 查询登录状态 |
| `/api/v1/system/pdd-login/cancel` | POST | 取消登录 |
| `/api/v1/system/pdd-logout` | POST | 解绑授权 |

#### 工作原理
1. Playwright 启动 Chromium 浏览器
2. 访问拼多多商家工作台 `https://mms.pinduoduo.com`
3. 截取二维码页面保存为 `data/pdd_login.png`
4. 检测页面元素判断登录状态
5. 登录成功后保存会话到 `data/pdd_storage_state.json`

### 1.2 前端实现

#### 核心文件
- `src/pages/System/index.jsx` - 系统管理主页
- `src/pages/System/PddAuthModal.jsx` - 拼多多授权弹窗

#### 授权流程
1. 点击"授权"按钮 → 打开授权弹窗
2. 点击"开始授权" → 调用后端生成二维码
3. 展示二维码 → 用户用拼多多商家版APP扫码
4. 自动轮询（每2秒）→ 检测登录状态
5. 登录成功 → 更新状态为"已授权"

### 1.3 测试步骤

```bash
# 1. 启动后端服务
cd D:\phpEnv\www\ecom-automation\services\pdd-cs-adapter
uvicorn main:app --reload --port 8003

# 2. 启动前端
cd D:\phpEnv\www\ecom-automation\admin
npm run dev

# 3. 访问系统管理页面
http://localhost:5173/system

# 4. 测试授权流程
# - 找到"拼多多"，点击"授权"
# - 用手机APP扫码
# - 确认登录成功
```

## 二、抖音授权

### 2.1 后端实现

#### 核心文件
- `douyin_bot.py` - 抖音浏览器自动化
- `routes/douyin_routes.py` - 抖音授权API

#### API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/system/douyin-login/start` | POST | 启动扫码登录 |
| `/api/v1/system/douyin-login/screenshot` | GET | 获取二维码截图 |
| `/api/v1/system/douyin-login/status` | GET | 查询登录状态 |
| `/api/v1/system/douyin-login/cancel` | POST | 取消登录 |
| `/api/v1/system/douyin-logout` | POST | 解绑授权 |

#### 工作原理
1. Playwright 启动 Chromium 浏览器
2. 访问抖音商家后台 `https://fxg.jinritemai.com`
3. 截取二维码页面保存为 `data/douyin_login.png`
4. 检测页面元素判断登录状态
5. 登录成功后保存会话到 `data/douyin_storage_state.json`

### 2.2 前端实现

#### 核心文件
- `src/pages/System/index.jsx` - 系统管理主页
- `src/pages/System/DouyinAuthModal.jsx` - 抖音授权弹窗

#### 授权流程
1. 点击"授权"按钮 → 打开授权弹窗
2. 点击"开始授权" → 调用后端生成二维码
3. 展示二维码 → 用户用抖音APP扫码
4. 自动轮询（每2秒）→ 检测登录状态
5. 登录成功 → 更新状态为"已授权"

### 2.3 测试步骤

```bash
# 使用与拼多多相同的前后端服务

# 测试授权流程
# - 找到"抖音"，点击"授权"
# - 用抖音APP扫码
# - 确认登录成功
```

## 三、统一API返回格式

所有授权接口使用统一的返回格式：

### 成功响应
```json
{
  "success": true,
  "message": "操作成功",
  "data": {
    "is_logged_in": true,
    "status": "logged_in",
    "screenshot_url": "/api/v1/system/xxx-login/screenshot"
  }
}
```

### 失败响应
```json
{
  "success": false,
  "message": "错误信息",
  "data": null
}
```

### 登录状态枚举
- `waiting_scan` - 等待扫码
- `logged_in` - 已登录
- `failed` - 登录失败
- `timeout` - 超时

## 四、目录结构

```
services/pdd-cs-adapter/
├── main.py                          # FastAPI主入口
├── config.py                        # 配置管理
├── playwright_bot.py                # 拼多多自动化
├── douyin_bot.py                    # 抖音自动化 ⭐新增
├── routes/
│   ├── __init__.py                  # 路由注册
│   ├── system_routes.py             # 拼多多授权API
│   └── douyin_routes.py             # 抖音授权API ⭐新增
└── data/
    ├── pdd_storage_state.json       # 拼多多会话
    ├── pdd_login.png                # 拼多多二维码
    ├── douyin_storage_state.json    # 抖音会话 ⭐新增
    └── douyin_login.png             # 抖音二维码 ⭐新增

admin/src/pages/System/
├── index.jsx                        # 系统管理主页（已更新）
├── PddAuthModal.jsx                 # 拼多多授权弹窗
├── DouyinAuthModal.jsx              # 抖音授权弹窗 ⭐新增
└── README.md                        # 使用文档
```

## 五、核心代码片段

### 5.1 浏览器自动化模板

```python
class PlatformBot:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.is_logged_in = False
        self.storage_state_path = Path("data/platform_storage_state.json")
        self.login_screenshot_path = Path("data/platform_login.png")
    
    async def start_qr_login(self) -> str:
        """启动二维码登录"""
        await self.start()
        await self.page.goto(PLATFORM_URL)
        await self.capture_login_screenshot()
        return str(self.login_screenshot_path)
    
    async def check_login_status(self) -> bool:
        """检查登录状态"""
        # 检测登录标识
        login_markers = ['text=扫码登录', '.qrcode']
        for marker in login_markers:
            if await self.page.locator(marker).count() > 0:
                return False
        
        # 检测已登录标识
        auth_markers = ['text=店铺', '[class*="avatar"]']
        for marker in auth_markers:
            if await self.page.locator(marker).count() > 0:
                await self.save_storage_state()
                self.is_logged_in = True
                return True
        
        return False
```

### 5.2 前端授权弹窗模板

```jsx
export default function PlatformAuthModal({ visible, onCancel, onSuccess }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [polling, setPolling] = useState(false);
  
  const startQrLogin = async () => {
    const response = await fetch(`${API_BASE}/api/v1/system/platform-login/start`, {
      method: 'POST'
    });
    const result = await response.json();
    if (result.success) {
      setQrCodeUrl(`${API_BASE}${result.data.screenshot_url}`);
      startPollingStatus();
    }
  };
  
  const startPollingStatus = () => {
    const timer = setInterval(async () => {
      const response = await fetch(`${API_BASE}/api/v1/system/platform-login/status`);
      const result = await response.json();
      if (result.data.is_logged_in) {
        clearInterval(timer);
        onSuccess();
      }
    }, 2000);
  };
  
  return (
    <Modal title="平台授权" open={visible} onCancel={onCancel}>
      <Steps current={currentStep} />
      {/* 渲染步骤内容 */}
    </Modal>
  );
}
```

## 六、常见问题

### 6.1 二维码加载失败
**原因**: 后端服务未启动或网络问题  
**解决**: 检查服务状态 `curl http://localhost:8003/api/v1/system/status`

### 6.2 扫码后一直"等待确认"
**原因**: 
- 未在APP中点击"确认登录"
- 页面元素检测失败

**解决**:
- 确认APP中完成授权操作
- 查看后端日志排查元素选择器问题
- 手动访问商家后台确认页面结构

### 6.3 会话持久化失败
**原因**: data 目录权限问题

**解决**:
```bash
# 确保 data 目录存在且可写
mkdir -p data
chmod 755 data
```

### 6.4 容器环境下浏览器启动失败
**原因**: 缺少浏览器依赖或 Chromium 未安装

**解决**:
```bash
# 安装 Playwright 浏览器
playwright install chromium
playwright install-deps
```

## 七、安全注意事项

1. **会话文件保护**: `*_storage_state.json` 包含登录凭证，不应提交到版本控制
2. **CORS 配置**: 生产环境应限制允许的域名
3. **敏感数据**: API Key、Secret 使用环境变量管理
4. **定期更新**: 电商平台可能更新页面结构，需要维护元素选择器

## 八、扩展新平台

添加新平台授权只需3步：

1. **创建 Bot 类** (`platform_bot.py`)
```python
class NewPlatformBot:
    PLATFORM_URL = "https://platform.example.com"
    # 实现 start_qr_login, check_login_status 等方法
```

2. **创建 API 路由** (`routes/platform_routes.py`)
```python
@router.post("/platform-login/start")
async def start_platform_login():
    # 调用 bot.start_qr_login()
```

3. **创建前端弹窗** (`PlatformAuthModal.jsx`)
```jsx
// 复制现有弹窗组件，修改 API 地址
```

## 九、性能优化

- **浏览器复用**: 登录后保持浏览器实例，避免频繁启动
- **截图优化**: 只截取二维码区域而非全屏
- **轮询间隔**: 根据平台响应速度调整（建议2-3秒）
- **超时处理**: 设置合理的超时时间（建议2分钟）

## 十、测试清单

- [ ] 后端服务启动成功
- [ ] 前端页面正常加载
- [ ] 拼多多授权流程完整
- [ ] 抖音授权流程完整
- [ ] 解绑功能正常
- [ ] 会话持久化有效
- [ ] 容器重启后会话复用
- [ ] 错误提示清晰准确
- [ ] 超时机制正常工作
- [ ] API返回格式统一

## 相关资源

- [拼多多开放平台](https://open.pinduoduo.com/)
- [抖音开放平台](https://developer.open-douyin.com/)
- [Playwright文档](https://playwright.dev/python/)
- [FastAPI文档](https://fastapi.tiangolo.com/)
