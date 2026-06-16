# 拼多多和抖音登录功能实现

## 功能概述

本项目实现了拼多多和抖音商家后台的 Playwright 自动化登录方案，支持两种登录方式：

1. **扫码登录**（推荐）- 适用于拼多多和抖音
2. **账号密码登录**（备用）- 抖音支持，拼多多可能受限

## 文件说明

### 核心文件

- `config.py` - 配置管理，支持从 `.env` 和 `.env.local` 加载配置
- `playwright_bot.py` - 拼多多浏览器自动化
- `douyin_bot.py` - 抖音浏览器自动化
- `routes/system_routes.py` - 拼多多登录API路由
- `routes/douyin_routes.py` - 抖音登录API路由

### 配置文件

- `.env.local` - **本地配置文件（已加入.gitignore，不会上传到Git）**
  - 存储账号密码等敏感信息
  - 优先级高于 `.env`

### 测试文件

- `test_qr_code_login.py` - 扫码登录测试脚本
- `test_auto_login.py` - 账号密码登录测试脚本
- `test_login.py` - 交互式测试脚本

## 配置说明

### 1. 创建本地配置文件

`.env.local` 文件已创建，包含以下配置：

```env
# 拼多多账号密码
PDD_USERNAME=pddzhh1122
PDD_PASSWORD=pdd1122!

# 抖音账号密码（如需要）
DOUYIN_USERNAME=
DOUYIN_PASSWORD=

# 浏览器配置
BROWSER_HEADLESS=false

# 数据存储目录
PDD_DATA_DIR=./data
```

### 2. 安全性

- `.env.local` 文件已添加到 `.gitignore`，不会被Git跟踪
- 会话文件 `*_storage_state.json` 也已添加到 `.gitignore`
- 数据目录 `data/` 包含的截图和会话文件不会上传

## API接口

### 拼多多登录接口

#### 1. 启动扫码登录
```
POST /api/v1/system/pdd-login/start
```
返回二维码截图路径，前端展示二维码供用户扫描

#### 2. 检查登录状态
```
GET /api/v1/system/pdd-login/status
```
轮询此接口检查用户是否已扫码登录

#### 3. 获取二维码截图
```
GET /api/v1/system/pdd-login/screenshot
```
返回二维码图片

#### 4. 取消登录
```
POST /api/v1/system/pdd-login/cancel
```
关闭登录浏览器

#### 5. 账号密码登录（备用）
```
POST /api/v1/system/pdd-login/password
```
使用配置的账号密码登录

#### 6. 获取授权状态
```
GET /api/v1/system/pdd-auth/status
```
检查是否已持久化登录（会话文件是否存在）

#### 7. 登出
```
POST /api/v1/system/pdd-logout
```
删除会话文件，解除授权

### 抖音登录接口

#### 1. 启动扫码登录
```
POST /api/v1/system/douyin-login/start
```

#### 2. 检查登录状态
```
GET /api/v1/system/douyin-login/status
```

#### 3. 获取二维码截图
```
GET /api/v1/system/douyin-login/screenshot
```

#### 4. 取消登录
```
POST /api/v1/system/douyin-login/cancel
```

#### 5. 账号密码登录
```
POST /api/v1/system/douyin-login/password
```

#### 6. 获取授权状态
```
GET /api/v1/system/douyin-auth/status
```

#### 7. 登出
```
POST /api/v1/system/douyin-logout
```

## 使用方法

### 方法一：通过API（推荐）

1. 启动服务：
```bash
cd services/pdd-cs-adapter
python main.py
```

2. 调用API进行登录（扫码或密码）

### 方法二：通过测试脚本

#### 测试扫码登录：
```bash
cd services/pdd-cs-adapter
python test_qr_code_login.py
```

#### 测试账号密码登录：
```bash
cd services/pdd-cs-adapter
python test_auto_login.py
```

## 技术实现

### 登录流程

#### 扫码登录流程：
1. 启动Playwright浏览器（非无头模式）
2. 访问平台登录页面
3. 截取包含二维码的页面截图
4. 前端展示二维码
5. 轮询检查页面URL和DOM元素判断登录状态
6. 登录成功后保存浏览器会话状态（cookies、localStorage等）
7. 关闭浏览器或保持打开

#### 账号密码登录流程：
1. 启动Playwright浏览器
2. 访问登录页面
3. 尝试切换到账号密码登录模式（如果有切换按钮）
4. 智能匹配用户名和密码输入框（支持多种选择器）
5. 填入账号密码
6. 点击登录按钮
7. 轮询检查登录状态
8. 保存会话状态

### 会话持久化

- 使用Playwright的 `storage_state` 功能保存登录会话
- 会话文件保存在 `data/` 目录：
  - `pdd_storage_state.json` - 拼多多会话
  - `douyin_storage_state.json` - 抖音会话
- 下次启动时自动加载会话，无需重新登录

### 登录状态检测

通过多种方式判断登录成功：
- DOM元素检测（用户头像、店铺名称等）
- URL模式匹配（是否跳转到工作台）
- 登录标记反向检测（二维码、登录按钮消失）

## 注意事项

1. **拼多多账号密码登录**
   - 拼多多商家后台主要使用扫码登录
   - 账号密码登录可能受平台限制或需要额外验证
   - 建议优先使用扫码登录

2. **验证码处理**
   - 当前版本不支持自动处理验证码
   - 如果登录需要验证码，会超时失败
   - 建议使用扫码登录避免验证码

3. **浏览器配置**
   - 测试和首次登录建议设置 `BROWSER_HEADLESS=false`
   - 生产环境可设置为 `true`（无头模式）

4. **安全性**
   - 切勿将 `.env.local` 文件提交到Git
   - 定期更新密码
   - 会话文件具有等同登录态的权限，妥善保管

## 错误处理

代码包含完善的错误处理：
- 网络超时自动重试
- 浏览器意外关闭自动检测
- 登录失败生成错误截图（保存在`data/`目录）
- 友好的错误消息映射

## 依赖项

- Python 3.8+
- FastAPI
- Playwright
- Pydantic
- 其他依赖见 `requirements.txt`

## 后续优化建议

1. 添加验证码识别功能（OCR或第三方服务）
2. 支持多账号管理
3. 增加登录失败重试机制
4. 添加登录成功的Webhook通知
5. 实现会话自动刷新
