# OMS订单中台服务

电商订单管理系统中台服务，提供多平台订单汇总、库存管理、工单处理和统一运营看板功能。

## 功能特性

### 1. 多平台订单管理
- 支持抖店、快手、拼多多、闲鱼等电商平台
- 订单状态跟踪（待处理、处理中、已发货、已完成、退款中等）
- 支付状态管理
- 订单标签和风险等级管理
- 订单同步（手动触发平台订单同步）

### 2. 库存管理
- SKU级别库存管理
- 可用库存、锁定库存、在途库存
- 库存预警和风险标签
- 自动风险等级评估
- 发货扣减、到货增加库存操作

### 3. 工单管理
- 售后工单处理（退款、换货、退货、投诉、咨询）
- 工单状态跟踪（创建→处理中→已解决→已关闭）
- 优先级管理
- 退款状态跟踪
- 按订单、平台、处理人筛选

### 4. 统一运营看板
- 订单统计和趋势分析
- 库存状态概览
- 工单处理效率
- 平台对比分析
- 系统告警信息

## API接口

> 所有接口均以 `/api` 为前缀，完整API文档访问 `GET /docs` (Swagger UI)

### 订单管理 `/api/orders`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/orders` | 获取所有订单 |
| GET | `/api/orders/statistics` | 获取订单统计 |
| GET | `/api/orders/recent` | 获取最近订单 |
| GET | `/api/orders/high-risk` | 获取高风险订单 |
| GET | `/api/orders/refunding` | 获取退款中订单 |
| GET | `/api/orders/search` | 搜索订单 |
| GET | `/api/orders/{order_id}` | 获取订单详情 |
| POST | `/api/orders` | 创建订单 |
| POST | `/api/orders/sync/{platform}/{shop_id}` | 手动触发订单同步 |
| PUT | `/api/orders/{order_id}/status` | 更新订单状态 |
| PUT | `/api/orders/{order_id}/payment-status` | 更新支付状态 |
| PUT | `/api/orders/{order_id}/risk-level` | 设置订单风险等级 |
| POST | `/api/orders/{order_id}/tags` | 添加订单标签 |
| DELETE | `/api/orders/{order_id}/tags` | 移除订单标签 |
| GET | `/api/orders/platform/{platform}` | 获取指定平台订单 |
| GET | `/api/orders/status/{status}` | 获取指定状态订单 |
| DELETE | `/api/orders/{order_id}` | 删除订单 |

### 库存管理 `/api/inventory`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/inventory` | 获取所有库存 |
| GET | `/api/inventory/statistics` | 获取库存统计 |
| GET | `/api/inventory/low-stock` | 获取低库存商品 |
| GET | `/api/inventory/high-risk` | 获取高风险商品 |
| GET | `/api/inventory/search` | 搜索库存 |
| GET | `/api/inventory/{sku_id}` | 获取库存详情 |
| POST | `/api/inventory` | 创建库存项目 |
| POST | `/api/inventory/sync/{platform}/{shop_id}` | 手动触发SKU同步 |
| DELETE | `/api/inventory/{sku_id}` | 删除库存项目 |
| PUT | `/api/inventory/{sku_id}/stock` | 更新库存数量 |
| POST | `/api/inventory/{sku_id}/lock` | 锁定库存 |
| POST | `/api/inventory/{sku_id}/unlock` | 解锁库存 |
| POST | `/api/inventory/{sku_id}/ship` | 发货扣减库存 |
| POST | `/api/inventory/{sku_id}/receive` | 到货增加库存 |
| POST | `/api/inventory/{sku_id}/risk-tags` | 添加风险标签 |
| DELETE | `/api/inventory/{sku_id}/risk-tags` | 移除风险标签 |
| PUT | `/api/inventory/{sku_id}/risk-level` | 设置风险等级 |
| GET | `/api/inventory/platform/{platform}` | 获取指定平台库存 |

