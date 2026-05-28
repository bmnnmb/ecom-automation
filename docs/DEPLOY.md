# 🐳 部署指南 - Hermes 电商自动化系统

## 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Compose                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Postgres │  │  Redis   │  │   n8n    │  │ Metabase │        │
│  │  :5432   │  │  :6379   │  │  :5678   │  │  :3001   │        │
│  └────┬─────┘  └────┬─────┘  └──────────┘  └──────────┘        │
│       │             │                                           │
│  ┌────┴─────────────┴──────────────────────────────────────┐    │
│  │                    ecom-network                          │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │                                                         │    │
│  │  :8000 api-gateway    :8001 douyin-adapter              │    │
│  │  :8002 kuaishou-adapter  :8003 pdd-cs-adapter           │    │
│  │  :8004 xianyu-adapter    :8005 oms-service              │    │
│  │  :8006 rag-service       :8007 hermes-control           │    │
│  │  :8008 competitor-crawler                               │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## 快速开始

### 前置要求

- Docker >= 20.10
- Docker Compose >= 2.0 (V2 plugin, 不再需要独立安装 docker-compose)
- 至少 4GB 可用内存
- 至少 10GB 可用磁盘空间

### 1. 配置环境变量

```bash
cd ~/ecom-automation
cp .env.example .env
# 编辑 .env 填入实际的 API Key 和密钥
vim .env
```

**必填变量:**
- `DB_PASSWORD` — PostgreSQL 密码（默认 ecom2024，生产环境务必修改）

**按需变量（对应平台功能才需要）:**
- `DOUYIN_APP_KEY` / `DOUYIN_APP_SECRET` — 抖店
- `KUAISHOU_APP_KEY` / `KUAISHOU_APP_SECRET` — 快手
- `PDD_CLIENT_ID` / `PDD_CLIENT_SECRET` / `PDD_ACCESS_TOKEN` — 拼多多
- `XIANYU_COOKIE` — 闲鱼
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` — AI 功能

### 2. 启动所有服务

```bash
# 构建并启动（首次运行，需要构建镜像）
docker compose up -d --build

# 仅启动（镜像已构建）
docker compose up -d

# 仅启动基础设施（数据库 + 缓存）
docker compose up -d postgres redis

# 启动特定服务及其依赖
docker compose up -d api-gateway oms-service
```

### 3. 验证服务状态

```bash
# 查看所有容器状态
docker compose ps

# 检查服务健康状态（表格格式）
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

# 查看所有服务日志
docker compose logs -f

# 查看单个服务日志
docker compose logs -f api-gateway
docker compose logs -f --tail=50 oms-service
```

### 4. 访问服务

| 服务 | 端口 | 说明 | Health 端点 |
|------|------|------|-------------|
| API 网关 | http://localhost:8000 | 主入口，API 文档: /docs | /health |
| 抖店适配器 | http://localhost:8001 | 抖店平台对接 | /health |
| 快手适配器 | http://localhost:8002 | 快手平台对接 | /health |
| 拼多多客服 | http://localhost:8003 | 拼多多客服自动化 | /health |
| 闲鱼适配器 | http://localhost:8004 | 闲鱼平台对接 | /health |
| OMS 服务 | http://localhost:8005 | 订单管理系统 | /health |
| RAG 服务 | http://localhost:8006 | 知识库检索 | /health |
| Hermes 控制 | http://localhost:8007 | AI 控制中心 | /health |
| 竞品爬虫 | http://localhost:8008 | 竞品数据采集 | /health |
| n8n | http://localhost:5678 | 工作流引擎 | /healthz |
| Metabase | http://localhost:3001 | 数据可视化 | /api/health |
| PostgreSQL | localhost:5432 | 数据库 | pg_isready |
| Redis | localhost:6379 | 缓存 | redis-cli ping |

## 常用命令

### 服务管理

```bash
# 启动指定服务
docker compose up -d api-gateway oms-service

# 重启单个服务
docker compose restart douyin-adapter

# 查看服务日志
docker compose logs -f [service-name]

# 进入容器调试
docker compose exec api-gateway bash

# 停止所有服务
docker compose down

# 停止并删除数据卷（⚠️ 会丢失数据）
docker compose down -v
```

### 数据库操作

```bash
# 进入 PostgreSQL
docker compose exec postgres psql -U ecom -d ecom_automation

# 执行 SQL 文件
docker compose exec -T postgres psql -U ecom -d ecom_automation < database/migrations/001_phase1_init.sql

# 备份数据库
docker compose exec postgres pg_dump -U ecom ecom_automation > backup_$(date +%Y%m%d).sql

# 恢复数据库
cat backup.sql | docker compose exec -T postgres psql -U ecom -d ecom_automation
```

### Redis 操作

```bash
# 进入 Redis CLI
docker compose exec redis redis-cli

# 查看各服务使用的 Redis DB
# DB 0: api-gateway
# DB 1: douyin-adapter
# DB 2: kuaishou-adapter
# DB 3: pdd-cs-adapter
# DB 4: xianyu-adapter
# DB 5: oms-service
# DB 6: rag-service
# DB 7: hermes-control
# DB 8: competitor-crawler

# 切换到特定 DB 查看 key
docker compose exec redis redis-cli -n 0 KEYS '*'
```

### 镜像管理

```bash
# 重新构建单个服务
docker compose build api-gateway

# 强制重建（无缓存）
docker compose build --no-cache douyin-adapter

# 清理未使用的镜像
docker image prune -f

