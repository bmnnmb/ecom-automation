# Hermes 多平台电商自动化系统

基于 Hermes Agent 的多平台电商自动化运营系统，支持抖店、快手电商、拼多多、闲鱼四大平台。

## 系统架构

```
[ Hermes 总控 ]  :8080
    ├─ ecom-competitor-analyst skill
    ├─ ecom-selection-scorer skill
    ├─ ecom-product-copywriter skill
    ├─ ecom-cs-router skill
    ├─ ecom-aftersales-triage skill
    ├─ ecom-risk-watchdog skill
    └─ ecom-daily-report skill
            │
            ▼
[ Orchestrator ]  n8n :5678 + internal API + Redis Queue
            │
            ├───────────────┬───────────────┬───────────────┐
            ▼               ▼               ▼               ▼
  [平台适配器服务]   [抓取/RPA服务]    [知识库服务]      [OMS服务]
  Douyin :8001      Xianyu :8004      RAG :8006         OMS :8005
  Kuaishou :8002    PDD CS :8003
                    Crawler :8008
  [ API Gateway :8000 ]  [ Product Service :8006 ]
```

## 服务列表

| 服务 | 端口 | 技术栈 | 说明 |
|------|------|--------|------|
| api-gateway | 8000 | FastAPI | 统一REST API网关 |
| douyin-adapter | 8001 | FastAPI + 官方SDK | 抖店平台适配器 |
| kuaishou-adapter | 8002 | FastAPI + SDK | 快手平台适配器 |
| pdd-cs-adapter | 8003 | Python + Playwright | 拼多多客服自动化 |
| xianyu-adapter | 8004 | FastAPI + Playwright | 闲鱼自动化 |
| oms-service | 8005 | FastAPI + SQLAlchemy | 订单中台 (订单/库存/工单/看板) |
| rag-service | 8006 | FastAPI + pgvector | RAG 知识库检索 |
| hermes-control | 8080 | Python + Hermes | 总控、策略、调度、报表 |
| competitor-crawler | 8008 | Python asyncio | 竞品数据采集与分析 |
| product-service | 8006 | FastAPI + SQLAlchemy | 商品与分类管理 |

## 快速开始

```bash
# 克隆项目
git clone https://github.com/DMNO1/ecom-automation.git
cd ecom-automation

# 安装依赖
pip install -r requirements.txt

# 启动服务
docker-compose up -d
```

## 开发阶段

### 第1阶段 (2-3周)
- [ ] 抖店 Adapter 基础版
- [ ] 拼多多客服自动化
- [ ] 闲鱼自动回复系统
- [ ] PostgreSQL + Redis + n8n
- [ ] Hermes 4个核心 Skills

### 第2阶段 (3-6周)
- [ ] OMS 基础版
- [ ] 竞品爬虫标准化
- [ ] 商品上架文案生成
- [ ] 合规审核
- [ ] 快手 Adapter

### 第3阶段 (6-10周)
- [ ] 选品评分模型
- [ ] 风险预警模型
- [ ] 多店铺路由
- [ ] 管理后台和BI看板

## API 文档

系统包含 10 个微服务，共计 95+ 个 REST API 端点。

| 服务 | 端口 | 说明 | 交互式文档 |
|------|------|------|-----------|
| API Gateway | 8000 | 统一 API 网关 (代理层) | `http://localhost:8000/docs` |
| 抖店适配器 | 8001 | 抖店 OAuth + API | `http://localhost:8001/docs` |
| 快手适配器 | 8002 | 快手 OAuth + API | `http://localhost:8002/docs` |
| 拼多多客服 | 8003 | 客服自动化 | `http://localhost:8003/docs` |
| 闲鱼适配器 | 8004 | 闲鱼自动化 | `http://localhost:8004/docs` |
| OMS 服务 | 8005 | 订单中台 (订单/库存/工单/看板) | `http://localhost:8005/docs` |
| RAG 知识库 | 8006 | 知识检索 | `http://localhost:8006/docs` |
| Hermes 总控 | 8080 | 任务调度/技能执行/报表 | `http://localhost:8080/docs` |
| 竞品爬虫 | 8008 | 竞品数据采集与分析 | `http://localhost:8008/docs` |
| 商品服务 | 8006 | 商品/分类/客户管理 | `http://localhost:8006/docs` |

**主要 API 模块：**

- **统一鉴权** `/api/auth` — 多平台 OAuth2 授权流程（抖店/快手/拼多多/闲鱼）
- **店铺管理** `/api/shops` — 店铺 CRUD、平台配置
- **商品管理** `/api/products` — 商品 CRUD、状态管理、毛利计算（→product-service）
- **客户管理** `/api/customers` — 客户 CRUD、等级、标签（→product-service）
- **订单管理** `/api/orders` — 订单查询、状态流转、同步（→oms-service）
- **库存管理** `/api/inventory` — 库存查询、锁定/解锁、出入库（→oms-service）
- **工单管理** `/api/tickets` — 工单创建、分配、退款、投诉（→oms-service）
- **运营看板** `/api/dashboard` — 统计、趋势、概览、告警（→oms-service）
- **客服消息** `/api/messages` — 消息收发、回复
- **售后服务** `/api/aftersales` — 售后工单创建、处理
- **竞品分析** `/api/competitors` — 竞品数据采集与分析
- **报表统计** `/api/reports` — 日报/周报/月报生成
- **系统设置** `/api/settings` — 系统配置管理
- **RAG 检索** `/rag/query` — 知识库语义检索
- **竞品爬虫** `/crawl`, `/tasks`, `/analysis` — 数据采集与分析
- **任务调度** `/tasks`, `/skills`, `/goals` — Hermes 任务编排

> 📄 完整 API 文档：[docs/API.md](docs/API.md) | OpenAPI Spec：[docs/openapi.yaml](docs/openapi.yaml)

## 文档

| 文档 | 说明 |
|------|------|
| [docs/API.md](docs/API.md) | 完整 API 接口文档 |
| [docs/DEPLOY.md](docs/DEPLOY.md) | 部署指南 |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | 开发指南（环境搭建、编码规范、测试流程） |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | 故障排除指南（常见问题与解决方案） |
| [docs/openapi.yaml](docs/openapi.yaml) | OpenAPI 3.0 规范文件 |
| [CHANGELOG.md](CHANGELOG.md) | 项目变更日志 |
| [PROGRESS.md](PROGRESS.md) | 项目进度跟踪 |
| [BUG-TRACKING.md](BUG-TRACKING.md) | Bug 跟踪记录 |

## 技术栈

- **主语言**: Python
- **Web框架**: FastAPI
- **数据库**: PostgreSQL 15+
- **缓存/队列**: Redis
- **工作流**: n8n
- **浏览器自动化**: Playwright
- **AI Agent**: Hermes
- **知识库**: Dify/FastGPT + pgvector
- **部署**: Docker Compose

## 许可证

Private
