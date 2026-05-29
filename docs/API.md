# ecom-automation API Documentation

> 最后更新: 2026-05-29 | 源码扫描自 11 个微服务

本文档覆盖 ecom-automation 项目的全部 REST API 端点，共 **11 个服务、95+ 个接口**。

## 目录

- [服务概览](#服务概览)
- [1. API Gateway (端口 8000)](#1-api-gateway-端口-8000)
  - [统一鉴权 /api/auth](#统一鉴权-apiauth)
  - [店铺管理 /api/shops](#店铺管理-apishops)
  - [商品管理 /api/products](#商品管理-apiproducts)
  - [订单管理 /api/orders](#订单管理-apiorders)
  - [客服消息 /api/messages](#客服消息-apimessages)
  - [售后服务 /api/aftersales](#售后服务-apiaftersales)
  - [竞品分析 /api/competitors](#竞品分析-apicompetitors)
  - [报表统计 /api/reports](#报表统计-apireports)
  - [库存管理 /api/inventory](#库存管理-apiinventory)
  - [工单管理 /api/tickets](#工单管理-apitickets)
  - [运营看板 /api/dashboard](#运营看板-apidashboard)
  - [系统设置 /api/settings](#系统设置-apisettings)
- [2. Hermes 总控服务 (端口 8080)](#2-hermes-总控服务-端口-8080)
  - [任务管理](#任务管理)
  - [技能执行](#技能执行)
  - [报表生成](#报表生成)
  - [业务目标处理](#业务目标处理)
- [3. RAG 知识库服务 (端口 8006)](#3-rag-知识库服务-端口-8006)
- [4. 竞品爬虫服务 (端口 8008)](#4-竞品爬虫服务-端口-8008)
  - [爬取任务](#爬取任务)
  - [任务调度](#任务调度)
  - [数据分析](#数据分析)
  - [数据查询](#数据查询)
- [5. 商品管理服务 (端口 8006)](#5-商品管理服务-端口-8006)
  - [商品 CRUD](#商品-crud)
  - [商品批量操作](#商品批量操作)
  - [分类管理](#分类管理)
  - [客户管理](#客户管理)
- [6. 抖店适配器 (端口 8001)](#6-抖店适配器-端口-8001)
- [7. 快手适配器 (端口 8002)](#7-快手适配器-端口-8002)
- [8. OMS 订单中台 (端口 8005)](#8-oms-订单中台-端口-8005)
  - [订单管理](#订单管理)
  - [库存管理](#库存管理)
  - [工单管理](#工单管理)
  - [运营看板](#运营看板)
- [9. 拼多多客服适配器 (端口 8003)](#9-拼多多客服适配器-端口-8003)
- [10. 闲鱼适配器 (端口 8004)](#10-闲鱼适配器-端口-8004)
- [数据模型](#数据模型)

---

## 服务概览

| 服务 | 端口 | 技术栈 | 说明 |
|------|------|--------|------|
| api-gateway | 8000 | FastAPI | 统一 REST API 网关 |
| douyin-adapter | 8001 | FastAPI + 官方SDK | 抖店平台适配器 |
| kuaishou-adapter | 8002 | FastAPI + SDK | 快手平台适配器 |
| pdd-cs-adapter | 8003 | Python + Playwright | 拼多多客服自动化 |
| xianyu-adapter | 8004 | FastAPI + Playwright | 闲鱼自动化 |
| oms-service | 8005 | FastAPI + SQLAlchemy | 订单中台 (订单/库存/工单/看板) |
| product-service | 8006 | FastAPI + SQLAlchemy | 商品与分类管理 |
| rag-service | 8006 | FastAPI + pgvector | RAG 知识库检索 |
| hermes-control | 8080 | Python + Hermes | 总控、策略、调度、报表 |
| competitor-crawler | 8008 | Python asyncio | 竞品数据采集与分析 |

---

## 1. API Gateway (端口 8000)

基础路径: `http://localhost:8000`

### 统一鉴权 `/api/auth`

#### 获取授权链接

```
GET /api/auth/authorize/{platform}?shop_id={shop_id}&redirect_uri={redirect_uri}
```

| 参数 | 类型 | 位置 | 必填 | 说明 |
|------|------|------|------|------|
| platform | string | path | ✅ | 平台标识 (douyin / kuaishou / pdd / xianyu) |
| shop_id | string | query | ✅ | 店铺 ID |
| redirect_uri | string | query | ✅ | OAuth 回调地址 |

**响应 200**
```json
{
  "status": "success",
  "authorization_url": "https://..."
}
```

#### OAuth 回调

```
GET /api/auth/callback/{platform}?code={code}&state={state}&redirect_uri={redirect_uri}
```

| 参数 | 类型 | 位置 | 必填 | 说明 |
|------|------|------|------|------|
| platform | string | path | ✅ | 平台标识 |
| code | string | query | ✅ | 授权码 |
| state | string | query | ✅ | 状态参数（通常含 shop_id） |
| redirect_uri | string | query | ✅ | 回调地址 |

**响应 200**
```json
{
  "status": "success",
  "message": "Authorization successful",
  "shop_id": "shop_1",
  "tokens": {
    "access_token": "...",
    "refresh_token": "...",
    "expires_in": 7200,
    "token_type": "Bearer"
  }
}
```

#### 刷新令牌

```
POST /api/auth/refresh/{platform}?shop_id={shop_id}&refresh_token={refresh_token}
```

| 参数 | 类型 | 位置 | 必填 | 说明 |
|------|------|------|------|------|
| platform | string | path | ✅ | 平台标识 |
| shop_id | string | query | ✅ | 店铺 ID |
| refresh_token | string | query | ✅ | 刷新令牌 |

**响应 200**
```json
{
  "status": "success",
  "message": "Token refreshed successfully",
  "tokens": {
    "access_token": "...",
    "refresh_token": "...",
    "expires_in": 7200,
    "refresh_expires_in": 2592000
  }
}
```

---

### 店铺管理 `/api/shops`

#### 获取店铺列表

```
GET /api/shops?platform={platform}
```

| 参数 | 类型 | 位置 | 必填 | 说明 |
|------|------|------|------|------|
| platform | string | query | ❌ | 按平台筛选 |

**响应 200** — `ShopResponse[]`
```json
[
  {
    "id": "shop_1",
    "platform": "douyin",
    "shop_name": "测试店铺",
    "auth_status": "pending",
    "created_at": "2026-05-27T10:00:00",
    "updated_at": "2026-05-27T10:00:00"
  }
]
```

#### 创建店铺

```
POST /api/shops
```

**请求体** — `ShopCreate`
```json
{
  "platform": "douyin",
  "shop_name": "新店铺"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| platform | string | ✅ | 平台标识 |
| shop_name | string | ✅ | 店铺名称 |

**响应 200** — `ShopResponse`

#### 获取店铺详情

```
GET /api/shops/{shop_id}
```

| 参数 | 类型 | 位置 | 说明 |
|------|------|------|------|
| shop_id | string | path | 店铺 ID |

**响应 200** — `ShopResponse`  
**响应 404** — `{"detail": "店铺不存在"}`

#### 删除店铺

```
DELETE /api/shops/{shop_id}
```

**响应 200**
```json
{"message": "删除成功"}
```

---

### 商品管理 `/api/products`

#### 获取商品列表

```
GET /api/products?shop_id={shop_id}&status={status}&skip={skip}&limit={limit}
```

| 参数 | 类型 | 位置 | 必填 | 默认值 | 说明 |
|------|------|------|------|--------|------|
| shop_id | string | query | ❌ | — | 按店铺筛选 |
| status | string | query | ❌ | — | 按状态筛选 |
| skip | int | query | ❌ | 0 | 跳过条数 |
| limit | int | query | ❌ | 50 | 返回数量上限 |

**响应 200** — `ProductResponse[]`
```json
[
  {
    "id": "prod_1",
    "shop_id": "shop_1",
    "title": "商品标题",
    "price": 99.99,
    "cost_price": 50.00,
    "sku_id": "SKU001",
    "status": "draft",
    "listing_risk_score": 0,
    "margin_score": 49.99,
    "created_at": "2026-05-27T10:00:00",
    "updated_at": "2026-05-27T10:00:00"
  }
]
```

#### 创建商品

```
POST /api/products
```

**请求体** — `ProductCreate`
```json
{
  "shop_id": "shop_1",
  "title": "商品标题",
  "price": 99.99,
  "cost_price": 50.00,
  "sku_id": "SKU001"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| shop_id | string | ✅ | 店铺 ID |
| title | string | ✅ | 商品标题 |
| price | float | ✅ | 售价 |
| cost_price | float | ❌ | 成本价（用于计算毛利分） |
| sku_id | string | ❌ | SKU 编号 |

**响应 200** — `ProductResponse`

#### 获取商品详情

```
GET /api/products/{product_id}
```

**响应 200** — `ProductResponse`  
**响应 404** — `{"detail": "商品不存在"}`

#### 更新商品状态

```
PUT /api/products/{product_id}/status?status={status}
```

| 参数 | 类型 | 位置 | 说明 |
|------|------|------|------|
| product_id | string | path | 商品 ID |
| status | string | query | 新状态 |

**响应 200** — `ProductResponse`

---

### 订单管理 `/api/orders`

> 代理到 OMS 订单中台，详见 [OMS 订单管理](#订单管理-apiorders)

```
GET  /api/orders                # 订单列表
POST /api/orders                # 创建订单
GET  /api/orders/{order_id}     # 订单详情
PUT  /api/orders/{order_id}/status  # 更新状态
DELETE /api/orders/{order_id}   # 删除订单
```

---

### 客服消息 `/api/messages`

```
GET  /api/messages                   # 消息列表
POST /api/messages                   # 发送消息
GET  /api/messages/{message_id}      # 消息详情
POST /api/messages/{message_id}/reply  # 回复消息
```

---

### 售后服务 `/api/aftersales`

```
GET   /api/aftersales                    # 售后列表
POST  /api/aftersales                    # 创建售后
GET   /api/aftersales/{aftersale_id}     # 售后详情
PATCH /api/aftersales/{aftersale_id}     # 更新售后
```

---

### 竞品分析 `/api/competitors`

```
GET    /api/competitors                     # 竞品列表
POST   /api/competitors                     # 添加竞品
GET    /api/competitors/{competitor_id}      # 竞品详情
DELETE /api/competitors/{competitor_id}      # 删除竞品
```

---

### 报表统计 `/api/reports`

```
GET /api/reports/daily           # 日报
GET /api/reports/weekly          # 周报
GET /api/reports/monthly         # 月报
```

---

### 库存管理 `/api/inventory`

> 代理到 OMS 订单中台，详见 [OMS 库存管理](#库存管理-apiinventory)

```
GET  /api/inventory                   # 库存列表
GET  /api/inventory/low-stock         # 低库存预警
GET  /api/inventory/{sku_id}          # 库存详情
POST /api/inventory                   # 创建库存
PUT  /api/inventory/{sku_id}/stock    # 更新库存
```

---

### 工单管理 `/api/tickets`

> 代理到 OMS 订单中台，详见 [OMS 工单管理](#工单管理-apitickets)

```
GET  /api/tickets                    # 工单列表
POST /api/tickets                    # 创建工单
GET  /api/tickets/{ticket_id}        # 工单详情
PUT  /api/tickets/{ticket_id}/status # 更新状态
PUT  /api/tickets/{ticket_id}/assign # 分配工单
```

---

### 运营看板 `/api/dashboard`

> 代理到 OMS 订单中台，详见 [OMS 运营看板](#运营看板-apidashboard)

```
GET /api/dashboard           # 看板统计
GET /api/dashboard/stats     # 综合统计
GET /api/dashboard/trend     # 趋势数据
```

---

### 系统设置 `/api/settings`

```
GET /api/settings            # 获取设置
PUT /api/settings            # 更新设置
```

---

## 2. Hermes 总控服务 (端口 8080)

基础路径: `http://localhost:8080`

### 健康检查

```
GET /health
```

### 获取服务配置

```
GET /config
```

**响应**
```json
{
  "app_name": "Hermes总控服务",
  "version": "1.0.0",
  "debug": false,
  "log_level": "INFO",
  "skill_mapping": {}
}
```

---

### 任务管理

#### 提交任务

```
POST /tasks
```

**请求体** — `TaskRequest`
```json
{
  "task_type": "skill:competitor_analysis",
  "params": {"goal": "分析竞品定价策略"},
  "priority": "high"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task_type | string | ✅ | 任务类型，如 `skill:xxx` 或 `n8n:xxx` |
| params | object | ❌ | 任务参数 |
| priority | string | ❌ | 优先级: `low` / `normal` / `high` / `urgent` |

**响应 200**
```json
{
  "status": "success",
  "task_id": "task_abc123",
  "message": "任务已提交，ID: task_abc123"
}
```

#### 列出任务

```
GET /tasks?status={status}&limit={limit}
```

| 参数 | 类型 | 位置 | 必填 | 默认值 | 说明 |
|------|------|------|------|--------|------|
| status | string | query | ❌ | — | 任务状态过滤 |
| limit | int | query | ❌ | 50 | 返回数量限制 |

#### 获取任务状态

```
GET /tasks/{task_id}
```

#### 取消任务

```
DELETE /tasks/{task_id}
```

#### 获取队列状态

```
GET /queue/status
```

---

### 技能执行

#### 执行技能

```
POST /skills/execute
```

**请求体** — `SkillExecuteRequest`
```json
{
  "skill_name": "competitor_analysis",
  "params": {"platform": "douyin"}
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| skill_name | string | ✅ | 技能名称 |
| params | object | ❌ | 技能参数 |

#### 列出所有技能

```
GET /skills
```

#### 获取技能信息

```
GET /skills/{skill_name}
```

---

### 报表生成

#### 生成报表

```
POST /reports/generate
```

**请求体** — `ReportRequest`
```json
{
  "report_type": "daily",
  "date": "2026-05-27",
  "time_range": "24h"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| report_type | string | ✅ | 报表类型: `daily` / `weekly` / `abnormal` |
| date | string | ❌ | 日期，格式 YYYY-MM-DD |
| time_range | string | ❌ | 时间范围（用于异常检测） |

#### 列出报表

```
GET /reports?report_type={type}&limit={limit}
```

#### 清理旧报表

```
POST /reports/cleanup
```

---

### 业务目标处理

#### 处理业务目标

```
POST /goals/process
```

**请求体** — `BusinessGoalRequest`
```json
{
  "goal": "分析竞品定价策略并生成报告",
  "target_metrics": {"roi": 0.15},
  "deadline": "2026-06-01"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| goal | string | ✅ | 业务目标描述 |
| target_metrics | object | ❌ | 目标指标 |
| deadline | string | ❌ | 截止时间 |

系统会根据目标关键词自动创建对应任务：
- 竞品/竞争对手/市场分析 → `skill:competitor_analysis`
- 异常/问题/监控 → `skill:abnormal_detection`
- 客服/服务/支持 → `skill:customer_service_router`
- 售后/退货/退款 → `skill:after_sales_triage`
- 报表/报告/数据 → `skill:daily_report`

---

## 3. RAG 知识库服务 (端口 8006)

基础路径: `http://localhost:8006`

### 健康检查

```
GET /health
GET /
```

### RAG 查询

```
GET /rag/query?query={query}&domain={domain}&top_k={top_k}&threshold={threshold}
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| query | string | ✅ | — | 查询文本 |
| domain | string | ✅ | — | 知识领域: `product` / `aftersale` / `rules` / `scripts` |
| top_k | int | ❌ | 5 | 返回结果数量 (1-20) |
| threshold | float | ❌ | 0.5 | 相似度阈值 (0.0-1.0) |

**响应** — `QueryResponse`
```json
{
  "query": "退货流程",
  "domain": "aftersale",
  "results": [...],
  "total_results": 3,
  "processing_time": 0.05
}
```

### 全领域查询

```
GET /rag/query/all?query={query}&top_k={top_k}
```

### 获取所有领域

```
GET /rag/domains
```

### 服务统计

```
GET /rag/stats
```

### 知识条目 CRUD

```
GET    /rag/knowledge/{domain}                   # 获取知识条目列表
POST   /rag/knowledge/{domain}                   # 创建知识条目
PUT    /rag/knowledge/{domain}/{item_id}         # 更新知识条目
DELETE /rag/knowledge/{domain}/{item_id}         # 删除知识条目
```

**创建请求体** — `KnowledgeItemCreate`
```json
{
  "id": "faq_001",
  "domain": "aftersale",
  "category": "退货",
  "question": "如何退货？",
  "answer": "联系客服发起退货...",
  "keywords": ["退货", "退款"],
  "metadata": {}
}
```

### 索引重建

```
POST /rag/rebuild-index/{domain}     # 重建指定领域索引
POST /rag/rebuild-index-all          # 重建所有索引
```

### 缓存管理

```
GET  /cache/stats          # 获取缓存统计信息
POST /cache/invalidate     # 清除缓存
```

---

## 4. 竞品爬虫服务 (端口 8008)

基础路径: `http://localhost:8008`

### 健康检查

```
GET /      # 服务状态
GET /health  # 健康检查
```

---

### 商品爬取

#### 批量爬取

```
POST /crawl
```

**请求体** — `CrawlRequest`
```json
{
  "urls": [
    {"platform": "douyin", "url": "https://...", "product_id": "P001"},
    {"platform": "pdd", "url": "https://...", "product_id": "P002"}
  ]
}
```

**响应** — `CrawlResponse`
```json
{
  "total": 2,
  "successful": 2,
  "failed": 0,
  "results": [...]
}
```

#### 单品爬取

```
POST /crawl/single
```

**请求体** — `ProductUrl`
```json
{
  "platform": "douyin",
  "url": "https://...",
  "product_id": "P001"
}
```

---

### 调度任务

```
POST   /tasks                       # 创建调度任务
GET    /tasks                       # 列出所有任务
GET    /tasks/{task_id}             # 获取指定任务
DELETE /tasks/{task_id}             # 删除任务
POST   /tasks/{task_id}/pause       # 暂停任务
POST   /tasks/{task_id}/resume      # 恢复任务
```

**创建任务** — `TaskCreate`
```json
{
  "platform": "douyin",
  "product_id": "P001",
  "url": "https://...",
  "task_type": "price_check",
  "interval_minutes": 60
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| platform | Platform enum | ✅ | 平台 |
| product_id | string | ✅ | 商品 ID |
| url | string | ✅ | 商品 URL |
| task_type | TaskType enum | ✅ | 任务类型 (price_check / title_check / full_check) |
| interval_minutes | int | ❌ | 间隔分钟数 (1-1440) |

---

### 数据分析

```
GET /analysis/price/{platform}/{product_id}?days={days}       # 价格趋势
GET /analysis/title/{platform}/{product_id}?days={days}       # 标题变化
GET /analysis/promotions/{platform}/{product_id}              # 促销监控
GET /analysis/report/{product_id}?platforms={platforms}       # 竞品分析报告
```

**价格趋势响应**
```json
{
  "platform": "douyin",
  "product_id": "P001",
  "analysis": {
    "current_price": 99.99,
    "min_price": 79.99,
    "max_price": 129.99,
    "avg_price": 95.50,
    "price_change": -10.00,
    "price_change_percent": -9.09,
    "trend": "decreasing",
    "volatility": 0.15
  }
}
```

---

### 数据查询

```
GET /products?platform={platform}                                    # 监控商品列表
GET /products/search?keyword={keyword}&platform={platform}           # 搜索商品
GET /products/{platform}/{product_id}/history?days={days}            # 价格历史
GET /stats                                                           # 服务统计
GET /anti-crawler/stats                                              # 反爬统计
```

---

## 5. 商品管理服务 (端口 8006)

基础路径: `http://localhost:8006`

独立的商品与客户管理微服务，使用 SQLAlchemy + SQLite，支持商品、分类、客户的完整 CRUD 及批量操作。

### 健康检查

```
GET /         # 服务状态
GET /health   # 健康检查
```

---

### 商品 CRUD

#### 获取商品列表

```
GET /api/products?keyword={keyword}&platform={platform}&category={category}&status={status}&page={page}&page_size={page_size}
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| keyword | string | ❌ | — | 关键词搜索（匹配商品名称和SKU） |
| platform | string | ❌ | — | 平台筛选: `douyin` / `pdd` / `xianyu` / `kuaishou` |
| category | string | ❌ | — | 分类筛选 |
| status | string | ❌ | — | 状态筛选: `active` / `draft` / `out_of_stock` / `disabled` |
| page | int | ❌ | 1 | 页码 |
| page_size | int | ❌ | 20 | 每页数量 (1-100) |

**响应**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Type-C数据线",
      "sku": "SKU0001",
      "platform": "douyin",
      "platform_name": "抖音",
      "category": "数码配件",
      "price": 99.99,
      "cost": 45.00,
      "stock": 100,
      "sales": 256,
      "status": "active",
      "status_label": "在售",
      "image": "https://picsum.photos/seed/1/80/80",
      "description": "Type-C数据线的详细描述",
      "created_at": "2026-05-29T10:00:00",
      "updated_at": "2026-05-29T10:00:00"
    }
  ],
  "meta": {
    "total": 50,
    "page": 1,
    "page_size": 20,
    "total_pages": 3
  }
}
```

#### 获取商品统计

```
GET /api/products/stats
```

**响应**
```json
{
  "success": true,
  "data": {
    "total": 50,
    "active": 35,
    "lowStock": 8,
    "outOfStock": 5,
    "totalValue": 125000.00
  }
}
```

#### 获取商品详情

```
GET /api/products/{product_id}
```

**响应 200** — 商品详情
**响应 404** — `{"detail": "商品 {product_id} 不存在"}`

#### 创建商品

```
POST /api/products
```

**请求体** — `ProductCreateRequest`
```json
{
  "name": "新品数据线",
  "sku": "SKU0051",
  "platform": "douyin",
  "category": "数码配件",
  "price": 29.99,
  "cost": 12.00,
  "stock": 200,
  "image": "https://example.com/image.jpg",
  "description": "高品质Type-C数据线"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | ✅ | 商品名称 (1-200字符) |
| sku | string | ✅ | SKU编码 (1-50字符，唯一) |
| platform | string | ✅ | 所属平台: `douyin` / `pdd` / `xianyu` / `kuaishou` |
| category | string | ✅ | 商品分类 |
| price | float | ✅ | 售价 (>0) |
| cost | float | ❌ | 成本价 (≥0，默认0) |
| stock | int | ❌ | 库存数量 (≥0，默认0) |
| image | string | ❌ | 商品图片URL |
| description | string | ❌ | 商品描述 |
| status | string | ❌ | 商品状态 (默认 `active`) |

**响应 200** — 创建成功
**响应 409** — `{"detail": "SKU 'xxx' 已存在"}`

#### 更新商品

```
PATCH /api/products/{product_id}
```

**请求体** — `ProductUpdateRequest`（所有字段可选）
```json
{
  "price": 39.99,
  "stock": 150,
  "status": "active"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | 商品名称 |
| sku | string | SKU编码 |
| platform | string | 所属平台 |
| category | string | 商品分类 |
| price | float | 售价 |
| cost | float | 成本价 |
| stock | int | 库存数量 |
| image | string | 商品图片URL |
| description | string | 商品描述 |
| status | string | 商品状态 |
| sales | int | 销量 |

**响应 200** — 更新成功
**响应 404** — `{"detail": "商品 {product_id} 不存在"}`

#### 删除商品

```
DELETE /api/products/{product_id}
```

**响应 200** — `{"success": true, "message": "商品 {product_id} 已删除"}`

---

### 商品批量操作

#### 批量删除

```
POST /api/products/batch/delete
```

**请求体** — `BatchActionRequest`
```json
{
  "product_ids": [1, 2, 3]
}
```

**响应** — `{"success": true, "message": "已删除 3 个商品"}`

#### 批量下架

```
POST /api/products/batch/disable
```

**请求体** — `BatchActionRequest`
```json
{
  "product_ids": [1, 2, 3]
}
```

**响应** — `{"success": true, "message": "已下架 3 个商品"}`

#### 批量调价

```
POST /api/products/batch/price
```

**请求体** — `BatchPriceAdjustRequest`
```json
{
  "product_ids": [1, 2, 3],
  "adjust_type": "increase_pct",
  "adjust_value": 10
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| product_ids | int[] | ✅ | 商品ID列表 (至少1个) |
| adjust_type | string | ✅ | 调整方式: `increase_pct` / `decrease_pct` / `increase_amt` / `decrease_amt` |
| adjust_value | float | ✅ | 调整数值 (>0) |

**响应** — `{"success": true, "message": "已调整 3 个商品的价格"}`

---

### 分类管理

#### 获取所有分类

```
GET /api/categories
```

**响应**
```json
{
  "success": true,
  "data": [
    {"id": 1, "name": "数码配件", "parent_id": null, "sort_order": 0},
    {"id": 2, "name": "家居日用", "parent_id": null, "sort_order": 1}
  ]
}
```

#### 创建分类

```
POST /api/categories
```

**请求体** — `CategoryCreateRequest`
```json
{
  "name": "新品专区",
  "parent_id": null,
  "sort_order": 10
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | ✅ | 分类名称 (1-100字符) |
| parent_id | int | ❌ | 父分类ID |
| sort_order | int | ❌ | 排序序号 (默认0) |

**响应 200** — 创建成功
**响应 409** — `{"detail": "分类 'xxx' 已存在"}`

#### 删除分类

```
DELETE /api/categories/{category_id}
```

> 注意：删除操作为软删除（设置 `is_active=False`）

**响应 200** — `{"success": true, "message": "分类 'xxx' 已禁用"}`

---

### 客户管理

#### 获取客户统计

```
GET /api/customers/stats
```

**响应**
```json
{
  "success": true,
  "data": {
    "total": 50,
    "newCustomers": 8,
    "activeCustomers": 35,
    "vipCustomers": 12
  }
}
```

#### 获取客户列表

```
GET /api/customers?keyword={keyword}&level={level}&tag={tag}&page={page}&page_size={page_size}
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| keyword | string | ❌ | — | 搜索（匹配姓名、手机、邮箱） |
| level | string | ❌ | — | 等级筛选: `普通` / `银卡` / `金卡` / `钻石` |
| tag | string | ❌ | — | 标签筛选 |
| page | int | ❌ | 1 | 页码 |
| page_size | int | ❌ | 20 | 每页数量 (1-100) |

**响应**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "张伟",
      "phone": "13812345678",
      "email": "customer1@example.com",
      "gender": "男",
      "level": "金卡",
      "tags": "[\"VIP\", \"高价值\"]",
      "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=1",
      "address": "北京市朝阳区某某街道1号",
      "total_spent": 35000.00,
      "order_count": 25,
      "last_order_time": "2026-05-25 14:30",
      "points": 5000,
      "balance": 1500.00,
      "created_at": "2026-01-15T10:00:00",
      "updated_at": "2026-05-25T14:30:00"
    }
  ],
  "meta": {
    "total": 50,
    "page": 1,
    "page_size": 20,
    "total_pages": 3
  }
}
```

#### 获取客户详情

```
GET /api/customers/{customer_id}
```

**响应 200** — 客户详情
**响应 404** — `{"detail": "客户 {customer_id} 不存在"}`

#### 创建客户

```
POST /api/customers
```

**请求体** — `CustomerCreateRequest`
```json
{
  "name": "李芳",
  "phone": "13987654321",
  "email": "lifang@example.com",
  "gender": "女",
  "level": "普通",
  "tags": ["新客户"],
  "address": "上海市浦东新区某某路100号"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | ✅ | 客户姓名 (1-100字符) |
| phone | string | ❌ | 手机号 |
| email | string | ❌ | 邮箱 |
| gender | string | ❌ | 性别: `男` / `女` |
| level | string | ❌ | 等级 (默认 `普通`) |
| tags | string[] | ❌ | 标签列表 |
| avatar | string | ❌ | 头像URL |
| address | string | ❌ | 地址 |
| total_spent | float | ❌ | 累计消费 |
| order_count | int | ❌ | 订单数 |
| last_order_time | string | ❌ | 最近下单时间 |
| points | int | ❌ | 积分 |
| balance | float | ❌ | 账户余额 |

#### 更新客户

```
PATCH /api/customers/{customer_id}
```

**请求体** — `CustomerUpdateRequest`（所有字段可选，同创建接口）

**响应 200** — 更新成功
**响应 404** — `{"detail": "客户 {customer_id} 不存在"}`

#### 删除客户

```
DELETE /api/customers/{customer_id}
```

**响应 200** — `{"success": true, "message": "客户 {customer_id} 已删除"}`

---

## 6. 抖店适配器 (端口 8001)

基础路径: `http://localhost:8001`

抖店开放平台 API 适配器，提供商品、订单、库存、售后、物流等管理功能。

### 健康检查

```
GET /         # 服务状态
GET /health   # 健康检查
```

### OAuth 授权

```
GET  /auth/url                    # 获取授权链接
POST /auth/callback               # OAuth 回调
POST /auth/refresh                # 刷新令牌
```

### 商品管理 `/api/shop/douyin`

```
GET /api/shop/douyin/products/list                    # 商品列表
GET /api/shop/douyin/products/detail/{product_id}     # 商品详情
```

### 订单管理

```
GET /api/shop/douyin/orders/list                      # 订单列表
GET /api/shop/douyin/orders/detail/{order_id}         # 订单详情
```

### 库存管理

```
POST /api/shop/douyin/inventory/update                # 更新库存
```

### 售后管理

```
GET /api/shop/douyin/aftersales/list                  # 售后列表
```

### 物流管理

```
POST /api/shop/douyin/logistics/send                  # 发货
```

---

## 7. 快手适配器 (端口 8002)

基础路径: `http://localhost:8002`

快手开放平台 API 适配器，提供商品、订单、库存、物流等管理功能。内置 Token 自动刷新调度器。

### 健康检查

```
GET /         # 服务状态
GET /health   # 健康检查
```

### OAuth 授权

```
GET  /auth/url                    # 获取授权链接
POST /auth/callback               # OAuth 回调
POST /auth/refresh                # 刷新令牌
GET  /auth/token-status           # Token 状态检查
POST /auth/force-refresh          # 强制刷新 Token
```

### 商品管理 `/api/shop/kuaishou`

```
GET /api/shop/kuaishou/products/list                    # 商品列表
GET /api/shop/kuaishou/products/detail/{product_id}     # 商品详情
```

### 订单管理

```
GET /api/shop/kuaishou/orders/list                      # 订单列表
GET /api/shop/kuaishou/orders/detail/{order_id}         # 订单详情
```

### 库存管理

```
POST /api/shop/kuaishou/inventory/update                # 更新库存
```

### 物流管理

```
POST /api/shop/kuaishou/logistics/send                  # 发货
```

---

## 8. OMS 订单中台 (端口 8005)

基础路径: `http://localhost:8005`

统一订单管理中台，聚合多平台订单、库存、工单、运营看板数据。通过 API Gateway 代理，前端统一通过 `/api/orders`、`/api/inventory`、`/api/tickets`、`/api/dashboard` 访问。

### 健康检查

```
GET /         # 服务状态
GET /health   # 健康检查
```

---

### 订单管理 `/api/orders`

#### 获取订单列表

```
GET /api/orders
```

**响应** — `Order[]`

#### 获取订单统计

```
GET /api/orders/statistics
```

#### 获取最近订单

```
GET /api/orders/recent
```

#### 获取高风险订单

```
GET /api/orders/high-risk
```

#### 获取退款中订单

```
GET /api/orders/refunding
```

#### 搜索订单

```
GET /api/orders/search
```

#### 获取订单详情

```
GET /api/orders/{order_id}
```

**响应 200** — `Order`
**响应 404** — 订单不存在

#### 创建订单

```
POST /api/orders
```

**请求体** — `Order`
```json
{
  "order_id": "ORD001",
  "platform": "douyin",
  "platform_order_id": "DY123456",
  "status": "pending",
  "payment_status": "unpaid",
  "items": [
    {
      "sku_id": "SKU001",
      "product_name": "Type-C数据线",
      "quantity": 2,
      "unit_price": 29.99,
      "total_price": 59.98
    }
  ],
  "total_amount": 59.98,
  "discount_amount": 5.00,
  "actual_amount": 54.98,
  "customer": {
    "customer_id": "C001",
    "name": "张三",
    "phone": "13800138000",
    "address": "北京市朝阳区xxx路",
    "platform_uid": "uid_123"
  }
}
```

#### 同步订单 (手动触发)

```
POST /api/orders/sync/{platform}/{shop_id}
```

#### 更新订单状态

```
PUT /api/orders/{order_id}/status
```

#### 更新支付状态

```
PUT /api/orders/{order_id}/payment-status
```

#### 添加订单标签

```
POST /api/orders/{order_id}/tags
```

#### 移除订单标签

```
DELETE /api/orders/{order_id}/tags
```

#### 设置风险等级

```
PUT /api/orders/{order_id}/risk-level
```

#### 获取指定平台订单

```
GET /api/orders/platform/{platform}
```

#### 获取指定状态订单

```
GET /api/orders/status/{status}
```

#### 删除订单

```
DELETE /api/orders/{order_id}
```

---

### 库存管理 `/api/inventory`

#### 获取所有库存

```
GET /api/inventory
```

**响应** — `InventoryItem[]`

#### 获取库存统计

```
GET /api/inventory/statistics
```

#### 获取低库存商品

```
GET /api/inventory/low-stock
```

#### 获取高风险商品

```
GET /api/inventory/high-risk
```

#### 搜索库存

```
GET /api/inventory/search
```

#### 获取库存详情

```
GET /api/inventory/{sku_id}
```

**响应 200** — `InventoryItem`

#### 创建库存项目

```
POST /api/inventory
```

#### 手动触发SKU同步

```
POST /api/inventory/sync/{platform}/{shop_id}
```

#### 删除库存项目

```
DELETE /api/inventory/{sku_id}
```

#### 更新库存数量

```
PUT /api/inventory/{sku_id}/stock
```

#### 锁定库存

```
POST /api/inventory/{sku_id}/lock
```

#### 解锁库存

```
POST /api/inventory/{sku_id}/unlock
```

#### 发货扣减

```
POST /api/inventory/{sku_id}/ship
```

#### 到货增加

```
POST /api/inventory/{sku_id}/receive
```

#### 添加风险标签

```
POST /api/inventory/{sku_id}/risk-tags
```

#### 移除风险标签

```
DELETE /api/inventory/{sku_id}/risk-tags
```

#### 设置风险等级

```
PUT /api/inventory/{sku_id}/risk-level
```

#### 获取指定平台库存

```
GET /api/inventory/platform/{platform}
```

---

### 工单管理 `/api/tickets`

#### 获取所有工单

```
GET /api/tickets
```

**响应** — `Ticket[]`

#### 获取工单统计

```
GET /api/tickets/statistics
```

#### 获取最近工单

```
GET /api/tickets/recent
```

#### 获取待处理工单

```
GET /api/tickets/open
```

#### 获取高优先级工单

```
GET /api/tickets/high-priority
```

#### 获取超时工单

```
GET /api/tickets/overdue
```

#### 获取退款工单

```
GET /api/tickets/refund
```

#### 获取投诉工单

```
GET /api/tickets/complaint
```

#### 搜索工单

```
GET /api/tickets/search
```

#### 获取工单详情

```
GET /api/tickets/{ticket_id}
```

**响应 200** — `Ticket`

#### 创建工单

```
POST /api/tickets
```

#### 更新工单状态

```
PUT /api/tickets/{ticket_id}/status
```

#### 分配工单

```
PUT /api/tickets/{ticket_id}/assign
```

#### 解决工单

```
PUT /api/tickets/{ticket_id}/resolve
```

#### 关闭工单

```
PUT /api/tickets/{ticket_id}/close
```

#### 更新退款信息

```
PUT /api/tickets/{ticket_id}/refund
```

#### 添加工单标签

```
POST /api/tickets/{ticket_id}/tags
```

#### 移除工单标签

```
DELETE /api/tickets/{ticket_id}/tags
```

#### 设置工单优先级

```
PUT /api/tickets/{ticket_id}/priority
```

#### 获取指定订单工单

```
GET /api/tickets/order/{order_id}
```

#### 获取指定平台工单

```
GET /api/tickets/platform/{platform}
```

#### 获取指定处理人工单

```
GET /api/tickets/assignee/{assignee}
```

---

### 运营看板 `/api/dashboard`

#### 获取看板统计

```
GET /api/dashboard
```

**响应** — `DashboardStats`
```json
{
  "total_orders": 150,
  "pending_orders": 12,
  "processing_orders": 8,
  "completed_orders": 120,
  "total_revenue": 45000.00,
  "today_revenue": 3200.00,
  "total_tickets": 25,
  "open_tickets": 5,
  "resolved_tickets": 18,
  "low_stock_items": 3,
  "high_risk_items": 1,
  "platform_stats": {},
  "recent_orders": [],
  "recent_tickets": []
}
```

#### 获取综合统计

```
GET /api/dashboard/stats
```

#### 获取趋势数据

```
GET /api/dashboard/trend
```

#### 获取概览数据

```
GET /api/dashboard/overview
```

#### 获取指定平台数据

```
GET /api/dashboard/platform/{platform}
```

#### 获取告警信息

```
GET /api/dashboard/alerts
```

---

## 9. 拼多多客服适配器 (端口 8003)

基础路径: `http://localhost:8003`

拼多多客服自动化服务，基于 Playwright 实现浏览器自动化。

### 健康检查

```
GET /         # 服务状态
GET /health   # 健康检查
```

> ⚠️ 客服自动化接口待实现

---

## 10. 闲鱼适配器 (端口 8004)

基础路径: `http://localhost:8004`

闲鱼平台自动化服务，基于 Playwright 实现浏览器自动化。

### 健康检查

```
GET /         # 服务状态
GET /health   # 健康检查
```

> ⚠️ 自动化接口待实现

---

## 数据模型

### ShopCreate / ShopResponse

```typescript
interface ShopCreate {
  platform: string;     // 平台标识
  shop_name: string;    // 店铺名称
}

interface ShopResponse extends ShopCreate {
  id: string;           // 店铺 ID
  auth_status: string;  // 授权状态: pending / authorized / expired
  created_at: string;   // 创建时间 (ISO 8601)
  updated_at: string;   // 更新时间 (ISO 8601)
}
```

### ProductCreate / ProductResponse

```typescript
interface ProductCreate {
  shop_id: string;
  title: string;
  price: number;
  cost_price?: number;
  sku_id?: string;
}

interface ProductResponse extends ProductCreate {
  id: string;
  status: string;           // draft / active / inactive
  listing_risk_score: number;
  margin_score: number;     // 毛利率百分比
  created_at: string;
  updated_at: string;
}
```

### TaskRequest / SkillExecuteRequest / ReportRequest

```typescript
interface TaskRequest {
  task_type: string;
  params: Record<string, any>;
  priority: "low" | "normal" | "high" | "urgent";
}

interface SkillExecuteRequest {
  skill_name: string;
  params: Record<string, any>;
}

interface ReportRequest {
  report_type: "daily" | "weekly" | "abnormal";
  date?: string;
  time_range?: string;
}
```

### ProductCreateRequest (商品服务)

```typescript
interface ProductCreateRequest {
  name: string;           // 商品名称 (1-200字符)
  sku: string;            // SKU编码 (唯一)
  platform: string;       // 平台: douyin / pdd / xianyu / kuaishou
  category: string;       // 商品分类
  price: number;          // 售价 (>0)
  cost?: number;          // 成本价 (默认0)
  stock?: number;         // 库存数量 (默认0)
  image?: string;         // 图片URL
  description?: string;   // 描述
  status?: string;        // 状态 (默认 active)
}

interface ProductUpdateRequest {
  name?: string;
  sku?: string;
  platform?: string;
  category?: string;
  price?: number;
  cost?: number;
  stock?: number;
  image?: string;
  description?: string;
  status?: string;
  sales?: number;
}

interface BatchActionRequest {
  product_ids: number[];  // 商品ID列表
}

interface BatchPriceAdjustRequest {
  product_ids: number[];
  adjust_type: "increase_pct" | "decrease_pct" | "increase_amt" | "decrease_amt";
  adjust_value: number;   // 调整数值 (>0)
}
```

### CategoryCreateRequest

```typescript
interface CategoryCreateRequest {
  name: string;           // 分类名称 (1-100字符)
  parent_id?: number;     // 父分类ID
  sort_order?: number;    // 排序序号 (默认0)
}
```

### CustomerCreateRequest / CustomerUpdateRequest

```typescript
interface CustomerCreateRequest {
  name: string;           // 客户姓名 (1-100字符)
  phone?: string;         // 手机号
  email?: string;         // 邮箱
  gender?: string;        // 性别: 男 / 女
  level?: string;         // 等级: 普通 / 银卡 / 金卡 / 钻石
  tags?: string[];        // 标签列表
  avatar?: string;        // 头像URL
  address?: string;       // 地址
  total_spent?: number;   // 累计消费
  order_count?: number;   // 订单数
  last_order_time?: string;
  points?: number;        // 积分
  balance?: number;       // 账户余额
}
```

### Platform 枚举

```
douyin | kuaishou | pdd | xianyu
```

### 商品状态枚举

```
active | draft | out_of_stock | disabled
```

### 客户等级枚举

```
普通 | 银卡 | 金卡 | 钻石
```

---

## 错误响应

所有服务统一错误格式：

```json
{
  "detail": "错误描述"
}
```

| HTTP 状态码 | 含义 |
|------------|------|
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
