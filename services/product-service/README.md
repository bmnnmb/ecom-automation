# 商品管理服务 (Product Service)

独立微服务，端口 `8006`。提供商品、分类、客户的完整 CRUD 操作及运营看板数据，使用 SQLite 持久化存储。

## 技术栈

- **框架**: FastAPI + Uvicorn
- **ORM**: SQLAlchemy 2.0
- **数据库**: SQLite (`data/product_service.db`)
- **校验**: Pydantic v2

## 启动

```bash
cd services/product-service
pip install -r requirements.txt
python main.py
# 服务运行在 http://0.0.0.0:8006
```

首次启动自动初始化数据库，创建默认分类和 50 条示例商品数据。

## API 端点

### 商品管理

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/products` | 商品列表（支持搜索、筛选、分页） |
| `GET` | `/api/products/stats` | 商品统计数据 |
| `GET` | `/api/products/{product_id}` | 商品详情 |
| `POST` | `/api/products` | 创建商品 |
| `PATCH` | `/api/products/{product_id}` | 更新商品 |
| `DELETE` | `/api/products/{product_id}` | 删除商品 |

### 批量操作

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/products/batch/delete` | 批量删除 |
| `POST` | `/api/products/batch/disable` | 批量下架 |
| `POST` | `/api/products/batch/price` | 批量调价 |

### 分类管理

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/categories` | 获取所有分类 |
| `POST` | `/api/categories` | 创建分类 |
| `DELETE` | `/api/categories/{category_id}` | 删除分类（软删除） |

### 客户管理

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/customers` | 客户列表（支持搜索、筛选、分页） |
| `GET` | `/api/customers/stats` | 客户统计数据 |
| `GET` | `/api/customers/{customer_id}` | 客户详情 |
| `POST` | `/api/customers` | 创建客户 |
| `PATCH` | `/api/customers/{customer_id}` | 更新客户 |
| `DELETE` | `/api/customers/{customer_id}` | 删除客户 |

### 运营看板

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/dashboard/stats` | 综合统计数据 |
| `GET` | `/api/dashboard/trend` | 趋势数据（支持 `days` 参数，1-90 天） |

### 健康检查

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/health` | 健康状态 |
| `GET` | `/` | 服务信息 |

## 查询参数

商品列表 (`GET /api/products`) 支持以下筛选参数：

| 参数 | 类型 | 说明 |
|------|------|------|
| `keyword` | string | 按名称或 SKU 搜索 |
| `platform` | string | 平台筛选: `douyin`/`pdd`/`xianyu`/`kuaishou` |
| `category` | string | 分类筛选 |
| `status` | string | 状态筛选: `active`/`draft`/`out_of_stock`/`disabled` |
| `page` | int | 页码（默认 1） |
| `page_size` | int | 每页数量（默认 20，最大 100） |

客户列表 (`GET /api/customers`) 支持以下筛选参数：

| 参数 | 类型 | 说明 |
|------|------|------|
| `keyword` | string | 按姓名、手机、邮箱搜索 |
| `level` | string | 等级筛选: `普通`/`银卡`/`金卡`/`钻石` |
| `tag` | string | 标签筛选 |
| `page` | int | 页码（默认 1） |
| `page_size` | int | 每页数量（默认 20，最大 100） |

## 数据模型

### Product（商品）

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string(200) | 商品名称 |
| `sku` | string(50) | SKU 编码（唯一） |
| `platform` | string(20) | 平台标识 |
| `category` | string(100) | 分类名称 |
| `price` | float | 售价 |
| `cost` | float | 成本价 |
| `stock` | int | 库存数量 |
| `sales` | int | 累计销量 |
| `status` | string(20) | 状态 |
| `image` | string(500) | 图片 URL |
| `description` | text | 描述 |

### Category（分类）

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string(100) | 分类名称（唯一） |
| `parent_id` | int | 父分类 ID（支持层级） |
| `sort_order` | int | 排序序号 |
| `is_active` | bool | 是否启用 |

### Customer（客户）

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string(100) | 客户姓名 |
| `phone` | string(20) | 手机号 |
| `email` | string(100) | 邮箱 |
| `gender` | string(10) | 性别: 男 / 女 |
| `level` | string(20) | 等级: 普通 / 银卡 / 金卡 / 钻石 |
| `tags` | text | 标签（JSON 数组） |
| `avatar` | string(500) | 头像 URL |
| `address` | string(500) | 地址 |
| `total_spent` | float | 累计消费 |
| `order_count` | int | 订单数 |
| `last_order_time` | string(30) | 最近下单时间 |
| `points` | int | 积分 |
| `balance` | float | 账户余额 |

## 平台与状态枚举

**平台**: `douyin`(抖音) | `pdd`(拼多多) | `xianyu`(闲鱼) | `kuaishou`(快手)

**状态**: `active`(在售) | `draft`(草稿) | `out_of_stock`(缺货) | `disabled`(已下架)

## 依赖

```
fastapi>=0.104.0
uvicorn>=0.24.0
sqlalchemy>=2.0.0
pydantic>=2.0.0
```
