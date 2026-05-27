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
- Docker Compose >= 2.0
- 至少 4GB 可用内存

### 1. 配置环境变量

```bash
cd ~/ecom-automation
cp .env.example .env
# 编辑 .env 填入实际的 API Key 和密钥
vim .env
```

### 2. 启动所有服务

```bash
# 构建并启动（首次运行）
docker compose up -d --build

# 仅启动（镜像已构建）
docker compose up -d
```

### 3. 验证服务状态

```bash
# 查看所有容器状态
docker compose ps

# 检查服务健康状态
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

# 查看日志
docker compose logs -f api-gateway
docker compose logs -f --tail=50
```

### 4. 访问服务

| 服务 | 端口 | 说明 |
|------|------|------|
| API 网关 | http://localhost:8000 | 主入口，API 文档: /docs |
| 抖店适配器 | http://localhost:8001 | 抖店平台对接 |
| 快手适配器 | http://localhost:8002 | 快手平台对接 |
| 拼多多客服 | http://localhost:8003 | 拼多多客服自动化 |
| 闲鱼适配器 | http://localhost:8004 | 闲鱼平台对接 |
| OMS 服务 | http://localhost:8005 | 订单管理系统 |
| RAG 服务 | http://localhost:8006 | 知识库检索 |
| Hermes 控制 | http://localhost:8007 | AI 控制中心 |
| 竞品爬虫 | http://localhost:8008 | 竞品数据采集 |
| n8n | http://localhost:5678 | 工作流引擎 |
| Metabase | http://localhost:3001 | 数据可视化 |
| PostgreSQL | localhost:5432 | 数据库 |
| Redis | localhost:6379 | 缓存 |

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

# 停止并删除数据卷
docker compose down -v
```

### 数据库操作

```bash
# 进入 PostgreSQL
docker compose exec postgres psql -U ecom -d ecom_automation

# 执行 SQL 文件
docker compose exec -T postgres psql -U ecom -d ecom_automation < database/migrations/001_init.sql

# 备份数据库
docker compose exec postgres pg_dump -U ecom ecom_automation > backup_$(date +%Y%m%d).sql

# 恢复数据库
cat backup.sql | docker compose exec -T postgres psql -U ecom -d ecom_automation
```

### Redis 操作

```bash
# 进入 Redis CLI
docker compose exec redis redis-cli

# 查看所有键
docker compose exec redis redis-cli KEYS '*'
```

### 镜像管理

```bash
# 重新构建单个服务
docker compose build api-gateway

# 强制重建（无缓存）
docker compose build --no-cache douyin-adapter

# 清理未使用的镜像
docker image prune -f
```

## 健康检查

所有微服务都配置了 Docker HEALTHCHECK：

```bash
# 查看健康状态
docker inspect --format='{{.Name}}: {{.State.Health.Status}}' $(docker compose ps -q)

# 手动测试健康端点
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8005/health
```

## 环境变量说明

| 变量 | 必填 | 说明 |
|------|------|------|
| `DB_PASSWORD` | ✅ | PostgreSQL 密码 |
| `DOUYIN_APP_KEY` | 按需 | 抖店 App Key |
| `DOUYIN_APP_SECRET` | 按需 | 抖店 App Secret |
| `KUAISHOU_APP_KEY` | 按需 | 快手 App Key |
| `KUAISHOU_APP_SECRET` | 按需 | 快手 App Secret |
| `PDD_CLIENT_ID` | 按需 | 拼多多 Client ID |
| `PDD_CLIENT_SECRET` | 按需 | 拼多多 Client Secret |
| `XIANYU_COOKIE` | 按需 | 闲鱼登录 Cookie |
| `OPENAI_API_KEY` | 按需 | OpenAI API Key |
| `N8N_USER` | 否 | n8n 用户名 (默认: admin) |
| `N8N_PASSWORD` | 否 | n8n 密码 (默认: n8n2024) |
| `LOG_LEVEL` | 否 | 日志级别 (默认: INFO) |

## 故障排查

### 服务启动失败

```bash
# 查看失败原因
docker compose logs [service-name] | tail -50

# 常见问题:
# 1. 端口被占用 → 修改 docker-compose.yml 中的端口映射
# 2. 依赖未就绪 → 检查 depends_on 和 healthcheck
# 3. 环境变量缺失 → 检查 .env 文件
```

### 数据库连接失败

```bash
# 检查 PostgreSQL 是否就绪
docker compose exec postgres pg_isready -U ecom

# 检查网络连通性
docker compose exec api-gateway ping postgres
```

### 内存不足

```bash
# 查看容器资源使用
docker stats --no-stream

# 限制容器内存 (在 docker-compose.yml 中添加)
# mem_limit: 512m
```

## 生产环境建议

1. **修改默认密码** — 生产环境务必修改 `DB_PASSWORD`、`N8N_PASSWORD`
2. **使用 secrets** — 考虑使用 Docker Secrets 管理敏感信息
3. **配置反向代理** — 使用 Nginx/Traefik 做反向代理和 SSL
4. **日志收集** — 配置 ELK/Loki 集中日志管理
5. **监控告警** — 集成 Prometheus + Grafana 监控
6. **数据备份** — 定期备份 PostgreSQL 和 Redis 数据
7. **资源限制** — 为每个容器设置 CPU/内存限制

## 端口分配表

| 服务 | 外部端口 | 内部端口 | Redis DB |
|------|----------|----------|----------|
| api-gateway | 8000 | 8000 | 0 |
| douyin-adapter | 8001 | 8001 | 1 |
| kuaishou-adapter | 8002 | 8002 | 2 |
| pdd-cs-adapter | 8003 | 8003 | 3 |
| xianyu-adapter | 8004 | 8004 | 4 |
| oms-service | 8005 | 8005 | 5 |
| rag-service | 8006 | 8006 | 6 |
| hermes-control | 8007 | 8007 | 7 |
| competitor-crawler | 8008 | 8008 | 8 |
| PostgreSQL | 5432 | 5432 | - |
| Redis | 6379 | 6379 | - |
| n8n | 5678 | 5678 | - |
| Metabase | 3001 | 3000 | - |