### 工单管理 `/api/tickets`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/tickets` | 获取所有工单 |
| GET | `/api/tickets/statistics` | 获取工单统计 |
| GET | `/api/tickets/recent` | 获取最近工单 |
| GET | `/api/tickets/open` | 获取待处理工单 |
| GET | `/api/tickets/high-priority` | 获取高优先级工单 |
| GET | `/api/tickets/overdue` | 获取超时工单 |
| GET | `/api/tickets/refund` | 获取退款工单 |
| GET | `/api/tickets/complaint` | 获取投诉工单 |
| GET | `/api/tickets/search` | 搜索工单 |
| GET | `/api/tickets/{ticket_id}` | 获取工单详情 |
| POST | `/api/tickets` | 创建工单 |
| PUT | `/api/tickets/{ticket_id}/status` | 更新工单状态 |
| PUT | `/api/tickets/{ticket_id}/assign` | 分配工单 |
| PUT | `/api/tickets/{ticket_id}/resolve` | 解决工单 |
| PUT | `/api/tickets/{ticket_id}/close` | 关闭工单 |
| PUT | `/api/tickets/{ticket_id}/refund` | 更新退款信息 |
| PUT | `/api/tickets/{ticket_id}/priority` | 设置工单优先级 |
| POST | `/api/tickets/{ticket_id}/tags` | 添加工单标签 |
| DELETE | `/api/tickets/{ticket_id}/tags` | 移除工单标签 |
| GET | `/api/tickets/order/{order_id}` | 获取指定订单工单 |
| GET | `/api/tickets/platform/{platform}` | 获取指定平台工单 |
| GET | `/api/tickets/assignee/{assignee}` | 获取指定处理人工单 |

### 运营看板 `/api/dashboard`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/dashboard` | 获取运营看板数据 |
| GET | `/api/dashboard/stats` | Dashboard综合统计 |
| GET | `/api/dashboard/overview` | 获取概览数据 |
| GET | `/api/dashboard/trend` | 获取趋势数据 |
| GET | `/api/dashboard/platform/{platform}` | 获取指定平台数据 |
| GET | `/api/dashboard/trends` | 获取趋势数据（旧版） |
| GET | `/api/dashboard/alerts` | 获取告警信息 |

### 健康检查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 服务根路径 |
| GET | `/health` | 健康检查 |

## 启动服务

### 本地开发
```bash
cd ~/ecom-automation/services/oms-service
pip install -r requirements.txt
python main.py
```

服务将在 http://localhost:8005 启动

### Docker部署
```bash
cd ~/ecom-automation/services/oms-service
docker build -t oms-service .
docker run -p 8005:8005 oms-service
```

## 服务信息

- 端口: 8005
- 版本: 1.0.0
- 健康检查: `GET /health`
- API文档: `GET /docs` (Swagger UI)

## 目录结构

```
oms-service/
├── main.py                  # FastAPI主入口
├── pydantic_models.py       # Pydantic数据模型
├── order_manager.py         # 订单管理器
├── inventory_manager.py     # 库存管理器
├── ticket_manager.py        # 工单管理器
├── database.py              # 数据库配置
├── orm_models.py            # SQLAlchemy ORM模型
├── order_db_models.py       # 订单数据库模型
├── models/                  # 数据模型
│   ├── db_models.py         # 数据库模型定义
│   └── unified_models.py    # 统一模型
├── providers/               # 外部服务适配器
│   ├── base.py              # 基础适配器
│   └── mock_provider.py     # Mock适配器
├── repositories/            # 数据仓库
│   └── sku_repository.py    # SKU数据仓库
├── migrations/              # 数据库迁移
│   └── env.py               # Alembic环境配置
├── routes/                  # API路由
│   ├── order_routes.py      # 订单接口
│   ├── inventory_routes.py  # 库存接口
│   ├── ticket_routes.py     # 工单接口
│   └── dashboard_routes.py  # 看板接口
├── requirements.txt         # Python依赖
├── Dockerfile              # Docker配置
└── README.md               # 说明文档
```

## 数据模型

### 订单 (Order)
- 订单ID、平台来源、订单状态、支付状态
- 商品列表、金额信息
- 客户信息、物流信息
- 标签、风险等级

### 库存 (InventoryItem)
- SKU ID、商品名称、所属平台
- 总库存、可用库存、锁定库存、在途库存
- 预警设置、风险标签、风险等级

### 工单 (Ticket)
- 工单ID、关联订单、平台来源
- 工单类型、状态、优先级
- 问题描述、解决方案
- 退款信息（如适用）

## 示例数据

服务内置了示例数据，包括：
- 3个示例订单（抖音、快手、拼多多）
- 5个库存项目（各平台商品）
- 5个工单（退款、换货、投诉等类型）

启动后即可查看和操作这些示例数据。
