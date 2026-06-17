# 🛠 开发指南 - Hermes 电商自动化系统

> 本文档面向开发者，涵盖本地开发环境搭建、项目结构、编码规范、测试流程和常见问题。

---

## 目录

- [环境要求](#环境要求)
- [快速搭建本地开发环境](#快速搭建本地开发环境)
- [项目结构](#项目结构)
- [服务开发](#服务开发)
- [数据库开发](#数据库开发)
- [测试](#测试)
- [编码规范](#编码规范)
- [Git 工作流](#git-工作流)
- [常见问题](#常见问题)

---

## 环境要求

| 工具 | 版本要求 | 说明 |
|------|---------|------|
| Python | 3.11+ | 推荐 3.12 |
| Docker | 24+ | 基础设施和服务容器化 |
| Docker Compose | v2 | 编排多服务 |
| Git | 2.30+ | 版本管理 |
| Make | 3.81+ | 快捷命令（可选） |
| Node.js | 18+ | n8n 自定义节点开发（可选） |

---

## 快速搭建本地开发环境

### 1. 克隆项目

```bash
git clone https://github.com/DMNO1/ecom-automation.git
cd ecom-automation
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填写各平台 API Key 和密钥
vim .env
```

**关键环境变量：**

| 变量 | 说明 | 必填 |
|------|------|------|
| `DB_PASSWORD` | PostgreSQL 密码 | ✅ |
| `DOUYIN_APP_KEY` / `DOUYIN_APP_SECRET` | 抖店开放平台凭证 | 抖店开发时 |
| `KUAISHOU_APP_KEY` / `KUAISHOU_APP_SECRET` | 快手开放平台凭证 | 快手开发时 |
| `PDD_CLIENT_ID` / `PDD_CLIENT_SECRET` | 拼多多开放平台凭证 | 调试拼多多开放平台 API 时 |
| `PDD_DATA_DIR` | 拼多多扫码登录会话目录 | 调试本地客服工作台自动化时 |
| `XIANYU_COOKIE` | 闲鱼登录 Cookie | 闲鱼开发时 |
| `OPENAI_API_KEY` | OpenAI API Key | RAG/Hermes |

说明：
- 拼多多本地扫码登录不依赖 `PDD_CLIENT_ID` / `PDD_CLIENT_SECRET`
- 二维码截图和浏览器会话默认写入 `PDD_DATA_DIR`
- 管理后台可通过 `系统设置 -> 平台配置 -> 拼多多扫码登录` 直接发起联调

### 3. 启动基础设施

```bash
# 仅启动 PostgreSQL + Redis（日常开发推荐）
make up-infra

# 或直接用 docker compose
docker compose up -d postgres redis
```

### 4. 启动单个服务（本地开发）

```bash
# 进入服务目录
cd services/competitor-crawler

# 创建虚拟环境
python -m venv venv
source venv/bin/activate   # macOS/Linux
# venv\Scripts\activate    # Windows

# 安装依赖
pip install -r requirements.txt

# 启动服务（热重载）
uvicorn main:app --reload --port 8000
```

### 5. 启动全部服务（Docker）

```bash
make build    # 构建所有镜像
make up       # 启动所有服务
make health   # 检查所有服务健康状态
```

---

## 项目结构

```
ecom-automation/
├── README.md                  # 项目概览
├── Makefile                   # 快捷命令
├── docker-compose.yml         # 服务编排
├── .env.example               # 环境变量模板
├── requirements.txt           # 全局 Python 依赖
├── database/
│   ├── init.sql               # 数据库初始化脚本
│   └── migrations/            # Alembic 迁移文件
├── scripts/                   # 运维脚本
│   ├── run_tests.py           # 集成测试运行器
│   └── auto_merge_jules.py    # Jules 自动合并
├── docs/
│   ├── API.md                 # API 文档
│   ├── DEPLOY.md              # 部署指南
│   ├── DEVELOPMENT.md         # 开发指南（本文档）
│   └── openapi.yaml           # OpenAPI 规范
└── services/                  # 微服务目录
    ├── api-gateway/           # 统一 API 网关 (端口 8000)
    ├── douyin-adapter/        # 抖店适配器 (端口 8001)
    ├── kuaishou-adapter/      # 快手适配器 (端口 8002)
    ├── pdd-cs-adapter/        # 拼多多客服 (端口 8003)
    ├── xianyu-adapter/        # 闲鱼适配器 (端口 8004)
    ├── oms-service/           # 订单中台 (端口 8005)
    ├── rag-service/           # RAG 知识库 (端口 8006)
    ├── hermes-control/        # Hermes 总控 (端口 8007)
    ├── competitor-crawler/    # 竞品爬虫 (端口 8008)
    └── product-service/       # 商品服务
```

### 服务目录结构规范

每个服务遵循统一结构：

```
services/<service-name>/
├── main.py              # FastAPI 应用入口
├── models.py            # SQLAlchemy / Pydantic 模型
├── requirements.txt     # 服务级依赖
├── Dockerfile           # 容器构建
├── README.md            # 服务说明
├── routes/              # API 路由（可选拆分）
├── utils/               # 工具函数（可选）
└── test_*.py            # 测试文件
```

---

## 服务开发

### 添加新端点

1. 在 `main.py` 或 `routes/` 下添加路由：

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/example", tags=["示例"])

class ExampleResponse(BaseModel):
    id: int
    name: str

@router.get("/{item_id}", response_model=ExampleResponse)
async def get_example(item_id: int):
    """获取示例数据"""
    # 实现逻辑
    return ExampleResponse(id=item_id, name="示例")
```

2. 如果使用独立路由文件，在 `main.py` 中注册：

```python
from routes.example import router as example_router
app.include_router(example_router)
```

### 平台适配器开发规范

所有平台适配器（douyin、kuaishou、pdd、xianyu）遵循相同模式：

```
┌──────────┐     ┌──────────────┐     ┌─────────────┐
│ 客户端请求 │ ──▶ │  Adapter API  │ ──▶ │ 平台 SDK/API │
└──────────┘     └──────────────┘     └─────────────┘
                        │
                  ┌─────┴─────┐
                  │  统一模型    │
                  │  (Pydantic) │
                  └───────────┘
```

**关键组件：**
- `auth.py` — OAuth2 授权流程
- `*_client.py` — 平台 API 封装
- `models.py` — 数据模型定义
- `routes/` — API 端点

### 环境变量注入

服务通过环境变量获取配置，Docker Compose 中已预设：

```yaml
environment:
  DATABASE_URL: postgresql://ecom:${DB_PASSWORD}@postgres:5432/ecom_automation
  REDIS_URL: redis://redis:6379/<db_number>
  LOG_LEVEL: ${LOG_LEVEL:-INFO}
```

本地开发时可直接 `export` 或使用 `.env` 文件配合 `python-dotenv`。

---

## 数据库开发

### 连接数据库

```bash
# Docker 内 PostgreSQL
docker compose exec postgres psql -U ecom -d ecom_automation

# 本地连接
psql -h localhost -p 5432 -U ecom -d ecom_automation
```

### 迁移管理

```bash
# 生成迁移文件
cd services/<service>
alembic revision --autogenerate -m "描述变更"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

### 数据库初始化

首次启动时，`database/init.sql` 会自动执行，创建基础表结构和初始数据。

---

## 测试

### 单元测试

```bash
# 在服务目录下运行
cd services/<service>
pytest test_*.py -v

# 带覆盖率
pytest test_*.py -v --cov=. --cov-report=html
```

### 集成测试

```bash
# 确保所有服务已启动
make up

# 运行集成测试
python scripts/run_tests.py
```

### API 测试

每个服务的 `test_api.py` 包含端到端 API 测试：

```bash
cd services/competitor-crawler
pytest test_api.py -v
```

### 测试规范

- 每个服务至少包含 `test_api.py`（API 端点测试）
- 测试使用 `httpx.AsyncClient` 或 `TestClient`
- Mock 外部依赖（平台 API、数据库）
- 测试文件命名：`test_<module>.py`

---

## 编码规范

### Python 风格

- **格式化**: Black（行宽 88）
- **导入排序**: isort
- **类型注解**: 所有公共函数必须有类型注解
- **文档字符串**: Google 风格 docstring

```python
async def fetch_product(product_id: str, platform: str) -> dict:
    """从指定平台获取商品信息。

    Args:
        product_id: 商品 ID
        platform: 平台名称 (douyin/kuaishou/pdd/xianyu)

    Returns:
        商品信息字典

    Raises:
        HTTPException: 平台 API 调用失败
    """
```

### FastAPI 规范

- 所有端点必须有 `response_model`
- 所有端点必须有 `tags` 分组
- 错误响应使用 `HTTPException`，包含有意义的错误消息
- 使用 `Depends` 注入共享依赖

### 提交规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/)：

```
feat: 新功能
fix: 修复 bug
docs: 文档更新
refactor: 重构
test: 测试相关
chore: 构建/工具变更
```

---

## Git 工作流

### 分支策略

```
main          ← 生产就绪代码
├── develop   ← 开发主线
├── feat/*    ← 功能分支
├── fix/*     ← 修复分支
└── docs/*    ← 文档分支
```

### 开发流程

```bash
# 1. 从 develop 创建功能分支
git checkout develop
git pull origin develop
git checkout -b feat/my-feature

# 2. 开发并提交
git add -A
git commit -m "feat: 添加 XXX 功能"

# 3. 推送并创建 PR
git push origin feat/my-feature
# 在 GitHub 创建 PR -> develop

# 4. 合并后删除分支
git checkout develop
git pull origin develop
git branch -d feat/my-feature
```

---

## 常见问题

### Q: 服务启动报 `Connection refused` 错误？

确保基础设施已启动：
```bash
make up-infra
# 等待 PostgreSQL 和 Redis 就绪
docker compose ps
```

### Q: 如何只重启某个服务？

```bash
# Docker 方式
docker compose restart <service-name>

# 本地方式：直接 Ctrl+C 后重新运行 uvicorn
```

### Q: 如何查看服务日志？

```bash
# 所有服务
make logs

# 指定服务
docker compose logs -f <service-name>

# 最近 100 行
docker compose logs --tail=100 <service-name>
```

### Q: 如何连接到 Docker 内的 Redis？

```bash
docker compose exec redis redis-cli

# 选择特定 DB（各服务使用独立 DB）
SELECT 0   # api-gateway
SELECT 1   # douyin-adapter
SELECT 2   # kuaishou-adapter
# ... 参见 docker-compose.yml 中的 REDIS_URL
```

### Q: Playwright 浏览器自动化服务如何调试？

```bash
# 安装浏览器（首次）
playwright install chromium

# 有头模式调试（本地）
HEADLESS=false uvicorn main:app --reload

# Docker 中需要挂载 /dev/shm
# docker-compose.yml 中已配置 shm_size
```

### Q: 如何联调拼多多扫码登录？

```bash
# 启动拼多多客服适配器
cd services/pdd-cs-adapter
uvicorn main:app --reload --port 8003

# 触发二维码生成
curl -X POST http://localhost:8003/api/v1/system/pdd-login/start

# 查询登录状态
curl http://localhost:8003/api/v1/system/pdd-login/status
```

如需从前端联调，进入管理后台 `系统设置 -> 平台配置 -> 拼多多扫码登录` 即可。

### Q: 如何添加新平台适配器？

1. 复制现有适配器目录（推荐从 `kuaishou-adapter` 开始）
2. 修改 `main.py` 中的服务名和端口
3. 更新 `auth.py` 中的 OAuth 流程
4. 实现 `*_client.py` 中的平台 API 封装
5. 在 `docker-compose.yml` 中添加服务配置
6. 在 `api-gateway` 中注册路由转发
7. 更新本文档和 `README.md`

---

## 端口分配速查

| 端口 | 服务 | Redis DB |
|------|------|----------|
| 5432 | PostgreSQL | — |
| 6379 | Redis | 0-15 |
| 3001 | Metabase | — |
| 5678 | n8n | — |
| 8000 | API Gateway | 0 |
| 8001 | 抖店适配器 | 1 |
| 8002 | 快手适配器 | 2 |
| 8003 | 拼多多客服 | 3 |
| 8004 | 闲鱼适配器 | 4 |
| 8005 | OMS 服务 | 5 |
| 8006 | RAG 服务 | 6 |
| 8007 | Hermes 总控 | 7 |
| 8008 | 竞品爬虫 | 8 |

---

## 有用的 Make 命令

```bash
make help           # 显示所有可用命令
make build          # 构建所有镜像
make build-svc SVC=api-gateway  # 构建指定服务
make up             # 启动所有服务
make up-infra       # 仅启动基础设施
make down           # 停止所有服务
make restart        # 重启所有服务
make logs           # 查看日志
make ps             # 查看运行状态
make health         # 健康检查
make clean          # 清理容器和镜像
make backup         # 数据库备份
make restore        # 数据库恢复
```
