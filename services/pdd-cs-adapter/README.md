# 拼多多客服自动化服务

基于 FastAPI 和 Playwright 的拼多多客服自动化服务，支持本地客服工作台账号密码授权登录、浏览器会话持久化，以及后续客服自动化能力扩展。

## 当前可用能力

- 本地打开可见浏览器发起拼多多商家工作台账号密码授权
- 从 `.env` 读取 `PDD_USERNAME` / `PDD_PASSWORD` 自动填入登录表单
- 用户手动完成滑块、短信或扫码确认等安全验证
- 轮询登录状态，成功后持久化浏览器会话并关闭浏览器
- 重启容器后复用已保存的会话文件
- 提供系统状态、配置、授权信息和浏览器自检接口

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
- `POST /api/v1/system/pdd-login/start` - 启动拼多多账号密码授权登录
- `GET /api/v1/system/pdd-login/status` - 查询账号密码授权登录状态
- `POST /api/v1/system/pdd-login/cancel` - 取消账号密码授权登录
- `POST /api/v1/system/pdd-login/password` - 兼容入口，同样启动账号密码授权登录
- `GET /api/v1/system/pdd-auth/status` - 查询拼多多持久授权状态
- `GET /api/v1/system/pdd-auth/info` - 查看授权信息 JSON，不返回 cookie 值
- `GET /api/v1/system/pdd-auth/page` - 查看授权信息 HTML 页面
- `POST /api/v1/system/test/browser` - 测试浏览器

## 账号密码授权流程

```text
1. POST /api/v1/system/pdd-login/start
2. 后端打开可见浏览器，访问拼多多商家工作台
3. 后端从 .env 自动填入 PDD_USERNAME / PDD_PASSWORD 并提交
4. 用户在浏览器里手动完成滑块、短信或扫码确认
5. GET /api/v1/system/pdd-login/status 轮询登录状态
6. 授权成功后自动保存 /app/data/pdd_storage_state.json 并关闭浏览器
7. 打开 /api/v1/system/pdd-auth/page 查看授权信息
```

## 配置说明

主要配置项：
- `PDD_CLIENT_ID` / `PDD_CLIENT_SECRET` - 拼多多开放平台 API 凭证，仅调用开放平台接口时需要
- `PDD_ACCESS_TOKEN` - 拼多多开放平台 Access Token，仅调用开放平台接口时需要
- `PDD_USERNAME` / `PDD_PASSWORD` - 拼多多商家后台账号密码，用于账号密码授权登录
- `PDD_DATA_DIR` - 浏览器会话持久化目录
- `AUTO_REPLY_ENABLED` - 是否启用自动回复
- `BROWSER_HEADLESS` - 是否使用无头浏览器
- `BROWSER_CONTROL_URL` - 远程浏览器入口；Docker Compose 默认是 `http://localhost:6080/vnc.html?autoconnect=true&resize=scale`

说明：
- 账号密码授权登录不依赖 `PDD_CLIENT_ID` / `PDD_CLIENT_SECRET`
- 如未配置 `PDD_DATA_DIR`，默认使用 `/app/data`
- 授权流程需要可见浏览器；Docker Compose 通过 noVNC 暴露容器内浏览器，端口只绑定本机 `127.0.0.1:6080`

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

1. 账号密码授权登录需要稳定网络环境和可见的 Playwright 浏览器
2. 建议持久化 `PDD_DATA_DIR`，否则容器重启后需要重新授权
3. 只有调用开放平台 API 时才需要申请拼多多开放平台权限
4. 建议定期检查日志和 `pdd_storage_state.json` 是否正常落盘

## License

MIT
