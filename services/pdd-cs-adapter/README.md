# 拼多多客服自动化服务

基于 FastAPI 和 Playwright 的拼多多客服自动化服务，支持本地客服工作台扫码登录、浏览器会话持久化，以及后续客服自动化能力扩展。

## 当前可用能力

- 本地发起拼多多商家工作台扫码登录
- 保存二维码截图，供管理后台直接展示
- 轮询登录状态并持久化浏览器会话
- 重启容器后复用已保存的会话文件
- 提供系统状态、配置和浏览器自检接口

## 项目结构

```
pdd-cs-adapter/
├── main.py              # 主入口
├── config.py            # 配置管理
├── pdd_client.py        # 拼多多API客户端
├── message_handler.py   # 消息处理逻辑
├── playwright_bot.py    # 浏览器自动化
├── knowledge_base.py    # 客服知识库
├── routes/              # API路由
│   ├── __init__.py
│   ├── chat_routes.py   # 聊天相关API
│   ├── knowledge_routes.py  # 知识库管理API
│   └── system_routes.py     # 系统管理API
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入实际配置
```

### 3. 启动服务

```bash
uvicorn main:app --reload --port 8003
```

### 4. 使用Docker部署

```bash
docker build -t pdd-cs-adapter .
docker run -p 8003:8003 --env-file .env -v $(pwd)/data:/app/data pdd-cs-adapter
```

## API文档

启动服务后访问：
- Swagger UI: http://localhost:8003/docs
- ReDoc: http://localhost:8003/redoc

## 主要API端点

### 聊天相关
- `GET /api/v1/chat/conversations` - 获取会话列表
- `POST /api/v1/chat/messages` - 处理消息
- `POST /api/v1/chat/auto-reply/start` - 启动自动回复

### 知识库管理
- `GET /api/v1/knowledge/faq` - 获取所有FAQ
- `POST /api/v1/knowledge/faq` - 创建FAQ
- `POST /api/v1/knowledge/search` - 搜索知识库

### 系统管理
- `GET /api/v1/system/status` - 获取系统状态
- `GET /api/v1/system/config` - 获取配置
- `POST /api/v1/system/pdd-login/start` - 启动拼多多扫码登录
- `GET /api/v1/system/pdd-login/screenshot` - 获取当前二维码截图
- `GET /api/v1/system/pdd-login/status` - 查询扫码登录状态
- `POST /api/v1/system/pdd-login/cancel` - 取消扫码登录
- `POST /api/v1/system/test/browser` - 测试浏览器

## 扫码登录流程

```text
1. POST /api/v1/system/pdd-login/start
2. 打开 /api/v1/system/pdd-login/screenshot 获取二维码截图
3. 用户扫码并在拼多多侧确认
4. GET /api/v1/system/pdd-login/status 轮询登录状态
5. 登录成功后自动保存 /app/data/pdd_storage_state.json
```

## 配置说明

主要配置项：
- `PDD_CLIENT_ID` / `PDD_CLIENT_SECRET` - 拼多多开放平台 API 凭证，仅调用开放平台接口时需要
- `PDD_ACCESS_TOKEN` - 拼多多开放平台 Access Token，仅调用开放平台接口时需要
- `PDD_DATA_DIR` - 扫码登录二维码截图与浏览器会话持久化目录
- `AUTO_REPLY_ENABLED` - 是否启用自动回复
- `BROWSER_HEADLESS` - 是否使用无头浏览器

说明：
- 本地扫码登录不依赖 `PDD_CLIENT_ID` / `PDD_CLIENT_SECRET`
- 如未配置 `PDD_DATA_DIR`，默认使用 `/app/data`
- `PDD_USERNAME` / `PDD_PASSWORD` 仍可用于代码内其他登录流程，但不是当前扫码登录能力的前置条件

## 开发说明

### 消息处理流程
1. 浏览器自动化读取工作台消息
2. 消息处理器分析风险等级
3. 低风险消息自动匹配知识库回复
4. 高风险消息转人工处理
5. 记录处理结果和指标

### 风险分级规则
- 低风险：普通咨询，可自动回复
- 中风险：需关注但可尝试自动回复
- 高风险：投诉、举报等，必须转人工

## 注意事项

1. 本地扫码登录需要稳定网络环境和可用的 Playwright 浏览器
2. 建议持久化 `PDD_DATA_DIR`，否则容器重启后需要重新扫码
3. 只有调用开放平台 API 时才需要申请拼多多开放平台权限
4. 建议定期检查日志和 `pdd_storage_state.json` 是否正常落盘

## License

MIT
