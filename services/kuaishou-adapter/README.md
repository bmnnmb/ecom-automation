# 快手Adapter服务

快手开放平台API适配器服务，提供商品、订单、库存、物流等管理功能。内置Token自动刷新调度器，保障长期稳定运行。

## 功能特性

- **商品管理**: 获取商品列表、商品详情
- **订单管理**: 获取订单列表、订单详情
- **库存管理**: 更新商品库存
- **物流管理**: 发货操作
- **OAuth授权**: 授权管理、token刷新
- **Token自动刷新**: 后台调度器定期检查token状态，提前30分钟自动刷新即将过期的token

## API端点

基础路径: `http://localhost:8002`

业务API以 `/api/shop/kuaishou` 为前缀，授权API在根路径下。

### 授权API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/auth/url` | 获取授权URL（参数: `redirect_uri`） |
| POST | `/auth/callback` | OAuth回调（参数: `code`） |
| POST | `/auth/refresh` | 手动刷新token |
| GET | `/auth/token-status` | 查看Token调度器运行状态 |
| POST | `/auth/force-refresh` | 强制立即刷新token（通过调度器） |

### 商品API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/shop/kuaishou/products/list` | 获取商品列表（支持分页: `page`, `page_size`） |
| GET | `/api/shop/kuaishou/products/detail/{product_id}` | 获取商品详情 |

### 订单API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/shop/kuaishou/orders/list` | 获取订单列表（支持分页和状态筛选） |
| GET | `/api/shop/kuaishou/orders/detail/{order_id}` | 获取订单详情 |

### 库存API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/shop/kuaishou/inventory/update` | 更新库存 |

### 物流API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/shop/kuaishou/logistics/send` | 发货 |

### 系统端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 服务信息 |
| GET | `/health` | 健康检查 |

## Token自动刷新调度器

内置 `TokenRefreshScheduler`，在服务启动时自动运行：

- **检查间隔**: 每5分钟检查一次token状态
- **提前刷新**: token过期前30分钟自动刷新
- **失败重试**: 指数退避重试（最多3次，基础延迟10秒）
- **状态统计**: 记录刷新次数、失败次数、连续失败次数

### 调度器API

#### 查看调度器状态

```bash
curl http://localhost:8002/auth/token-status
```

响应示例：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "running": true,
    "check_interval_seconds": 300,
    "refresh_ahead_minutes": 30,
    "token_expires_in_seconds": 1800,
    "has_access_token": true,
    "has_refresh_token": true,
    "last_refresh_time": "2026-05-29T10:30:00",
    "last_refresh_success": true,
    "consecutive_failures": 0,
    "total_refreshes": 5,
    "total_failures": 0
  }
}
```

#### 强制刷新token

```bash
curl -X POST http://localhost:8002/auth/force-refresh
```

## 配置

1. 复制 `.env.example` 为 `.env`
2. 配置快手开放平台的 `app_key` 和 `app_secret`
3. 通过 `/auth/url` 获取授权URL进行授权
4. 授权后通过 `/auth/callback` 获取access_token

## 运行

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行服务
python main.py
```

### Docker运行

```bash
# 构建镜像
docker build -t kuaishou-adapter .

# 运行容器
docker run -p 8002:8002 --env-file .env kuaishou-adapter
```

### Docker Compose

作为 `docker-compose.yml` 的一部分运行（推荐）：

```bash
docker compose up -d kuaishou-adapter
```

## 环境变量

| 变量名 | 说明 | 必需 |
|--------|------|------|
| KUAISHOU_APP_KEY | 快手应用AppKey | 是 |
| KUAISHOU_APP_SECRET | 快手应用AppSecret | 是 |
| KUAISHOU_ACCESS_TOKEN | 访问令牌 | 否 |
| KUAISHOU_REFRESH_TOKEN | 刷新令牌 | 否 |
| KUAISHOU_SHOP_ID | 店铺ID | 否 |

## 技术栈

- FastAPI 0.104.1
- Pydantic 2.5.0
- HTTPX 0.25.2
- Loguru 0.7.2
- Uvicorn 0.24.0

## 注意事项

1. 本适配器基于快手开放平台API开发，具体API端点和参数需要根据实际API文档进行调整
2. 签名生成规则需要根据快手开放平台的实际要求进行实现
3. 建议在生产环境中使用HTTPS和适当的安全措施
4. Token调度器会在服务启动时自动运行，无需手动干预