# 查看镜像大小
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep ecom
```

## 健康检查

所有微服务都配置了 Docker HEALTHCHECK，启动后自动监控：

```bash
# 查看健康状态
docker inspect --format='{{.Name}}: {{.State.Health.Status}}' $(docker compose ps -q)

# 手动测试健康端点
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8005/health

# 健康状态含义:
# starting  - 启动中（start_period 内）
# healthy   - 正常运行
# unhealthy - 健康检查失败（连续 N 次失败后）
```

## 环境变量说明

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `DB_PASSWORD` | ✅ | ecom2024 | PostgreSQL 密码 |
| `DOUYIN_APP_KEY` | 按需 | - | 抖店 App Key |
| `DOUYIN_APP_SECRET` | 按需 | - | 抖店 App Secret |
| `KUAISHOU_APP_KEY` | 按需 | - | 快手 App Key |
| `KUAISHOU_APP_SECRET` | 按需 | - | 快手 App Secret |
| `PDD_CLIENT_ID` | 按需 | - | 拼多多 Client ID |
| `PDD_CLIENT_SECRET` | 按需 | - | 拼多多 Client Secret |
| `PDD_ACCESS_TOKEN` | 按需 | - | 拼多多 Access Token |
| `XIANYU_COOKIE` | 按需 | - | 闲鱼登录 Cookie |
| `OPENAI_API_KEY` | 按需 | - | OpenAI API Key |
| `ANTHROPIC_API_KEY` | 按需 | - | Anthropic API Key |
| `N8N_USER` | 否 | admin | n8n 用户名 |
| `N8N_PASSWORD` | 否 | n8n2024 | n8n 密码 |
| `LOG_LEVEL` | 否 | INFO | 日志级别 |
| `ENV` | 否 | production | 运行环境 |

## 端口分配表

| 服务 | 外部端口 | 内部端口 | Redis DB | 说明 |
|------|----------|----------|----------|------|
| api-gateway | 8000 | 8000 | 0 | 主入口网关 |
| douyin-adapter | 8001 | 8001 | 1 | 抖店适配器 |
| kuaishou-adapter | 8002 | 8002 | 2 | 快手适配器 |
| pdd-cs-adapter | 8003 | 8003 | 3 | 拼多多客服 |
| xianyu-adapter | 8004 | 8004 | 4 | 闲鱼适配器 |
| oms-service | 8005 | 8005 | 5 | 订单管理 |
| rag-service | 8006 | 8006 | 6 | 知识库检索 |
| hermes-control | 8007 | 8007 | 7 | AI 控制中心 |
| competitor-crawler | 8008 | 8008 | 8 | 竞品爬虫 |
| PostgreSQL | 5432 | 5432 | - | 数据库 |
| Redis | 6379 | 6379 | - | 缓存（9 个 DB） |
| n8n | 5678 | 5678 | - | 工作流引擎 |
| Metabase | 3001 | 3000 | - | 数据可视化 |

## 故障排查

### 服务启动失败

```bash
# 查看失败原因
docker compose logs [service-name] | tail -50

# 常见问题:
# 1. 端口被占用 → 修改 docker-compose.yml 中的端口映射，或 kill 占用进程
# 2. 依赖未就绪 → 检查 depends_on 和 healthcheck 配置
# 3. 环境变量缺失 → 检查 .env 文件是否完整
# 4. 镜像构建失败 → docker compose build --no-cache [service-name] 重新构建
```

### 数据库连接失败

```bash
# 检查 PostgreSQL 是否就绪
docker compose exec postgres pg_isready -U ecom

# 检查网络连通性
docker compose exec api-gateway ping postgres

# 检查数据库是否存在
docker compose exec postgres psql -U ecom -l
```

### Redis 连接失败

```bash
# 检查 Redis 是否就绪
docker compose exec redis redis-cli ping

# 检查各服务的 Redis DB
docker compose exec redis redis-cli -n 0 DBSIZE  # api-gateway
docker compose exec redis redis-cli -n 1 DBSIZE  # douyin-adapter
```

### 内存不足

```bash
# 查看容器资源使用
docker stats --no-stream

# 限制容器内存 (在 docker-compose.yml 中添加):
#   deploy:
#     resources:
#       limits:
#         memory: 512M
```

### 容器反复重启

```bash
# 查看重启次数和原因
docker inspect --format='{{.Name}}: restarts={{.RestartCount}} exitCode={{.State.ExitCode}}' $(docker compose ps -q)

# 查看最后退出日志
docker compose logs --tail=100 [service-name]
```

## 生产环境建议

1. **修改默认密码** — 生产环境务必修改 `DB_PASSWORD`、`N8N_PASSWORD`
2. **使用 secrets** — 考虑使用 Docker Secrets 或外部密钥管理（如 Vault）
3. **配置反向代理** — 使用 Nginx/Traefik 做反向代理和 SSL 终止
4. **日志收集** — 配置 ELK/Loki 集中日志管理
5. **监控告警** — 集成 Prometheus + Grafana 监控容器和服务指标
6. **数据备份** — 定期备份 PostgreSQL（pg_dump）和 Redis（RDB/AOF）
7. **资源限制** — 为每个容器设置 CPU/内存限制，防止单个服务耗尽资源
8. **网络隔离** — 生产环境考虑将数据库放入独立网络，仅允许应用层访问
9. **镜像安全** — 定期更新基础镜像，扫描 CVE 漏洞
10. **优雅关闭** — 所有 FastAPI 服务支持 SIGTERM 信号，确保请求完成后退出
