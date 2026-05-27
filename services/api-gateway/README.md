# API 网关服务

多平台电商自动化系统统一API网关，聚合各微服务接口，提供统一的鉴权、路由和请求管理。

## 功能特性

### 核心功能
- **统一入口**：聚合店铺、商品、订单、客服、售后、竞品、报表等所有业务模块
- **平台鉴权**：支持抖音、快手、拼多多、闲鱼等平台的OAuth2授权流程
- **请求日志**：自动记录所有入站/出站请求，便于调试和审计
- **CORS支持**：默认允许所有来源，适配前端跨域调用
- **全局异常处理**：统一捕获和格式化错误响应

### 技术栈
- **Web框架**：FastAPI 0.104.1
- **ASGI服务器**：Uvicorn 0.24.0
- **数据校验**：Pydantic 2.5.0
- **HTTP客户端**：httpx 0.25.2
- **日志**：loguru 0.7.2
- **容器化**：Docker (Python 3.11-slim)

## 快速开始

### 1. 安装依赖

```bash
cd ~/ecom-automation/services/api-gateway
pip install -r requirements.txt
```

### 2. 配置环境变量

在项目根目录创建 `.env` 文件：

```bash
# 数据库
DATABASE_URL=postgresql://ecom:password@localhost:5432/ecom_automation

# Redis
REDIS_URL=redis://localhost:6379/1

# 平台密钥（按需配置）
DOUYIN_APP_KEY=your_key
DOUYIN_APP_SECRET=your_secret
KUAISHOU_APP_KEY=your_key
KUAISHOU_APP_SECRET=your_secret
PDD_CLIENT_ID=your_id
PDD_CLIENT_SECRET=your_secret
```

### 3. 启动服务

```bash
# 开发模式（热重载）
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. 使用Docker部署

```bash
# 构建镜像
docker build -t ecom-api-gateway .

# 运行容器
docker run -d -p 8000:8000 --name ecom-api-gateway \
  -e DATABASE_URL=postgresql://ecom:password@postgres:5432/ecom_automation \
  -e REDIS_URL=redis://redis:6379/1 \
  ecom-api-gateway
```

## API文档

启动服务后访问：
- Swagger UI：http://localhost:8000/docs
- ReDoc：http://localhost:8000/redoc

### 路由模块

| 模块 | 前缀 | 说明 |
|------|------|------|
| 统一鉴权 | `/api/auth` | 平台OAuth2授权、回调、刷新Token |
| 店铺管理 | `/api/shops` | 店铺CRUD、状态管理 |
| 商品管理 | `/api/products` | 商品查询、创建、状态更新 |
| 订单管理 | `/api/orders` | 订单列表、详情查询 |
| 客服消息 | `/api/messages` | 多平台客服消息收发 |
| 售后服务 | `/api/aftersales` | 退换货、售后工单管理 |
| 竞品分析 | `/api/competitors` | 竞品数据查询与分析 |
| 报表统计 | `/api/reports` | 日报、周报生成与查询 |

### 主要接口

#### 统一鉴权

```bash
# 获取平台授权URL
GET /api/auth/authorize/{platform}
# platform: douyin | kuaishou | pdd | xianyu

# OAuth回调处理
GET /api/auth/callback/{platform}?code=xxx

# 刷新Token
POST /api/auth/refresh/{platform}
```

#### 店铺管理

```bash
# 获取所有店铺
GET /api/shops

# 创建店铺
POST /api/shops
{
  "name": "我的抖音小店",
  "platform": "douyin",
  "shop_id": "123456"
}

# 获取店铺详情
GET /api/shops/{shop_id}

# 删除店铺
DELETE /api/shops/{shop_id}
```

#### 商品管理

```bash
# 获取商品列表
GET /api/products

# 创建商品
POST /api/products
{
  "title": "示例商品",
  "price": 99.99,
  "shop_id": "123456"
}

# 获取商品详情
GET /api/products/{product_id}

# 更新商品状态
PUT /api/products/{product_id}/status
{
  "status": "on_sale"
}
```

#### 订单管理

```bash
# 获取订单列表
GET /api/orders

# 获取订单详情
GET /api/orders/{order_id}
```

#### 报表统计

```bash
# 日报
GET /api/reports/daily?date=2024-01-01

# 周报
GET /api/reports/weekly?week=2024-W01
```

#### 健康检查

```bash
GET /health
# 返回: {"status": "healthy", "service": "ecom-api-gateway", "version": "1.0.0"}
```

## 项目结构

```
api-gateway/
├── main.py              # 主入口，FastAPI应用配置与路由注册
├── requirements.txt     # Python依赖
├── Dockerfile           # Docker构建配置
└── routes/              # 路由模块
    ├── __init__.py
    ├── auth/            # 鉴权模块
    │   ├── __init__.py
    │   ├── oauth.py     # OAuth2授权流程
    │   └── providers.py # 平台提供商抽象
    ├── shops.py         # 店铺管理
    ├── products.py      # 商品管理
    ├── orders.py        # 订单管理
    ├── messages.py      # 客服消息
    ├── aftersales.py    # 售后服务
    ├── competitors.py   # 竞品分析
    └── reports.py       # 报表统计
```

## 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | PostgreSQL连接URL | - |
| `REDIS_URL` | Redis连接URL | - |
| `DOUYIN_APP_KEY` | 抖音开放平台AppKey | - |
| `DOUYIN_APP_SECRET` | 抖音开放平台AppSecret | - |
| `KUAISHOU_APP_KEY` | 快手开放平台AppKey | - |
| `KUAISHOU_APP_SECRET` | 快手开放平台AppSecret | - |
| `PDD_CLIENT_ID` | 拼多多客户端ID | - |
| `PDD_CLIENT_SECRET` | 拼多多客户端Secret | - |

### CORS配置

默认配置允许所有来源（`allow_origins=["*"]`），生产环境建议修改 `main.py` 中的CORS配置，限制为具体前端域名。

## 依赖服务

本服务作为网关层，依赖以下后端服务：

| 服务 | 端口 | 说明 |
|------|------|------|
| PostgreSQL | 5432 | 主数据库 |
| Redis | 6379 | 缓存与会话 |
| 抖音适配器 | 8001 | 抖音平台对接 |
| 快手适配器 | 8002 | 快手平台对接 |
| 拼多多客服适配器 | 8003 | 拼多多客服对接 |
| 闲鱼适配器 | 8004 | 闲鱼平台对接 |
| 竞品爬虫 | 8005 | 竞品数据采集 |
| OMS服务 | 8006 | 订单管理系统 |
| RAG服务 | 8007 | 智能问答 |
| Hermes控制中心 | 8008 | 任务调度与自动化 |

## 故障排查

### 常见问题

1. **服务启动失败 - 端口占用**
   ```bash
   lsof -i :8000
   kill -9 <PID>
   ```

2. **数据库连接失败**
   - 检查PostgreSQL服务是否运行
   - 验证 `DATABASE_URL` 连接信息

3. **下游服务不可用**
   - 检查各适配器服务健康状态：`GET /health`
   - 查看日志中的超时或连接拒绝错误

### 日志查看

```bash
# Docker容器日志
docker logs -f ecom-api-gateway

# 本地开发日志
# loguru默认输出到stderr，开发模式下直接在终端查看
```

## 许可证

内部项目，未经授权不得外传。
