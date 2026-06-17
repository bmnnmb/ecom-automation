# 竞品爬虫服务 - 快速启动指南

## 概述

竞品爬虫服务支持抖音、快手、拼多多、闲鱼四大平台的商品数据采集与分析。

**服务端口**: 8008  
**依赖服务**: MongoDB (27017), PostgreSQL, Redis

---

## 🚀 一键启动（推荐）

### 方式一：Docker Compose 启动全部服务

```bash
# 在项目根目录执行
docker compose up -d

# 查看爬虫服务状态
docker ps | grep competitor-crawler

# 查看日志
docker logs -f ecom-competitor-crawler
```

### 方式二：单独启动爬虫服务

```bash
# 确保依赖服务已启动
docker compose up -d mongodb postgres redis

# 启动爬虫服务
docker compose up -d competitor-crawler

# 验证服务健康
curl http://localhost:8008/health
```

---

## 📋 前置条件

### 1. 环境检查

```bash
# 检查 Docker
docker --version

# 检查依赖服务
docker ps --filter "name=mongodb"
docker ps --filter "name=postgres"
docker ps --filter "name=redis"
```

### 2. 确保 MongoDB 正常运行

```bash
# 测试连接
docker exec -it ecom-mongodb mongosh --eval "db.runCommand({ ping: 1 })"
```

---

## 🔧 故障排查

### 问题 1: 服务启动失败

**症状**: `docker logs ecom-competitor-crawler` 显示连接错误

```bash
# 检查服务依赖
docker compose ps

# 重启服务
docker compose restart competitor-crawler

# 查看详细日志
docker logs ecom-competitor-crawler --tail 100
```

### 问题 2: MongoDB 连接失败

**症状**: 日志中出现 `Connection refused`

```bash
# 验证 MongoDB 可达性
docker exec ecom-competitor-crawler ping mongodb -c 3

# 检查环境变量
docker exec ecom-competitor-crawler env | grep MONGODB

# 重建服务
docker compose up -d --force-recreate competitor-crawler
```

### 问题 3: 健康检查失败

```bash
# 检查服务是否启动
docker exec ecom-competitor-crawler curl -f http://localhost:8008/health

# 查看进程
docker exec ecom-competitor-crawler ps aux

# 重启容器
docker restart ecom-competitor-crawler
```

---

## 🧪 验证服务

### 1. 健康检查

```bash
curl http://localhost:8008/health
```

**预期响应**:
```json
{
  "status": "healthy",
  "mongodb": "connected",
  "scheduler": "running"
}
```

### 2. API 文档

浏览器访问: http://localhost:8008/docs

### 3. 测试爬取（示例）

```bash
# 爬取单个商品
curl -X POST http://localhost:8008/crawl/single \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "douyin",
    "url": "https://haohuo.jinritemai.com/views/product/item?id=3594372956022802854"
  }'
```

---

## 📊 使用指南

### 1. 创建监控任务

```bash
# 每 15 分钟检查一次价格
curl -X POST http://localhost:8008/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "douyin",
    "product_id": "3594372956022802854",
    "url": "https://haohuo.jinritemai.com/views/product/item?id=3594372956022802854",
    "task_type": "price_check",
    "interval_minutes": 15
  }'
```

### 2. 查看所有任务

```bash
curl http://localhost:8008/tasks
```

### 3. 价格趋势分析

```bash
curl "http://localhost:8008/analysis/price/douyin/3594372956022802854?days=30"
```

### 4. 生成竞品报告

```bash
curl "http://localhost:8008/analysis/report/3594372956022802854?platforms=douyin,pdd"
```

---

## 🔐 配置说明

### 环境变量（docker-compose.yml）

```yaml
environment:
  MONGODB_URL: mongodb://mongodb:27017
  MONGODB_DATABASE: competitor_crawler
  DATABASE_URL: postgresql://ecom:password@postgres:5432/ecom_automation
  REDIS_URL: redis://redis:6379/8
  LOG_LEVEL: INFO
  DATA_DIR: /app/data
```

### 可选配置

创建 `services/competitor-crawler/.env` 文件：

