# 🔧 故障排除指南 - Hermes 电商自动化系统

> 本文档汇总常见问题及其解决方案，按故障类型分类。遇到问题时请先查阅本文档。

---

## 目录

- [基础设施问题](#基础设施问题)
  - [PostgreSQL](#postgresql)
  - [Redis](#redis)
  - [Docker 网络](#docker-网络)
- [服务启动问题](#服务启动问题)
  - [通用排查步骤](#通用排查步骤)
  - [端口冲突](#端口冲突)
  - [依赖服务未就绪](#依赖服务未就绪)
- [API 网关问题](#api-网关问题)
- [平台适配器问题](#平台适配器问题)
  - [抖店适配器](#抖店适配器)
  - [快手适配器](#快手适配器)
  - [拼多多客服适配器](#拼多多客服适配器)
  - [闲鱼适配器](#闲鱼适配器)
- [竞品爬虫问题](#竞品爬虫问题)
- [RAG 知识库问题](#rag-知识库问题)
- [OMS 订单中台问题](#oms-订单中台问题)
- [n8n 工作流问题](#n8n-工作流问题)
- [Metabase BI 问题](#metabase-bi-问题)
- [Playwright 浏览器自动化问题](#playwright-浏览器自动化问题)
- [性能问题](#性能问题)
- [日志与调试](#日志与调试)

---

## 基础设施问题

### PostgreSQL

**Q: 数据库连接失败 `connection refused`**

```bash
# 1. 检查容器是否运行
docker compose ps postgres

# 2. 查看日志
docker compose logs postgres

# 3. 检查健康状态
docker compose exec postgres pg_isready -U ecom -d ecom_automation

# 4. 如果容器未启动，尝试重启
docker compose restart postgres
```

**Q: 数据库初始化失败**

```bash
# 检查 init.sql 是否有语法错误
docker compose exec postgres psql -U ecom -d ecom_automation -f /docker-entrypoint-initdb.d/init.sql

# 手动执行迁移
docker compose exec -T postgres psql -U ecom -d ecom_automation < database/init.sql

# 执行特定迁移文件
docker compose exec -T postgres psql -U ecom -d ecom_automation < database/migrations/001_phase1_init.sql
```

**Q: 磁盘空间不足导致数据库无法写入**

```bash
# 检查 PostgreSQL 数据目录大小
docker compose exec postgres du -sh /var/lib/postgresql/data

# 清理 WAL 日志（谨慎操作）
docker compose exec postgres pg_archivecleanup /var/lib/postgresql/data/pg_wal $(ls /var/lib/postgresql/data/pg_wal/ | head -1)
```

**Q: `FATAL: too many connections`**

```bash
# 查看当前连接数
docker compose exec postgres psql -U ecom -d ecom_automation -c "SELECT count(*) FROM pg_stat_activity;"

# 查看各服务连接分布
docker compose exec postgres psql -U ecom -d ecom_automation -c "SELECT client_addr, usename, count(*) FROM pg_stat_activity GROUP BY client_addr, usename;"

# 解决：在各服务中配置连接池大小
# DATABASE_URL 中添加 ?pool_size=5&max_overflow=10
```

---

### Redis

**Q: Redis 连接失败**

```bash
# 1. 检查容器状态
docker compose ps redis

# 2. 测试连接
docker compose exec redis redis-cli ping
# 期望返回: PONG

# 3. 查看日志
docker compose logs redis
```

**Q: Redis 内存不足 (`OOM command not allowed`)**

```bash
# 查看内存使用
docker compose exec redis redis-cli INFO memory

# 当前配置为 256MB，可在 docker-compose.yml 中调整:
# command: redis-server --appendonly yes --maxmemory 512mb

# 清理特定 DB（注意：会丢失该 DB 的所有缓存）
docker compose exec redis redis-cli -n 0 FLUSHDB
```

**Q: 各服务 Redis DB 分配**

| DB | 服务 | 用途 |
|----|------|------|
| 0 | api-gateway | 会话缓存、路由缓存 |
| 1 | douyin-adapter | Token 缓存、请求去重 |
| 2 | kuaishou-adapter | Token 缓存、请求去重 |
| 3 | pdd-cs-adapter | 会话状态 |
| 4 | xianyu-adapter | 会话状态 |
| 5 | oms-service | 订单缓存 |
| 6 | rag-service | 查询缓存 |
| 7 | hermes-control | 任务队列 |
| 8 | competitor-crawler | 任务状态 |

```bash
# 查看某个 DB 的 key 数量
docker compose exec redis redis-cli -n 1 DBSIZE

# 查看某个 DB 的所有 key（调试用）
docker compose exec redis redis-cli -n 1 KEYS "*"
```

---

### Docker 网络

**Q: 服务之间无法互相访问**

```bash
# 检查网络
docker network ls | grep ecom

# 检查网络内成员
docker network inspect ecom-automation_ecom-network

# 从容器内部测试连通性
docker compose exec api-gateway curl -s http://oms-service:8005/health
```

**Q: 容器无法访问宿主机服务**

```bash
# Docker 内部使用 host.docker.internal 访问宿主机
docker compose exec api-gateway curl http://host.docker2:8080

# Linux 上可能需要在 docker-compose.yml 中添加:
# extra_hosts:
#   - "host.docker.internal:host-gateway"
```

---

## 服务启动问题

### 通用排查步骤

```bash
# 1. 查看所有服务状态
docker compose ps

# 2. 查看失败服务的日志
docker compose logs --tail=100 <service-name>

# 3. 检查健康检查状态
docker compose ps --format "table {{.Name}}\t{{.Status}}"

# 4. 重建并重启问题服务
docker compose up -d --build <service-name>

# 5. 强制重建（无缓存）
docker compose build --no-cache <service-name>
docker compose up -d <service-name>
```

### 端口冲突

**Q: `Bind for 0.0.0.0:8000 failed: port is already allocated`**

```bash
# 查看占用端口的进程
lsof -i :8000
# 或
netstat -an | grep 8000

# macOS 上停止占用端口的进程
kill -9 $(lsof -t -i :8000)

# 或修改 docker-compose.yml 中的端口映射
# ports:
#   - "8010:8000"  # 改用 8010 对外暴露
```

### 依赖服务未就绪

**Q: 服务启动时日志显示 `ConnectionRefused` 或 `could not connect`**

这通常是因为被依赖的服务（PostgreSQL/Redis）尚未就绪。docker-compose.yml 已配置 `depends_on` + `condition: service_healthy`，但如果健康检查配置不当仍可能出问题。

```bash
# 手动启动顺序
docker compose up -d postgres redis
sleep 10
docker compose up -d api-gateway oms-service
```

---

## API 网关问题

**Q: API 请求返回 502 Bad Gateway**

```bash
# 检查目标服务是否正常
docker compose logs api-gateway

# 测试直接访问后端服务
curl http://localhost:8005/health
curl http://localhost:8001/health
```

**Q: API 请求返回 404 但路由应该存在**

```bash
# 检查 api-gateway 的路由注册
docker compose exec api-gateway python -c "from main import app; print([r.path for r in app.routes])"

# 或查看路由列表
curl http://localhost:8000/openapi.json | python -m json.tool | grep "/paths"
```

---

## 平台适配器问题

### 抖店适配器

**Q: OAuth 授权失败**

```bash
# 检查环境变量是否配置
docker compose exec douyin-adapter env | grep DOUYIN

# 查看详细错误日志
docker compose logs douyin-adapter | grep -i "auth\|oauth\|token"

# 刷新 Token
curl -X POST http://localhost:8001/auth/refresh
```

**Q: 抖店 API 返回签名错误**

- 确认 `DOUYIN_APP_KEY` 和 `DOUYIN_APP_SECRET` 与抖店开放平台一致
- 检查系统时间是否准确（签名依赖时间戳）
- 确认 API 版本与 SDK 版本匹配

### 快手适配器

**Q: 快手 API 请求频率限制**

```bash
# 查看当前 Token 状态
curl http://localhost:8002/auth/token-status

# 强制刷新 Token
curl -X POST http://localhost:8002/auth/force-refresh
```

### 拼多多客服适配器

**Q: Playwright 启动失败**

```bash
# 检查浏览器是否已安装
docker compose exec pdd-cs-adapter playwright install chromium

# 查看详细错误
docker compose logs pdd-cs-adapter | grep -i "browser\|playwright\|chromium"
```

**Q: 拼多多页面加载超时**

- 检查网络连通性
- 确认 `shm_size` 配置（docker-compose.yml 中应设置 `shm_size: '2gb'`）
- 调整 `PLAYWRIGHT_TIMEOUT` 环境变量

**Q: 调了 `/api/v1/system/pdd-login/start`，但拿不到二维码截图**

```bash
# 检查数据目录是否存在
docker compose exec pdd-cs-adapter ls -la /app/data

# 检查截图文件是否已生成
docker compose exec pdd-cs-adapter ls -la /app/data/pdd_login.png

# 直接请求截图接口
curl -I http://localhost:8003/api/v1/system/pdd-login/screenshot
```

- 确认 `PDD_DATA_DIR` 与容器卷挂载一致
- 确认容器内 Playwright 已成功打开登录页
- 若返回 404，优先查看 `docker compose logs pdd-cs-adapter`

**Q: 一直显示“等待扫码确认”，但明明已经打开了工作台**

- 先访问 `http://localhost:8003/api/v1/system/pdd-login/status` 确认返回值
- 确认扫码后页面已进入工作台，而不是仍停留在登录页或二次确认页
- 如页面已跳转但状态仍为 `false`，删除旧会话后重新发起扫码：

```bash
docker compose exec pdd-cs-adapter rm -f /app/data/pdd_storage_state.json /app/data/pdd_login.png
curl -X POST http://localhost:8003/api/v1/system/pdd-login/start
```

**Q: 容器重启后拼多多登录态丢失**

- 确认 `docker-compose.yml` 中存在 `pdd_data:/app/data`
- 确认 `PDD_DATA_DIR=/app/data`
- 检查 `pdd_storage_state.json` 是否成功落盘：

```bash
docker compose exec pdd-cs-adapter ls -la /app/data/pdd_storage_state.json
```

- 如果文件存在但仍掉登录，通常是平台会话自然失效，需要重新扫码

### 闲鱼适配器

**Q: 闲鱼登录态失效**

```bash
# 查看当前会话状态
curl http://localhost:8004/health

# 检查 Cookie 存储
docker compose exec xianyu-adapter ls -la /app/data/
```

---

## 竞品爬虫问题

**Q: 爬虫任务卡住不动**

```bash
# 查看任务列表
curl http://localhost:8008/tasks

# 查看特定任务状态
curl http://localhost:8008/tasks/<task_id>

# 暂停任务
curl -X POST http://localhost:8008/tasks/<task_id>/pause

# 删除卡住的任务
curl -X DELETE http://localhost:8008/tasks/<task_id>
```

**Q: 反爬虫统计**

```bash
# 查看各平台反爬状态
curl http://localhost:8008/anti-crawler/stats

# 查看整体统计
curl http://localhost:8008/stats
```

**Q: 爬虫被目标网站封禁**

- 检查 `anti-crawler/stats` 中的封禁计数
- 适当增加请求间隔
- 更换代理 IP
- 降低并发数

---

## RAG 知识库问题

**Q: 向量搜索无结果**

```bash
# 查看缓存统计
curl http://localhost:8006/cache/stats

# 清理缓存重新索引
curl -X POST http://localhost:8006/cache/invalidate
```

**Q: pgvector 扩展未安装**

```bash
# 检查扩展
docker compose exec postgres psql -U ecom -d ecom_automation -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# 安装扩展（如果缺失）
docker compose exec postgres psql -U ecom -d ecom_automation -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

---

## OMS 订单中台问题

**Q: 订单同步延迟**

```bash
# 查看 OMS 服务日志
docker compose logs --tail=100 oms-service

# 检查 Redis 队列中积压的任务
docker compose exec redis redis-cli -n 5 LLEN order_sync_queue
```

**Q: 多平台订单状态不一致**

- 各平台 API 调用频率不同，状态同步有延迟
- 使用 OMS 的统一查询接口确认最新状态
- 检查各适配器的 webhook 回调是否正常

---

## n8n 工作流问题

**Q: n8n 无法访问**

```bash
# 检查容器状态
docker compose ps n8n

# 查看日志
docker compose logs n8n

# 默认登录地址
# http://localhost:5678
# 用户名: admin (或 .env 中的 N8N_USER)
# 密码: n8n2024 (或 .env 中的 N8N_PASSWORD)
```

**Q: n8n 工作流执行失败**

- 检查工作流中引用的服务是否在线
- 查看 n8n 执行日志（n8n 界面 → Executions）
- 确认环境变量（API Key 等）是否正确传递

---

## Metabase BI 问题

**Q: Metabase 无法连接数据库**

```bash
# Metabase 使用同一 PostgreSQL 实例
# 连接信息:
# Host: postgres
# Port: 5432
# Database: ecom_automation
# User: ecom
# Password: ${DB_PASSWORD}
```

**Q: Metabase 首次启动很慢**

Metabase 首次启动需要 1-2 分钟初始化（`start_period: 60s`）。请耐心等待。

```bash
# 查看初始化进度
docker compose logs -f metabase
```

---

## Playwright 浏览器自动化问题

**Q: 浏览器启动失败 `BrowserType.launch: Executable doesn't exist`**

```bash
# 进入容器安装浏览器
docker compose exec <service> playwright install chromium

# 或在 Dockerfile 中添加:
# RUN playwright install chromium
```

**Q: 页面截图或操作超时**

```bash
# 增加超时时间
# 环境变量 PLAYWRIGHT_TIMEOUT=60000 (毫秒)

# 有头模式调试（本地开发时）
HEADLESS=false uvicorn main:app --reload
```

**Q: 浏览器会话文件存在，但服务仍像首次启动一样要求重新登录**

- 检查会话文件是否写入到实际使用的 `PDD_DATA_DIR`
- 检查容器是否被替换且未复用 `pdd_data` 卷
- 确认当前访问的是同一套拼多多工作台域名配置（`PDD_WORKBENCH_URL`）

**Q: Docker 内浏览器崩溃 (OOM)**

- 确保 `shm_size: '2gb'` 已配置
- 减少并发浏览器实例数
- 检查容器内存限制

---

## 性能问题

**Q: 服务响应缓慢**

```bash
# 1. 检查资源使用
docker stats --no-stream

# 2. 检查数据库慢查询
docker compose exec postgres psql -U ecom -d ecom_automation -c "
SELECT query, calls, mean_exec_time, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;"

# 3. 检查 Redis 命中率
docker compose exec redis redis-cli INFO stats | grep -E "keyspace_hits|keyspace_misses"

# 4. 检查是否有连接泄漏
docker compose exec postgres psql -U ecom -d ecom_automation -c "SELECT count(*) FROM pg_stat_activity;"
```

**Q: Docker 宿主机资源不足**

```bash
# 查看 Docker 资源使用
docker system df
docker stats --no-stream

# 清理无用资源
docker system prune -f

# 清理构建缓存
docker builder prune -f
```

---

## 日志与调试

### 查看日志

```bash
# 实时查看所有服务日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f api-gateway

# 最近 100 行
docker compose logs --tail=100 <service>

# 带时间戳
docker compose logs -f -t <service>

# 查看最近 5 分钟的日志
docker compose logs --since 5m <service>
```

### 进入容器调试

```bash
# 进入服务容器
docker compose exec api-gateway bash

# 运行 Python 交互式环境
docker compose exec api-gateway python

# 检查服务内部网络
docker compose exec api-gateway curl http://oms-service:8005/health
```

### 调试单个服务（本地运行）

```bash
cd services/<service-name>
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 设置环境变量（参考 .env.example）
export DATABASE_URL=postgresql://ecom:ecom2024@localhost:5432/ecom_automation
export REDIS_URL=redis://localhost:6379/0

# 启动服务（带热重载）
uvicorn main:app --reload --port <port>
```

### 健康检查端点

所有服务都提供 `/health` 端点：

```bash
curl http://localhost:8000/health  # api-gateway
curl http://localhost:8001/health  # douyin-adapter
curl http://localhost:8002/health  # kuaishou-adapter
curl http://localhost:8003/health  # pdd-cs-adapter
curl http://localhost:8004/health  # xianyu-adapter
curl http://localhost:8005/health  # oms-service
curl http://localhost:8006/health  # rag-service
curl http://localhost:8007/health  # hermes-control
curl http://localhost:8008/health  # competitor-crawler
```

---

## 快速参考

### Make 命令速查

| 命令 | 说明 |
|------|------|
| `make ps` | 查看服务状态 |
| `make logs` | 实时查看日志 |
| `make health` | 健康检查 |
| `make restart-svc SVC=api-gateway` | 重启指定服务 |
| `make build-svc SVC=api-gateway` | 重建指定服务 |
| `make backup` | 数据库备份 |
| `make restore` | 数据库恢复 |
| `make clean` | 清理容器和镜像 |

### 环境变量速查

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DB_PASSWORD` | PostgreSQL 密码 | `ecom2024` |
| `N8N_USER` | n8n 用户名 | `admin` |
| `N8N_PASSWORD` | n8n 密码 | `n8n2024` |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `HEADLESS` | 浏览器无头模式 | `true` |
| `PLAYWRIGHT_TIMEOUT` | Playwright 超时(ms) | `30000` |

### 端口速查

| 端口 | 服务 |
|------|------|
| 3001 | Metabase |
| 5432 | PostgreSQL |
| 5678 | n8n |
| 6379 | Redis |
| 8000 | API Gateway |
| 8001 | 抖店适配器 |
| 8002 | 快手适配器 |
| 8003 | 拼多多客服 |
| 8004 | 闲鱼适配器 |
| 8005 | OMS 服务 |
| 8006 | RAG 知识库 |
| 8007 | Hermes 总控 |
| 8008 | 竞品爬虫 |
