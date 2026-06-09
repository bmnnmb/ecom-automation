# Repository Guidelines

## 项目结构与模块组织

本仓库是多服务电商自动化系统。Python FastAPI 微服务位于 `services/`，每个服务独立成目录，例如 `api-gateway`、`oms-service`、`rag-service` 和各平台适配器。React 管理后台位于 `admin/`，源码在 `admin/src/`，静态资源在 `admin/src/assets/`。共享模型在 `shared/`。数据库初始化和迁移文件在 `database/`，脚本在 `scripts/`，项目文档在 `docs/`，生成的测试报告在 `test-reports/`。

### API 网关路由

api-gateway (端口 8000) 提供以下代理路由：
- `/api/products`、`/api/customers` → product-service:8006
- `/api/orders`、`/api/inventory`、`/api/tickets`、`/api/dashboard` → oms-service:8005
- `/api/finance`、`/api/supply-chain`、`/api/system`、`/api/messages`、`/api/competitors` → 本地种子数据

### 前端认证

前端使用 localStorage 存储 token 和用户信息，路由守卫在 `admin/src/router/index.jsx` 中实现。登录页面在 `admin/src/pages/Login/`。

## 构建、测试与开发命令

- `pip install -r requirements.txt`：安装根目录 Python 依赖。
- `make up-infra`：启动本地开发所需的 PostgreSQL 和 Redis。
- `make build`：构建所有 Docker Compose 服务镜像。
- `make up`：以后台模式启动完整本地服务栈。
- `make logs-svc SVC=api-gateway`：查看指定服务日志。
- `python scripts/run_tests.py`：运行仓库级集成与结构检查。
- `cd services/<service> && pytest test_*.py -v`：运行单个服务测试。
- `cd admin && npm install && npm run dev`：安装并启动 Vite 管理后台。
- `cd admin && npm run build`：构建管理后台前端。

## 编码风格与命名约定

使用 Python 3.11+，FastAPI 入口保持在 `main.py`。服务路由放在 `routes/`，模块名应清晰，例如 `order_routes.py` 或 `products.py`。测试文件使用 `test_*.py`。公共函数优先添加类型注解，请求和响应结构使用 Pydantic 模型，API 端点显式声明 `response_model`。管理后台 React 组件使用 PascalCase，页面相关 CSS 与页面模块放在一起。

项目整体以中文为主要协作语言。文档、说明、提交信息和 PR 描述应优先使用中文，保留必要的英文技术名词、命令、接口名和 Conventional Commits 类型前缀。

## 测试规范

修改端点、模型、数据库行为或平台适配器逻辑时，应新增或更新测试。优先编写隔离的服务测试和符合 `pytest` 约定的 API 测试。先运行受影响服务的测试，再对较大范围改动运行 `python scripts/run_tests.py`。

## 提交与 Pull Request 规范

Git 历史采用 Conventional Commits，常见格式包括 `feat(dashboard): ...`、`fix: ...`、`docs: ...`。提交应聚焦单一变更。PR 需要包含简短摘要、受影响服务、测试结果、相关 issue 或任务链接；涉及 `admin/` UI 改动时附截图。

## 安全与配置提示

本地配置从 `.env.example` 复制为 `.env`，不要提交凭证、Cookie、API Key 或生成的私有配置。平台凭证应通过环境变量读取。修改 Docker Compose 端口时需谨慎，因为服务路由和文档依赖稳定端口。