```bash
# 爬虫行为
CRAWLER_TIMEOUT=30
CRAWLER_MAX_RETRIES=3
CRAWLER_CONCURRENCY=5

# 调度器
SCHEDULER_PRICE_INTERVAL=15
SCHEDULER_TITLE_INTERVAL=30

# 代理（可选）
PROXY_ENABLED=false
PROXY_URL=http://proxy.example.com:8080
```

---

## 📦 数据存储

### MongoDB 数据结构

```javascript
// 商品快照 collection
db.snapshots.findOne()
{
  "_id": ObjectId("..."),
  "platform": "douyin",
  "product_id": "3594372956022802854",
  "url": "https://...",
  "title": "商品标题",
  "price": 99.00,
  "original_price": 199.00,
  "main_image_hash": "abc123...",
  "promotion_tags": ["限时特价", "包邮"],
  "comment_keywords": ["质量好", "物流快"],
  "sales_count": 10000,
  "shop_name": "官方旗舰店",
  "crawl_time": ISODate("2026-06-17T02:30:00.000Z")
}
```

### 文件系统存储

```
/app/data/
├── douyin/
│   └── 3594372956022802854/
│       ├── 2026-06-17T02-30-00.json
│       └── screenshots/
├── pdd/
├── kuaishou/
└── xianyu/
```

---

## 🔄 服务管理

### 启动/停止/重启

```bash
# 启动
docker compose start competitor-crawler

# 停止
docker compose stop competitor-crawler

# 重启
docker compose restart competitor-crawler

# 查看状态
docker compose ps competitor-crawler
```

### 查看日志

```bash
# 实时日志
docker logs -f ecom-competitor-crawler

# 最近 100 行
docker logs --tail 100 ecom-competitor-crawler

# 错误日志
docker logs ecom-competitor-crawler 2>&1 | grep ERROR
```

### 进入容器调试

```bash
docker exec -it ecom-competitor-crawler bash

# 检查进程
ps aux

# 测试内部连接
curl http://localhost:8008/health
ping mongodb
```

---

## 📈 监控与告警

### 服务统计

```bash
curl http://localhost:8008/stats
```

**响应示例**:
```json
{
  "total_runs": 1250,
  "successful_runs": 1200,
  "failed_runs": 50,
  "active_tasks": 25,
  "last_run_time": "2026-06-17T10:30:00Z",
  "uptime_hours": 168.5
}
```

### 告警配置（待实现）

目前价格变化和标题变化只记录日志，后续可配置：
- 钉钉 Webhook
- 企业微信
- 邮件通知
- 自定义 Webhook

---

## 🐛 常见问题

### Q1: 爬取失败怎么办？

**A**: 检查以下几点：
1. 目标网站是否可访问
2. 查看日志中的具体错误信息
3. 验证 URL 格式是否正确
4. 检查是否触发反爬虫机制

```bash
# 查看失败详情
docker logs ecom-competitor-crawler 2>&1 | grep "Failed to crawl"
```

### Q2: 如何调整爬取频率？

**A**: 修改任务的 `interval_minutes` 参数：

```bash
# 更新任务（需要先删除再创建）
curl -X DELETE http://localhost:8008/tasks/{task_id}
curl -X POST http://localhost:8008/tasks -d '{"interval_minutes": 30, ...}'
```

### Q3: 数据保留多久？

**A**: 默认保留 90 天，可通过环境变量调整：

```yaml
environment:
  STORAGE_RETENTION_DAYS: 90
```

### Q4: 支持代理吗？

**A**: 支持。在 `.env` 中配置：

```bash
PROXY_ENABLED=true
PROXY_URL=http://proxy.example.com:8080
PROXY_USERNAME=user
PROXY_PASSWORD=pass
```

---

## 📚 相关文档

- [完整 API 文档](../API.md#竞品爬虫)
- [架构设计](../architecture/services.md#competitor-crawler)
- [部署指南](../DEPLOY.md)
- [开发指南](../DEVELOPMENT.md)

---

## 🆘 获取帮助

如遇问题，请：
1. 查看日志：`docker logs ecom-competitor-crawler --tail 200`
2. 检查健康状态：`curl http://localhost:8008/health`
3. 访问 API 文档：http://localhost:8008/docs
4. 联系开发团队

**更新时间**: 2026-06-17
