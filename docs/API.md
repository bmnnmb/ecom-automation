# ecom-automation API Documentation

> 自动生成于 2026-05-27 | 源码扫描自 4 个 FastAPI 服务

本文档覆盖 ecom-automation 项目的全部 REST API 端点，共 **4 个服务、50+ 个接口**。

## 目录

- [服务概览](#服务概览)
- [1. API Gateway (端口 8001)](#1-api-gateway-端口-8001)
  - [健康检查](#健康检查)
  - [统一鉴权 /api/auth](#统一鉴权-apiauth)
  - [店铺管理 /api/shops](#店铺管理-apishops)
  - [商品管理 /api/products](#商品管理-apiproducts)
  - [订单管理 /api/orders](#订单管理-apiorders)
  - [客服消息 /api/messages](#客服消息-apimessages)
  - [售后服务 /api/aftersales](#售后服务-apiaftersales)
  - [竞品分析 /api/competitors](#竞品分析-apicompetitors)
  - [报表统计 /api/reports](#报表统计-apireports)
- [2. Hermes 总控服务 (端口 8080)](#2-hermes-总控服务-端口-8080)
  - [任务管理](#任务管理)
  - [技能执行](#技能执行)
  - [报表生成](#报表生成)
  - [业务目标处理](#业务目标处理)
- [3. RAG 知识库服务](#3-rag-知识库服务)
- [4. 竞品爬虫服务 (端口 8000)](#4-竞品爬虫服务-端口-8000)

---

## 服务概览

| 服务 | 端口 | 技术栈 | 说明 |
|------|------|--------|------|
| api-gateway | 8001 | FastAPI | 统一 REST API 网关 |
| hermes-control | 8080 | FastAPI | 任务调度、技能执行、报表 |
| rag-service | — | FastAPI | RAG 知识库检索 |
| competitor-crawler | 8000 | FastAPI | 竞品数据采集与分析 |

---

## 1. API Gateway (端口 8001)

基础路径: `http://localhost:8001`

### 健康检查

```
GET /health
```

**响应**
```json
{
  "status": "healthy",
  "service": "ecom-api-gateway",
  "version": "1.0.0"
}
```

---

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

> ⚠️ 待实现

```
GET /api/orders                  # 订单列表（占位）
GET /api/orders/{order_id}       # 订单详情（占位）
```

---

### 客服消息 `/api/messages`

> ⚠️ 待实现

```
GET /api/messages                # 消息列表（占位）
```

---

### 售后服务 `/api/aftersales`

> ⚠️ 待实现

```
GET /api/aftersales              # 售后列表（占位）
```

---

### 竞品分析 `/api/competitors`

> ⚠️ 待实现

```
GET /api/competitors             # 竞品列表（占位）
```

---

### 报表统计 `/api/reports`

> ⚠️ 待实现

```
GET /api/reports/daily           # 日报（占位）
GET /api/reports/weekly          # 周报（占位）
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

## 3. RAG 知识库服务

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

---

## 4. 竞品爬虫服务 (端口 8000)

基础路径: `http://localhost:8000`

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
GET /analysis/title/{platform}/{platform}?days={days}         # 标题变化
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
```

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

### Platform 枚举

```
douyin | kuaishou | pdd | xianyu
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
